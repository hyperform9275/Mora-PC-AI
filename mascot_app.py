import sys
import os
import json
import random
import math
import ctypes
from PyQt6.QtCore import Qt, QPoint, QTimer, pyqtSignal, QObject
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QMenu, QGraphicsDropShadowEffect,
    QComboBox, QDialog, QCheckBox
)
from PyQt6.QtGui import QPixmap, QColor, QFont, QAction, QCursor, QTransform, QPainter

from core.voice_engine import VoiceEngine
from core.vision_engine import VisionEngine
from core.memory_manager import MemoryManager
from core.ai_brain import AIBrain

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
CHARACTERS_FILE = os.path.join(CONFIG_DIR, "characters.json")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")

class AIWorkerSignals(QObject):
    finished = pyqtSignal(str, bool)

class SettingsDialog(QDialog):
    """Cửa sổ cài đặt nâng cao cho Mora VTuber AI"""
    def __init__(self, settings, characters, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.characters = characters
        self.setWindowTitle("Cài Đặt Mora VTuber AI")
        self.resize(400, 460)
        self.setStyleSheet("""
            QDialog {
                background-color: #12131a;
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel {
                color: #e2e8f0;
                font-size: 13px;
                font-weight: 600;
            }
            QLineEdit, QComboBox {
                background-color: #1e202e;
                border: 1px solid #ff2b51;
                border-radius: 8px;
                padding: 6px 12px;
                color: #ffffff;
                font-size: 13px;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff2b51, stop:1 #9333ea);
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 10px 18px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #ff476e;
            }
            QCheckBox {
                color: #e2e8f0;
                font-size: 13px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Model Nhân vật VTuber:"))
        self.cb_char = QComboBox()
        for c in self.characters:
            self.cb_char.addItem(c["name"], c["id"])
        idx = next((i for i, c in enumerate(self.characters) if c["id"] == self.settings.get("active_character")), 0)
        self.cb_char.setCurrentIndex(idx)
        layout.addWidget(self.cb_char)

        layout.addWidget(QLabel("Nguồn suy luận AI (Provider):"))
        self.cb_provider = QComboBox()
        self.cb_provider.addItem("Ollama (Offline 100% trên máy)", "ollama")
        self.cb_provider.addItem("Google Gemini API (Online - Siêu nhanh)", "gemini")
        if self.settings.get("ai_provider") == "gemini":
            self.cb_provider.setCurrentIndex(1)
        layout.addWidget(self.cb_provider)

        layout.addWidget(QLabel("Tên Model Ollama Local:"))
        self.txt_ollama = QLineEdit(self.settings.get("ollama_model", "llama3.2:latest"))
        layout.addWidget(self.txt_ollama)

        layout.addWidget(QLabel("Google Gemini API Key:"))
        self.txt_gemini = QLineEdit(self.settings.get("gemini_api_key", ""))
        self.txt_gemini.setPlaceholderText("Dán API key từ Google AI Studio...")
        layout.addWidget(self.txt_gemini)

        self.chk_voice = QCheckBox("Bật giọng nói AI (Neural Text-to-Speech)")
        self.chk_voice.setChecked(self.settings.get("voice_enabled", True))
        layout.addWidget(self.chk_voice)

        self.chk_screen = QCheckBox("Cho phép quan sát màn hình (Vision Screen Mode)")
        self.chk_screen.setChecked(self.settings.get("watch_screen_enabled", True))
        layout.addWidget(self.chk_screen)

        self.chk_tab_react = QCheckBox("Tự động nhận diện khi đổi Tab/Game")
        self.chk_tab_react.setChecked(self.settings.get("react_to_tabs", True))
        layout.addWidget(self.chk_tab_react)

        btn_save = QPushButton("Lưu Cài Đặt")
        btn_save.clicked.connect(self.save_and_close)
        layout.addWidget(btn_save)

    def save_and_close(self):
        self.settings["active_character"] = self.cb_char.currentData()
        self.settings["ai_provider"] = self.cb_provider.currentData()
        self.settings["ollama_model"] = self.txt_ollama.text().strip()
        self.settings["gemini_api_key"] = self.txt_gemini.text().strip()
        self.settings["voice_enabled"] = self.chk_voice.isChecked()
        self.settings["watch_screen_enabled"] = self.chk_screen.isChecked()
        self.settings["react_to_tabs"] = self.chk_tab_react.isChecked()
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=2)
        self.accept()

class VTuberCanvas(QWidget):
    """
    Bộ Render Skeletal 2.5D độc lập:
    1. Lớp Thân (Body): Đứng đằm, xoay nhẹ theo trọng tâm.
    2. Lớp Đầu & Cổ (Head & Neck): Khớp xoay ở đáy cổ (Neck Pivot), tự do quay đầu/nghiêng đầu theo chuột.
    3. Lớp Bàn Tay (Hands): Cử động nhấp nhô, vẫy tay khi chào/nói chuyện.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(280, 340)

        # Layers
        self.pix_body = None
        self.pix_head = None
        self.pix_hands = None

        # Transforms
        self.head_tilt_x = 0.0
        self.head_tilt_y = 0.0
        self.head_tilt_z = 0.0
        self.body_tilt_y = 0.0
        self.breathing_offset = 0
        self.hand_offset_y = 0
        self.hand_angle = 0.0

    def update_layers(self, pix_body, pix_head, pix_hands,
                      head_tx, head_ty, head_tz, body_ty,
                      breathing_offset, hand_offset_y, hand_angle):
        self.pix_body = pix_body
        self.pix_head = pix_head
        self.pix_hands = pix_hands

        self.head_tilt_x = head_tx
        self.head_tilt_y = head_ty
        self.head_tilt_z = head_tz
        self.body_tilt_y = body_ty
        self.breathing_offset = breathing_offset
        self.hand_offset_y = hand_offset_y
        self.hand_angle = hand_angle
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        cx = self.width() / 2.0
        cy = (self.height() / 2.0) + self.breathing_offset

        # 1. Vẽ LỚP THÂN (Body Layer)
        if self.pix_body:
            t_body = QTransform()
            t_body.rotate(self.body_tilt_y, Qt.Axis.YAxis)
            trans_body = self.pix_body.transformed(t_body, Qt.TransformationMode.SmoothTransformation)
            bx = int(cx - (trans_body.width() / 2.0))
            by = int(cy - (trans_body.height() / 2.0))
            painter.drawPixmap(bx, by, trans_body)

        # 2. Vẽ LỚP TAY (Hands Layer) với chuyển động linh hoạt
        if self.pix_hands:
            t_hands = QTransform()
            t_hands.rotate(self.hand_angle, Qt.Axis.ZAxis)
            trans_hands = self.pix_hands.transformed(t_hands, Qt.TransformationMode.SmoothTransformation)
            hx = int(cx - (trans_hands.width() / 2.0))
            hy = int(cy - (trans_hands.height() / 2.0) + self.hand_offset_y)
            painter.drawPixmap(hx, hy, trans_hands)

        # 3. Vẽ LỚP ĐẦU & CỔ (Head & Neck Layer) với Khớp Xoay Độc Lập
        if self.pix_head:
            # Khớp cổ (Neck Pivot) nằm ở tọa độ đáy cổ (~135px)
            neck_y = cy - 25

            t_head = QTransform()
            # Xoay quanh trục cổ (Translate to neck pivot -> Rotate -> Translate back)
            t_head.translate(cx, neck_y)
            t_head.rotate(self.head_tilt_y, Qt.Axis.YAxis) # Quay mặt trái/phải
            t_head.rotate(self.head_tilt_x, Qt.Axis.XAxis) # Ngước/cúi đầu
            t_head.rotate(self.head_tilt_z, Qt.Axis.ZAxis) # Nghiêng đầu anime
            t_head.translate(-cx, -neck_y)

            trans_head = self.pix_head.transformed(t_head, Qt.TransformationMode.SmoothTransformation)
            hx = int(cx - (trans_head.width() / 2.0))
            hy = int(cy - (trans_head.height() / 2.0))
            painter.drawPixmap(hx, hy, trans_head)

class MoraVTuberWidget(QWidget):
    """
    Mora VTuber Desktop Companion:
    - Đầu & cổ chuyển động quay, gật, nghiêng độc lập với thân theo chuột.
    - Tay chuyển động nhấp nhô, cử động nhịp nhàng khi nói và tương tác.
    """
    def __init__(self):
        super().__init__()
        self.load_configs()

        self.voice_engine = VoiceEngine()
        self.vision_engine = VisionEngine()
        self.memory_manager = MemoryManager(os.path.join(CONFIG_DIR, "memory.json"))
        self.ai_brain = AIBrain(self.settings, self.memory_manager)

        self.signals = AIWorkerSignals()
        self.signals.finished.connect(self.on_ai_reply_received)

        self.drag_position = QPoint()
        self.is_thinking = False
        self.anim_step = 0.0

        # Trạng thái chuyển động khớp
        self.cur_head_y = 0.0
        self.cur_head_x = 0.0
        self.cur_head_z = 0.0
        self.cur_body_y = 0.0
        self.is_blinking = False
        self.mouth_state = False
        self.last_foreground_window = ""
        self.is_waving = False

        self.load_sprites()
        self.init_ui()
        self.init_animation_timers()
        self.show_welcome_greeting()

    def load_configs(self):
        with open(CHARACTERS_FILE, "r", encoding="utf-8") as f:
            self.characters = json.load(f)
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            self.settings = json.load(f)

        char_id = self.settings.get("active_character", "mora_redmagic")
        self.current_char = next((c for c in self.characters if c["id"] == char_id), self.characters[0])

    def load_sprites(self):
        """Nạp các lớp bộ phận (Layers) độc lập của Mora"""
        head_path = os.path.join(BASE_DIR, "assets/mora_layer_head.png")
        body_path = os.path.join(BASE_DIR, "assets/mora_layer_body.png")
        hands_path = os.path.join(BASE_DIR, "assets/mora_layer_hands.png")

        self.pix_body = QPixmap(body_path)
        self.pix_hands = QPixmap(hands_path)

        # Các trạng thái của Đầu
        self.pix_head_idle = QPixmap(head_path)
        talk_head = os.path.join(BASE_DIR, "assets/mora_layer_head_talk.png")
        self.pix_head_talk = QPixmap(talk_head) if os.path.exists(talk_head) else self.pix_head_idle
        blink_head = os.path.join(BASE_DIR, "assets/mora_layer_head_blink.png")
        self.pix_head_blink = QPixmap(blink_head) if os.path.exists(blink_head) else self.pix_head_idle

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(6)

        # 1. Bong bóng thoại Cyberpunk Kính mờ
        self.bubble_container = QWidget()
        self.bubble_container.setStyleSheet("""
            QWidget {
                background: rgba(18, 19, 26, 0.95);
                border: 2px solid #ff2b51;
                border-radius: 16px;
            }
        """)

        bubble_layout = QVBoxLayout(self.bubble_container)
        bubble_layout.setContentsMargins(14, 12, 14, 12)

        header_row = QHBoxLayout()
        self.lbl_char_title = QLabel(f"✨ {self.current_char['name']}")
        self.lbl_char_title.setStyleSheet("color: #ff4d6d; font-weight: bold; font-size: 13px; border: none; background: transparent;")
        header_row.addWidget(self.lbl_char_title)

        live_badge = QLabel("🔴 LIVE VTUBER")
        live_badge.setStyleSheet("color: #10b981; font-weight: bold; font-size: 10px; border: 1px solid #10b981; border-radius: 4px; padding: 1px 4px; background: rgba(16, 185, 129, 0.1);")
        header_row.addWidget(live_badge, alignment=Qt.AlignmentFlag.AlignRight)
        bubble_layout.addLayout(header_row)

        self.lbl_bubble_text = QLabel("Mora đang đồng hành cùng bạn...")
        self.lbl_bubble_text.setWordWrap(True)
        self.lbl_bubble_text.setStyleSheet("color: #f8fafc; font-size: 13px; line-height: 1.45; border: none; background: transparent;")
        bubble_layout.addWidget(self.lbl_bubble_text)

        input_row = QHBoxLayout()
        input_row.setSpacing(5)

        self.input_chat = QLineEdit()
        self.input_chat.setPlaceholderText("Hỏi Mora điều gì đó... (Enter)")
        self.input_chat.setStyleSheet("""
            QLineEdit {
                background: #0f1016;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #ffffff;
                padding: 5px 8px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #ff2b51;
            }
        """)
        self.input_chat.returnPressed.connect(self.on_send_chat)
        input_row.addWidget(self.input_chat)

        # Nút Gửi Chat
        self.btn_send = QPushButton("➤")
        self.btn_send.setToolTip("Gửi tin nhắn (Enter)")
        self.btn_send.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 5px 10px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #60a5fa;
            }
        """)
        self.btn_send.clicked.connect(self.on_send_chat)
        input_row.addWidget(self.btn_send)

        # Nút Soi màn hình
        self.btn_inspect = QPushButton("👁️ Soi")
        self.btn_inspect.setToolTip("Chụp và phân tích màn hình game/công việc hiện tại")
        self.btn_inspect.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff2b51, stop:1 #e11d48);
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 5px 10px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #ff4d6d;
            }
        """)
        self.btn_inspect.clicked.connect(self.on_inspect_screen)
        input_row.addWidget(self.btn_inspect)

        bubble_layout.addLayout(input_row)
        self.main_layout.addWidget(self.bubble_container)

        # 2. Canvas Vẽ Model VTuber Skeletal Rigged
        self.canvas = VTuberCanvas(self)
        self.canvas.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.canvas.setToolTip("Nhấp đúp chuột để tương tác! Đầu và tay Mora sẽ cử động linh hoạt theo bạn.")

        self.main_layout.addWidget(self.canvas, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setFixedWidth(320)
        screen_geo = QApplication.primaryScreen().geometry()
        x = screen_geo.width() - self.width() - 40
        y = screen_geo.height() - 560
        self.move(x, y)

    def init_animation_timers(self):
        self.render_timer = QTimer(self)
        self.render_timer.timeout.connect(self.update_vtuber_frame)
        self.render_timer.start(16) # 60 FPS

        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.trigger_blink)
        self.blink_timer.start(3500)

        self.lipsync_timer = QTimer(self)
        self.lipsync_timer.timeout.connect(self.update_lipsync)
        self.lipsync_timer.start(120)

        self.tab_timer = QTimer(self)
        self.tab_timer.timeout.connect(self.check_active_window)
        self.tab_timer.start(1500)

    def trigger_blink(self):
        self.is_blinking = True
        QTimer.singleShot(150, self.end_blink)
        self.blink_timer.setInterval(random.randint(2500, 5500))

    def end_blink(self):
        self.is_blinking = False

    def update_lipsync(self):
        if self.voice_engine.is_playing:
            self.mouth_state = not self.mouth_state
        else:
            self.mouth_state = False

    def check_active_window(self):
        if not self.settings.get("react_to_tabs", True) or self.is_thinking:
            return

        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            window_title = buff.value.strip()

            if window_title and window_title != self.last_foreground_window and "Mora" not in window_title:
                self.last_foreground_window = window_title
                lower_title = window_title.lower()
                if any(game in lower_title for game in ["league", "valorant", "genshin", "wukong", "steam", "dota"]):
                    self.trigger_waving(2000)
                    self.speak_and_display(f"Chiến game thôi! Mora thấy bạn vừa mở '{window_title[:24]}...'!")
                elif any(dev in lower_title for dev in ["visual studio", "code", "github", "terminal", "powershell"]):
                    self.speak_and_display("Chế độ lập trình! Cần Mora soi lỗi code thì bấm Soi nhé.")

    def trigger_waving(self, duration_ms=2500):
        self.is_waving = True
        QTimer.singleShot(duration_ms, self.stop_waving)

    def stop_waving(self):
        self.is_waving = False

    def update_vtuber_frame(self):
        cursor_pos = QCursor.pos()
        canvas_center = self.mapToGlobal(self.canvas.pos()) + QPoint(self.canvas.width() // 2, self.canvas.height() // 2)

        dx = cursor_pos.x() - canvas_center.x()
        dy = cursor_pos.y() - canvas_center.y()

        max_dist_x = QApplication.primaryScreen().geometry().width() / 2
        max_dist_y = QApplication.primaryScreen().geometry().height() / 2

        # 1. Khớp Cổ & Đầu (Head Tracking): Quay mặt mạnh mẽ theo chuột
        target_head_y = max(-16.0, min(16.0, (dx / max_dist_x) * 16.0))
        target_head_x = max(-9.0, min(9.0, -(dy / max_dist_y) * 9.0))
        target_head_z = max(-6.0, min(6.0, (dx / max_dist_x) * 6.0)) # Nghiêng đầu tự nhiên

        # 2. Thân (Body Tracking): Chỉ xoay nhẹ để tạo trọng tâm cơ thể
        target_body_y = max(-3.0, min(3.0, (dx / max_dist_x) * 3.0))

        # Khử giật LERP
        self.cur_head_y += (target_head_y - self.cur_head_y) * 0.12
        self.cur_head_x += (target_head_x - self.cur_head_x) * 0.12
        self.cur_head_z += (target_head_z - self.cur_head_z) * 0.12
        self.cur_body_y += (target_body_y - self.cur_body_y) * 0.08

        # 3. Nhịp thở (Breathing Motion)
        self.anim_step += 0.04
        breathing_offset = int(math.sin(self.anim_step) * 4)

        # 4. Chuyển động Bàn Tay (Hand Animation)
        if self.is_waving or self.voice_engine.is_playing:
            # Tay cử động nhấp nhô & lắc lư khi nói chuyện hoặc vẫy chào
            hand_offset_y = int(math.sin(self.anim_step * 3) * 6)
            hand_angle = math.sin(self.anim_step * 3) * 5.0
        else:
            hand_offset_y = int(math.sin(self.anim_step) * 2)
            hand_angle = 0.0

        # Chọn Sprite đầu phù hợp
        if self.is_blinking:
            active_head = self.pix_head_blink
        elif self.mouth_state:
            active_head = self.pix_head_talk
        else:
            active_head = self.pix_head_idle

        # Render các lớp lên canvas
        self.canvas.update_layers(
            self.pix_body, active_head, self.pix_hands,
            self.cur_head_x, self.cur_head_y, self.cur_head_z, self.cur_body_y,
            breathing_offset, hand_offset_y, hand_angle
        )

    def show_welcome_greeting(self):
        greetings = self.current_char.get("greetings", ["Mora đã online cùng bạn đây!"])
        text = random.choice(greetings)
        self.trigger_waving(2000)
        self.speak_and_display(text)

    def speak_and_display(self, text: str):
        self.lbl_bubble_text.setText(text)
        if self.settings.get("voice_enabled", True):
            voice = self.current_char.get("voice", "vi-VN-HoaiMyNeural")
            rate = self.current_char.get("voice_speed", "+5%")
            self.voice_engine.speak(text, voice=voice, rate=rate)

    def on_send_chat(self):
        text = self.input_chat.text().strip()
        if not text or self.is_thinking:
            return
        self.input_chat.clear()
        self.set_thinking_state(True)
        self.lbl_bubble_text.setText("Mora đang suy nghĩ...")

        import threading
        def worker():
            reply = self.ai_brain.generate_reply(text, self.current_char, image_base64=None)
            self.signals.finished.emit(reply, True)

        threading.Thread(target=worker, daemon=True).start()

    def on_inspect_screen(self):
        if self.is_thinking:
            return
        if not self.settings.get("watch_screen_enabled", True):
            self.speak_and_display("Chế độ xem màn hình đang tắt trong Cài Đặt!")
            return

        self.set_thinking_state(True)
        self.lbl_bubble_text.setText("Mora đang soi màn hình của bạn...")

        import threading
        def worker():
            img_b64 = self.vision_engine.capture_screen_base64()
            prompt = self.current_char.get("game_prompt", "Nhận xét màn hình này.")
            reply = self.ai_brain.generate_reply(prompt, self.current_char, image_base64=img_b64)
            self.signals.finished.emit(reply, True)

        threading.Thread(target=worker, daemon=True).start()

    def on_ai_reply_received(self, text: str, is_voice: bool):
        self.set_thinking_state(False)
        self.trigger_waving(2500)
        self.speak_and_display(text)

    def set_thinking_state(self, thinking: bool):
        self.is_thinking = thinking
        self.btn_inspect.setEnabled(not thinking)
        self.btn_send.setEnabled(not thinking)
        self.input_chat.setEnabled(not thinking)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.trigger_waving(2500)
            self.show_welcome_greeting()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #12131a;
                color: #ffffff;
                border: 1px solid #ff2b51;
                border-radius: 10px;
                padding: 6px;
                font-size: 13px;
            }
            QMenu::item {
                padding: 8px 22px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background-color: #ff2b51;
                color: #ffffff;
            }
        """)

        act_inspect = QAction("👁️ Soi Màn Hình Nhanh", self)
        act_inspect.triggered.connect(self.on_inspect_screen)
        menu.addAction(act_inspect)

        char_menu = menu.addMenu("🎭 Đổi Model Nhân Vật")
        for char in self.characters:
            act = QAction(char["name"], self)
            act.triggered.connect(lambda ch, c=char: self.switch_character(c))
            char_menu.addAction(act)

        menu.addSeparator()

        act_settings = QAction("⚙️ Cài Đặt (AI & Voice)", self)
        act_settings.triggered.connect(self.open_settings)
        menu.addAction(act_settings)

        act_toggle_voice = QAction("🔇 Tắt/Bật Giọng Nói", self)
        act_toggle_voice.triggered.connect(self.toggle_voice)
        menu.addAction(act_toggle_voice)

        menu.addSeparator()

        act_quit = QAction("❌ Thoát VTuber Mora", self)
        act_quit.triggered.connect(QApplication.instance().quit)
        menu.addAction(act_quit)

        menu.exec(event.globalPos())

    def switch_character(self, character):
        self.current_char = character
        self.settings["active_character"] = character["id"]
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=2)
        self.load_sprites()
        self.show_welcome_greeting()

    def toggle_voice(self):
        current = self.settings.get("voice_enabled", True)
        self.settings["voice_enabled"] = not current
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=2)
        status = "Bật" if not current else "Tắt"
        self.lbl_bubble_text.setText(f"Đã {status} giọng nói!")

    def open_settings(self):
        dlg = SettingsDialog(self.settings, self.characters, self)
        if dlg.exec():
            self.load_configs()
            self.load_sprites()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MoraVTuberWidget()
    widget.show()
    sys.exit(app.exec())
