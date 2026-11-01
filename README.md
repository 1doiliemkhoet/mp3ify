# mp3ify v1.0.1 — Công cụ chuyển MP4 sang MP3 trên Windows CMD

**Offline, không tải video lên mạng.** Một công cụ CLI cá nhân như `yt-dlp`, nhưng dành cho file MP4 đã có trên máy. Sử dụng Python 3 (thư viện chuẩn) và FFmpeg.

**Cập nhật v1.0.1:** Sửa lỗi tên file chứa dấu `[` `]` và ký tự Unicode. Nếu đã cài v1.0, giải nén ZIP mới rồi chạy lại `install.cmd` để cập nhật.

## 1. Cài 2 thành phần cần thiết

Mở CMD hoặc PowerShell:

```bat
python --version
ffmpeg -version
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
| `-o`, `--output` | File MP3 đầu ra (chỉ dùng khi chuyển 1 file) |
| `-d`, `--out-dir` | Thư mục chứa MP3 |
| `-r`, `--recursive` | Quét cả thư mục con |
| `-q`, `--quality` | Chất lượng MP3 VBR từ 0 đến 9; mặc định `2` (cao) |
| `-b`, `--bitrate` | Bitrate cố định, ví dụ `192`, `320` (kbps) |
| `--track N` | Audio track thứ N (tính từ 0) |
| `-y`, `--overwrite` | Ghi đè MP3 đã tồn tại |
| `--dry-run` | Chỉ hiển thị kế hoạch, không tạo file |

## 4. Lưu ý

- Không tự ý xóa hoặc sửa file MP4 gốc.
- Mặc định **bỏ qua** MP3 đã tồn tại; dùng `-y` để thay thế.
- Có bảo vệ file đầu ra: FFmpeg mã hóa sang file MP3 tạm, chỉ đổi tên khi chuyển đổi thành công.
- Mặc định lấy track audio đầu tiên; nếu video không có audio, CLI báo lỗi.
- Không thể nâng chất lượng audio nguồn thấp bằng cách xuất 320 kbps.
- Không bao gồm ffmpeg.exe trong ZIP. Nếu muốn dùng bản portable, có thể đặt `ffmpeg.exe` cùng thư mục `mp3ify.py` (với bản cài: `%LOCALAPPDATA%\Programs\mp3ify`).
- Khi nhiều file trùng tên được đẩy vào cùng thư mục `-d`, CLI sẽ bỏ qua file đầu ra đã có (trừ khi `-y`).

## 5. Gỡ cài đặt

Xóa thư mục `%LOCALAPPDATA%\Programs\mp3ify`, sau đó xóa mục đường dẫn đó khỏi `Path` trong **Environment Variables > User variables**.

## 6. Tự build .exe (nếu muốn)

Có thể chạy **`build-exe.cmd`** trên Windows (yêu cầu Python và Internet để tải PyInstaller), hoặc dùng các lệnh:

```bat
python -m pip install pyinstaller
python -m PyInstaller --onefile --console --name mp3ify mp3ify.py
```

File `dist\mp3ify.exe` sẽ chạy mà không cần cài Python. Vẫn cần FFmpeg trong PATH hoặc đặt `ffmpeg.exe` cạnh `mp3ify.exe`.

## 7. Đưa source lên GitHub

Gói `mp3ify-github-ready-v1.0.1.zip` có sẵn `.gitignore`, workflow chạy unit tests trên GitHub Actions và script `publish-github.cmd` để tự tạo repository bằng GitHub CLI.

1. Cài Git và GitHub CLI trên Windows nếu chưa có:
   ```cmd
   winget install -e --id Git.Git
   winget install -e --id GitHub.cli
   ```
2. Đóng CMD, mở CMD mới và đăng nhập (bằng trình duyệt, không gửi token cho ai):
   ```cmd
   gh auth login
   ```
3. Giải nén gói, mở CMD tại thư mục có `publish-github.cmd`, chạy:
   ```cmd
   publish-github.cmd
   ```

Script sẽ kiểm tra tài khoản **`1doiliemkhoet`**, tạo repo **`1doiliemkhoet/mp3ify`** dạng **private** và push branch `main`. Nếu muốn công khai nguồn:

```cmd
publish-github.cmd Public
```

Nếu repo đã tồn tại, script dừng để tránh ghi đè nội dung. Link repository sau khi tạo thành công: `https://github.com/1doiliemkhoet/mp3ify`.