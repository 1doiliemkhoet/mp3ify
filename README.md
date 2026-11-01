# mp3ify v1.1.0 — MP4 → MP3 hoặc trích xuất audio gốc

**Offline, không tải video lên mạng.** Một công cụ CLI cá nhân như `yt-dlp`, nhưng dành cho file MP4 đã có trên máy. Sử dụng Python 3 (thư viện chuẩn) và FFmpeg.

**Mới trong v1.1.0:** `--best` trích xuất nguyên luồng âm thanh gốc (`-c:a copy`), không chuyển mã, tự chọn đuôi file theo codec: AAC/ALAC → `.m4a`, MP3 → `.mp3`, Opus → `.opus`, Vorbis → `.ogg`, FLAC → `.flac`; codec ít gặp → `.mka`. Tùy chọn này **không nâng chất lượng file nguồn** và **không nhất thiết xuất ra MP3**. Bản v1.0.1 trước đó đã sửa tên file Unicode và `[...]`.

**Đã cài bản cũ?** Clone/pull source mới rồi chạy `install.cmd` thêm lần nữa để cập nhật bản đã cài.

## 1. Cài 2 thành phần cần thiết

Mở CMD hoặc PowerShell:

```bat
python --version
ffmpeg -version
ffprobe -version
```

Nếu chưa có Python, có thể cài với:

```bat
winget install -e --id Python.Python.3.13
```

Nếu chưa có FFmpeg:

```bat
winget install -e --id Gyan.FFmpeg
```

Sau khi cài các thành phần này, **đóng và mở CMD mới** để PATH được cập nhật.

FFmpeg: https://www.gyan.dev/ffmpeg/builds/

## 2. Cài `mp3ify` vào lệnh CMD

Giải nén ZIP, chạy **`install.cmd`**. Lệnh này sao chép `mp3ify.py` + `mp3ify.cmd` vào `%LOCALAPPDATA%\Programs\mp3ify` và thêm thư mục đó vào **User PATH**. Không cần chạy Administrator.

Sau đó đóng CMD, mở CMD mới:

```bat
mp3ify --version
mp3ify --help
```

**Hoặc** không cài PATH, mở CMD tại thư mục đã giải nén và chạy `mp3ify.cmd "video.mp4"`.

## 3. Ví dụ lệnh

```bat
:: Chuyển 1 file, MP3 nằm cạnh video
mp3ify "D:\Videos\demo.mp4"

:: Tên file đầu ra tùy chọn
mp3ify "D:\Videos\demo.mp4" -o "D:\Music\bai-hat.mp3"

:: Chuyển tất cả MP4 trong thư mục hiện tại (CMD hỗ trợ wildcard qua mp3ify)
mp3ify *.mp4

:: Chuyển cả thư mục, bao gồm thư mục con
mp3ify "D:\Videos" -r

:: Chuyển cả thư mục, xuất ra thư mục khác, giữ cây thư mục con
mp3ify "D:\Videos" -r -d "D:\MP3"

:: Trích xuất nguyên audio không mã hóa lại (AAC -> M4A, MP3 -> MP3...)
mp3ify "demo.mp4" --best

:: Chuyển 1 thư mục, giữ nguyên codec audio từng video
mp3ify "D:\Videos" -r --best -d "D:\Audio"

:: MP3 chất lượng cao cố định 320 kbps
mp3ify "demo.mp4" -b 320

:: Chọn track audio thứ hai (đánh số từ 0)
mp3ify "demo.mp4" --track 1

:: Ghi đè nếu đã có MP3
mp3ify "demo.mp4" -y

:: Xem trước mà không chuyển
mp3ify "D:\Videos" -r --dry-run
```

### Một số tùy chọn

| Tùy chọn | Ý nghĩa |
|---|---|
| `-h`, `--help` | Hướng dẫn |
| `-o`, `--output` | Tên file đầu ra (với `--best`, phải đúng đuôi theo codec nguồn) |
| `-d`, `--out-dir` | Thư mục chứa file âm thanh đầu ra |
| `-r`, `--recursive` | Quét cả thư mục con |
| `-q`, `--quality` | Chất lượng MP3 VBR từ 0 đến 9; mặc định `2` (cao) |
| `-b`, `--bitrate` | Bitrate MP3 cố định, ví dụ `192`, `320` (kbps) |
| `--best` | Giữ nguyên bitstream âm thanh; tự chọn định dạng đầu ra, cần `ffprobe` |
| `--track N` | Audio track thứ N (tính từ 0) |
| `-y`, `--overwrite` | Ghi đè file đầu ra đã tồn tại |
| `--dry-run` | Chỉ hiển thị kế hoạch, không tạo file |

## 4. Lưu ý

- Không tự ý xóa hoặc sửa file MP4 gốc.
- Mặc định **bỏ qua** file đầu ra đã tồn tại; dùng `-y` để thay thế.
- Có bảo vệ file đầu ra: FFmpeg ghi sang file tạm cùng định dạng, chỉ đổi tên khi chuyển đổi thành công.
- Mặc định lấy track audio đầu tiên; nếu video không có audio, CLI báo lỗi.
- Không thể nâng chất lượng audio nguồn thấp bằng cách xuất 320 kbps. `--best` giữ nguyên dữ liệu nén đã có, không tạo âm thanh lossless nếu nguồn là AAC/MP3.
- `--best` không dùng chung với `-q` hay `-b`: đây là chế độ **copy**, không mã hóa MP3. File đầu ra có thể là `.m4a`, `.opus`, `.mka`..., cần trình phát hỗ trợ.
- `--best` dùng `ffprobe` (đi kèm FFmpeg) để phát hiện codec; `--track N` dùng để chọn luồng cần trích xuất. Với codec chưa biết, output `.mka` để ưu tiên bảo toàn stream.
- `--best -o "song.mp3"` sẽ báo lỗi nếu codec nguồn là AAC (phải đặt tên `.m4a`); không bao giờ đổi đuôi giả thành MP3.
- Không bao gồm FFmpeg/ffprobe trong ZIP. Nếu muốn dùng bản portable, đặt `ffmpeg.exe` **và** `ffprobe.exe` cùng thư mục `mp3ify.py` (hoặc bên cạnh file `.exe` nếu đã build).
- Khi nhiều file trùng tên được đẩy vào cùng thư mục `-d`, CLI sẽ bỏ qua file đầu ra đã có (trừ khi `-y`).

## 5. Gỡ cài đặt

Xóa thư mục `%LOCALAPPDATA%\Programs\mp3ify`, sau đó xóa mục đường dẫn đó khỏi `Path` trong **Environment Variables > User variables**.

## 6. Tự build .exe (nếu muốn)

Có thể chạy **`build-exe.cmd`** trên Windows (yêu cầu Python và Internet để tải PyInstaller), hoặc dùng các lệnh:

```bat
python -m pip install pyinstaller
python -m PyInstaller --onefile --console --name mp3ify mp3ify.py
```

File `dist\mp3ify.exe` chạy mà không cần cài Python. Vẫn cần FFmpeg/ffprobe trong PATH hoặc đặt cả hai `.exe` bên cạnh `mp3ify.exe`.

## 7. Cập nhật bản cài từ GitHub

```cmd
git -C C:\mp3ify\mp3ify pull --ff-only
cd /d C:\mp3ify\mp3ify
install.cmd
```

Mở CMD mới, kiểm tra `mp3ify --version` (kết quả `1.1.0`).

Source repository: https://github.com/1doiliemkhoet/mp3ify
