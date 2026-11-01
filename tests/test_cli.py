"""Small self-contained tests: python -m unittest discover -s tests -v"""
import importlib.util
import contextlib
import io
import json
import shutil
import subprocess
from unittest import mock
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("mp3ify", Path(__file__).resolve().parents[1] / "mp3ify.py")
mp3ify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mp3ify)


class CLITests(unittest.TestCase):
    def test_bitrate(self):
        self.assertEqual(mp3ify.parse_bitrate("320k"), 320)
        self.assertEqual(mp3ify.parse_bitrate("192"), 192)

    def test_collect_recursive_and_dedupe(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "sub").mkdir()
            (root / "first.mp4").touch()
            (root / "sub" / "second.MP4").touch()
            files, errors = mp3ify.collect_files([str(root), str(root / "first.mp4")], recursive=False)
            self.assertFalse(errors)
            self.assertEqual(len(files), 1)
            files, errors = mp3ify.collect_files([str(root), str(root / "first.mp4")], recursive=True)
            self.assertFalse(errors)
            self.assertEqual(len(files), 2)
            self.assertIn("sub/second.MP4", [r.as_posix() for _, r in files])

    def test_literal_unicode_filename_with_square_brackets(self):
        # Regression: glob has_magic() must not treat [190153...] as a pattern.
        name = "15K views · 97 reactions ｜ Trundle + Nốt Trầm Bùng Nổ ｜ Hoàng Minh Ngọc [1901532534222730].mp4"
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / name
            path.touch()
            files, errors = mp3ify.collect_files([str(path)], recursive=False)
            self.assertFalse(errors)
            self.assertEqual(files, [(path, Path(name))])

    def test_glob_wildcard_still_expands(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            (directory / "one.mp4").touch()
            (directory / "two.mp4").touch()
            (directory / "other.txt").touch()
            files, errors = mp3ify.collect_files([str(directory / "*.mp4")], recursive=False)
            self.assertFalse(errors)
            self.assertEqual({p.name for p, _ in files}, {"one.mp4", "two.mp4"})

    def test_nonexistent_bracket_filename_reports_error(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "missing [12345].mp4"
            files, errors = mp3ify.collect_files([str(path)], recursive=False)
            self.assertFalse(files)
            self.assertTrue(errors)

    def test_bad_output_extension_rejected(self):
        with self.assertRaises(SystemExit) as exc:
            mp3ify.main(["video.mp4", "-o", "not-mp3.wav"])
        self.assertEqual(exc.exception.code, 2)

    def test_best_extensions(self):
        self.assertEqual(mp3ify.best_extension("aac"), ".m4a")
        self.assertEqual(mp3ify.best_extension("alac"), ".m4a")
        self.assertEqual(mp3ify.best_extension("mp3"), ".mp3")
        self.assertEqual(mp3ify.best_extension("opus"), ".opus")
        self.assertEqual(mp3ify.best_extension("vorbis"), ".ogg")
        self.assertEqual(mp3ify.best_extension("flac"), ".flac")
        self.assertEqual(mp3ify.best_extension("pcm_s16le"), ".mka")
        self.assertEqual(mp3ify.best_extension("unknowncodec"), ".mka")

    def test_best_rejects_lossy_options(self):
        for arg in ("-b", "-q"):
            with self.subTest(arg=arg), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as exc:
                    mp3ify.main(["video.mp4", "--best", arg, "320" if arg == "-b" else "0"])
                self.assertEqual(exc.exception.code, 2)

    def test_probe_codec_selects_correct_track(self):
        fake = mock.Mock(returncode=0, stdout=json.dumps({"streams": [
            {"codec_name": "aac"}, {"codec_name": "opus"}]}), stderr="")
        with mock.patch.object(mp3ify.subprocess, "run", return_value=fake) as runner:
            self.assertEqual(mp3ify.probe_codec("ffprobe", Path("some.mp4"), 1), ("opus", None))
            self.assertIsNone(mp3ify.probe_codec("ffprobe", Path("some.mp4"), 2)[0])
            self.assertIn("-select_streams", runner.call_args.args[0])

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg + ffprobe required")
    def test_best_aac_copy_real_audio_and_unicode_name(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "Trundle ｜ Nốt Trầm [1901532534222730].mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                            "sine=frequency=440:duration=0.25", "-c:a", "aac", str(source)],
                           check=True, capture_output=True)
            output = source.with_suffix(".m4a")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(mp3ify.main([str(source), "--best"]), 0)
            self.assertTrue(output.exists())
            self.assertFalse(source.with_suffix(".mp3").exists())
            self.assertEqual(mp3ify.probe_codec("ffprobe", output, 0), ("aac", None))
            # Packet-level content must be identical, not just same reported bitrate.
            def hashes(path):
                r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0",
                                    "-show_packets", "-show_data_hash", "sha256",
                                    "-show_entries", "packet=data_hash", "-of", "json", str(path)],
                                   check=True, capture_output=True, text=True)
                return [p["data_hash"] for p in json.loads(r.stdout)["packets"]]
            self.assertEqual(hashes(source), hashes(output))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(mp3ify.main([str(source), "--best"]), 0)  # skip existing
                self.assertEqual(mp3ify.main([str(source), "--best", "-y"]), 0)
            self.assertEqual(hashes(source), hashes(output))

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg + ffprobe required")
    def test_best_dry_run_and_output_extension_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "demo.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                            "sine=duration=0.1", "-c:a", "aac", str(source)],
                           check=True, capture_output=True)
            with contextlib.redirect_stdout(io.StringIO()) as result:
                self.assertEqual(mp3ify.main([str(source), "--best", "--dry-run"]), 0)
            self.assertIn("demo.m4a", result.getvalue())
            self.assertFalse(source.with_suffix(".m4a").exists())
            with contextlib.redirect_stdout(io.StringIO()) as result:
                self.assertEqual(mp3ify.main([str(source), "--best", "-o", str(Path(temp) / "wrong.mp3")]), 1)
            self.assertIn("must end in .m4a", result.getvalue())
            self.assertFalse((Path(temp) / "wrong.mp3").exists())


if __name__ == "__main__":
    unittest.main()
