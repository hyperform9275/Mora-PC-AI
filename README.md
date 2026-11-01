# Mora PC AI Desktop Mascot 🎮✨

Interactive 3D Desktop AI Assistant & Waifu Companion inspired by Mora (RedMagic) & Skirk, featuring real-time 3D rendering, cloth physics, vision understanding, and AI personality.

---

## 🌟 Tính Năng Chính (Features)

- **3D Real-time Desktop Mascot**: Mô hình 3D tương tác trực tiếp trên màn hình máy tính với Three.js trong suốt (transparent window).
- **Hệ Thống Vật Lý Đa Khớp Xương (Advanced Bone Physics)**:
  - Tà váy & đuôi cá (Fishtail Fins) chuyển động mềm mại theo gió desktop.
  - Cánh pha lê sau lưng (Crystal Wings) trôi bồng bềnh thanh thoát.
  - Tóc nhiều tầng (Multi-Joint Hair Wave Spring) phản hồi theo chuyển động đầu và chuột.
  - Vật lý dao động ngực (Bust Jiggle & Drag Momentum) tự nhiên khi kéo rê cửa sổ.
- **AI Brain (Gemini / LLMs)**: Trò chuyện tương tác với tính cách waifu ngọt ngào, xưng hô "Chủ nhân - em", ghi nhớ thông tin người dùng qua SQLite.
- **Vision Engine**: Khả năng "nhìn" màn hình của Chủ nhân và đưa ra lời bình luận, hỗ trợ theo thời gian thực.
- **Voice Engine & Voice Bank**: Hệ thống lồng tiếng phong phú với ngân hàng âm thanh phản ứng khi tương tác chạm vào các vị trí trên cơ thể.

---

## 🚀 Hướng Dẫn Cài Đặt & Khởi Chạy (Quick Start)

### 1. Yêu Cầu Hệ Thống
- Python 3.10+ (Đã thử nghiệm trên Python 3.12/3.14 Windows 11).
- Trình duyệt hỗ trợ WebGL.

### 2. Cài Đặt Thư Viện Cần Thiết
```bash
pip install -r requirements.txt
```
*(Hoặc cài đặt các gói chính: `google-genai`, `Pillow`, `pygame`, `psutil`, `pywebview`...)*

### 3. Cấu Hình Khóa API
Sao chép file mẫu:
```bash
copy config\settings.example.json config\settings.json
```
Mở `config/settings.json` và điền `gemini_api_key` của bạn.

### 4. Khởi Chạy Mascot 3D
Nhấp đúp chuột vào file:
```bash
start_3d_mora.bat
```
hoặc chạy bằng lệnh:
```bash
python run_3d_mora.py
```

---

## 📁 Cấu Trúc Thư Mục (Project Structure)

```
Mora-PC-AI/
├── assets/                  # 3D models, textures, voice bank & dataset
│   ├── textures/            # Bộ texture tùy biến (Red Ruby, Default...)
│   ├── voice_bank/          # File âm thanh lời chào & phản ứng
│   └── mora_3d.glb          # Mô hình 3D glTF/GLB chính
├── config/                  # Cấu hình tính cách, cài đặt và cơ sở dữ liệu
├── core/                    # Bộ não AI, xử lý thị giác, giọng nói và bộ nhớ
├── ui_3d/                   # Giao diện WebGL 3D Three.js & Engine vật lý
├── run_3d_mora.py           # Launcher chính cho 3D Desktop Mascot
└── start_3d_mora.bat        # Batch script khởi chạy nhanh 1-click
```

---

## 💖 Tác Giả & Bản Quyền
- Dự án được phát triển bởi **Anh Hào** (`hyperform9275`).
- Giữ bản quyền mã nguồn và thiết lập tính cách trợ lý ảo Mora.
