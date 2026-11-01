# 🎓 CẨM NANG PHỎNG VẤN & BẢN QUYỀN DỰ ÁN: MORA PC AI
> **Dành riêng cho bạn:** Đọc kỹ tài liệu này trước buổi phỏng vấn. Nó giúp bạn tự tin giải thích từng dòng code, bảo vệ kiến trúc hệ thống và chứng minh bạn chính là tác giả/kiến trúc sư trưởng của dự án.

---

## 📌 PHẦN 1: GIỚI THIỆU TỔNG QUAN DỰ ÁN (PITCHING 60 GIÂY)

Khi nhà tuyển dụng nói: *"Hãy giới thiệu một dự án cá nhân ấn tượng mà bạn từng làm"*, hãy trả lời như sau:

> *"Em đã thiết kế và phát triển **Mora PC AI** - một trợ lý ảo dạng Desktop Companion/Gaming Mascot không viền cửa sổ, lấy cảm hứng từ AI Mora trên dòng gaming phone Red Magic.  
> Không giống như ChatGPT hay các chatbot thông thường bị 'giam' trong một tab trình duyệt, Mora là một thực thể nổi trực tiếp trên màn hình desktop, luôn hiển thị trên cùng (Always-on-top) ngay cả khi người dùng đang chơi game hay làm việc.  
> Điểm cốt lõi của dự án là khả năng **Nhận thức màn hình (Screen Awareness)** qua Vision LLM để hỗ trợ tức thì những gì người dùng đang thao tác, kết hợp **Giọng nói thông minh (Neural TTS)** và **Hệ thống cá nhân hóa nhân vật/giọng nói** hoàn chỉnh."*

---

## 🏛️ PHẦN 2: KIẾN TRÚC HỆ THỐNG (SYSTEM ARCHITECTURE)

Dự án hỗ trợ 2 chế độ hiển thị linh hoạt (Dual Engine Display):
1. **Chế độ 2.5D Layered Skeletal Rigging (`mascot_app.py`)**: Nhẹ tối đa (~40MB RAM), bóc tách khớp xương cổ & tay 2D bằng PyQt6.
2. **Chế độ 3D VTuber Engine (`run_3d_mora.py`)**: Render mô hình 3D thực thụ từ Blender (`.glb`) qua WebGL / Three.js, xoay xương cổ 360 độ và cử động mắt/tay thật 100%.

```
┌────────────────────────────────────────────────────────┐
│   TẦNG 1: HIỂN THỊ 3D / 2.5D DESKTOP OVERLAY           │
│   Three.js WebGL (3D Bones) ⟷ PyQt6 Layered Canvas     │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────┴─────────────────────────────┐
│   TẦNG 2: XỬ LÝ ĐA PHƯƠNG THỨC (MULTIMODAL ENGINES)     │
│   ├── Vision Engine: mss (Chụp màn hình ~2ms in-memory)│
│   └── Voice Engine: Edge-TTS + WinMM Windows Audio     │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────┴─────────────────────────────┐
│   TẦNG 3: BỘ NÃO SUY LUẬN (AI INFERENCE BRAIN)         │
│   Adapter Pattern: Ollama (Offline) ⟷ Gemini (Vision)   │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────┴─────────────────────────────┐
│   TẦNG 4: BỘ NHỚ & NGỮ CẢNH (MEMORY & CONTEXT ENGINE)  │
│   Long-term Memory Bank • Context Prompt Injection     │
└────────────────────────────────────────────────────────┘
```

---

## 🎯 PHẦN 3: CÁC CÂU HỎI PHỎNG VẤN HÓC BÚA & CÁCH TRẢ LỜI ĂN ĐIỂM

### Câu hỏi 1: "Làm sao bạn tạo được một pop-up không viền, nền trong suốt và nổi trên mọi game mà không gây drop FPS?"
* **Bản chất kỹ thuật:** Dùng các cờ hệ thống của hệ điều hành Windows thông qua `PyQt6` kết hợp kỹ thuật **Layered Skeletal Rigging (Khớp xương 2.5D đa tầng)**.
* **Câu trả lời chuẩn:**
  > *"Em sử dụng 3 cờ quan trọng của PyQt6: `FramelessWindowHint`, `WindowStaysOnTopHint`, và `WA_TranslucentBackground` để dựng cửa sổ trong suốt luôn nổi trên desktop và game.  
  > Để nhân vật cử động chân thực như một model VTuber/Live2D thực thụ thay vì một tấm ảnh cứng đờ, em áp dụng kiến trúc **Layered Skeletal Rigging**:  
  > 1. Bóc tách mô hình thành 3 tầng độc lập: **Thân (Body)**, **Đầu & Cổ (Head & Neck)**, và **Bàn tay (Hands)**.  
  > 2. Đặt trục xoay (Neck Pivot) tại gốc khớp cổ: Khi chuột di chuyển, đầu và cổ tự do quay trái/phải, ngước lên/cúi xuống và nghiêng góc Z $\pm 16^\circ$ độc lập hoàn toàn với cơ thể.  
  > 3. Lớp bàn tay và miệng tự động cử động nhịp nhàng (Lip-sync & Hand Gestures) đồng bộ với âm thanh giọng nói và sự kiện chuyển tab/game.  
  > Toàn bộ quá trình vẽ diễn ra trực tiếp qua `QPainter` phần cứng trong một canvas cố định, khử hoàn toàn lỗi tràn dirty rect của Windows Layered Window và giữ mức tiêu thụ CPU dưới 1%."*

---

### Câu hỏi 2: "Cơ chế chụp và đọc màn hình (Screen Awareness) của bạn hoạt động thế nào để không làm lag máy?"
* **Bản chất kỹ thuật:** Chụp bằng `mss`, nén trong RAM, không ghi I/O ổ đĩa cứng.
* **Câu trả lời chuẩn:**
  > *"Thay vì dùng các thư viện thông thường ghi file ảnh xuống ổ cứng gây nghẽn I/O (Disk Bottleneck), em sử dụng thư viện `mss` truy xuất trực tiếp buffer đồ họa của hệ điều hành, chụp toàn bộ màn hình chỉ trong 2-3 mili-giây.  
  > Sau đó ảnh được nén dạng Base64 JPEG trực tiếp trong RAM (In-Memory Buffer bằng `io.BytesIO`) và đẩy qua luồng nền (Worker Thread) đến Vision AI (Gemini 1.5 Flash hoặc Llama-Vision). Người dùng chơi game hoàn toàn không cảm nhận được độ trễ."*

---

### Câu hỏi 3: "Bạn xử lý concurrency (đa luồng) thế nào để khi AI đang suy nghĩ hoặc đang nói, chuột và giao diện không bị đơ?"
* **Bản chất kỹ thuật:** Threading + PyQt Signals & Slots (Thread-safe communication).
* **Câu trả lời chuẩn:**
  > *"Giao diện GUI của hệ điều hành chạy trên Main Thread. Nếu thực hiện các tác vụ tốn thời gian như gọi mạng API AI hay sinh giọng nói TTS trên Main Thread, giao diện sẽ bị treo (Not Responding).  
  > Em đã tách riêng các tác vụ nặng vào `daemon threading.Thread`. Khi AI có kết quả, dữ liệu được gửi về Main Thread thông qua cơ chế `pyqtSignal` an toàn về mặt luồng (Thread-safe) để cập nhật bong bóng thoại và cất tiếng nói."*

---

### Câu hỏi 4: "Tại sao bạn lại hỗ trợ cả Ollama lẫn Gemini thay vì chỉ chọn 1 nguồn?"
* **Bản chất kỹ thuật:** Tránh Vendor Lock-in, mô hình Hybrid (Offline Security + Cloud Scalability).
* **Câu trả lời chuẩn:**
  > *"Đây là quyết định thiết kế theo mẫu Adapter Pattern:  
  > - **Ollama (Llama 3.2 / DeepSeek)**: Dành cho chế độ Offline 100%, bảo mật tuyệt đối khi người dùng không có mạng hoặc làm việc với tài liệu mật trên máy.  
  > - **Google Gemini API**: Tận dụng khả năng xử lý hình ảnh đa phương thức (Multimodal Vision) cực mạnh với tốc độ dưới 1 giây và Context Window khổng lồ. Người dùng có thể chuyển đổi dễ dàng chỉ với 1 click trong menu Cài Đặt."*

---

## 🎨 PHẦN 4: HƯỚNG DẪN TÙY BIẾN NHÂN VẬT & NGUỒN GIỌNG NÓI

Dự án được thiết kế mở 100% để bạn có thể thêm bất kỳ nhân vật hay giọng nói nào:

### 1. Thêm nhân vật mới:
Mở file `D:\Mora-PC-AI\config\characters.json` và thêm object nhân vật:
```json
{
  "id": "nhan_vat_cua_ban",
  "name": "Tên Nhân Vật",
  "avatar": "assets/anh_nhan_vat.png",
  "voice": "vi-VN-HoaiMyNeural",
  "voice_speed": "+5%",
  "personality": "Mô tả tính cách, xưng hô, giọng điệu...",
  "greetings": ["Câu chào 1", "Câu chào 2"],
  "game_prompt": "Câu chỉ thị khi soi màn hình..."
}
```

### 2. Các nguồn giọng nói (Voice Engine):
Hệ thống sử dụng Microsoft Neural Voice. Bạn có thể đổi mã giọng trong `voice`:
- **Nữ tiếng Việt dễ thương (Mora)**: `vi-VN-HoaiMyNeural`
- **Nam tiếng Việt chuẩn (Cyber)**: `vi-VN-NamMinhNeural`
- **Nữ tiếng Nhật phong cách Anime**: `ja-JP-NanamiNeural`
- **Nữ tiếng Anh hiện đại**: `en-US-AvaNeural`
- **Mở rộng tương lai (Voice Cloning)**: Có thể tích hợp API của **ElevenLabs** hoặc **GPT-SoVITS** vào file `core/voice_engine.py` chỉ với một hàm POST request!

---

## 🚀 PHẦN 5: BẬT VÀ TRẢI NGHIỆM

Chỉ cần nhấp đúp vào file:
👉 **`D:\Mora-PC-AI\start_mora.bat`**
- Nhân vật Mora sẽ xuất hiện lơ lửng ở góc phải màn hình.
- Chuột trái: Kéo rê đi khắp nơi.
- Chuột phải: Menu đổi nhân vật, soi màn hình, cài đặt API.
- Bấm **👁️ Soi**: Mora chụp và nhận xét ngay màn hình bạn đang mở!
