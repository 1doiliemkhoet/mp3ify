"""Small self-contained tests: python -m unittest discover -s tests -v"""
import importlib.util
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


if __name__ == "__main__":
    unittest.main()
