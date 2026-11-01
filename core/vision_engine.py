import io
import base64
import mss
from PIL import Image

class VisionEngine:
    """
    Module thị giác máy tính & chụp màn hình thời gian thực.
    Sử dụng mss (DirectX/GDI level) chụp màn hình cực nhanh (~2ms).
    Nén ảnh trực tiếp trong RAM (In-Memory Buffer), không ghi đĩa cứng để tối ưu FPS khi chơi game.
    """
    def __init__(self):
        self.sct = mss.mss()

    def capture_screen_base64(self, max_dimension=1024, quality=75) -> str:
        """
        Chụp màn hình chính và trả về chuỗi Base64 JPEG để gửi cho Vision LLM.
        Tự động nén kích thước để tiết kiệm token và giảm độ trễ mạng.
        """
        # Chụp màn hình số 1 (Màn hình chính)
        monitor = self.sct.monitors[1]
        screenshot = self.sct.grab(monitor)

        # Chuyển đổi dữ liệu thô sang ảnh PIL
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

        # Thu nhỏ ảnh nếu kích thước quá lớn để gửi API nhanh hơn
        if max(img.size) > max_dimension:
            img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

        # Nén vào bộ nhớ đệm (RAM)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)

        # Mã hóa Base64
        base64_str = base64.b64encode(buffer.read()).decode("utf-8")
        return base64_str

    def save_debug_screenshot(self, filepath="debug_screen.jpg"):
        """Lưu ảnh chụp phục vụ kiểm tra/debug"""
        monitor = self.sct.monitors[1]
        screenshot = self.sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        img.save(filepath, format="JPEG", quality=85)
        return filepath
