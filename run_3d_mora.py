import os

import sys

import ctypes

from ctypes import wintypes



# Kích hoạt phần cứng đồ họa rời NVIDIA GPU & Tăng tốc phần cứng Chromium WebEngine

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (

    "--enable-gpu-rasterization "

    "--enable-zero-copy "

    "--ignore-gpu-blocklist "

    "--enable-webgl "

    "--enable-accelerated-2d-canvas"

)

os.environ["QT_LOGGING_RULES"] = "qt.qpa.*=false"

sys.stdout.reconfigure(encoding='utf-8')



# Windows API constants for transparent click-through

user32 = ctypes.windll.user32

GWL_EXSTYLE = -20

WS_EX_TRANSPARENT = 0x00000020

VK_LBUTTON = 0x01



import json

import threading

import http.server

import socketserver



from PyQt6.QtWidgets import (

    QApplication, QMainWindow, QMenu, QSystemTrayIcon,

    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,

    QPushButton, QFrame, QScrollArea, QDialog, QComboBox, QMessageBox, QCheckBox

)

from PyQt6.QtWebEngineWidgets import QWebEngineView

from PyQt6.QtWebChannel import QWebChannel

from PyQt6.QtCore import Qt, QUrl, QPoint, QObject, pyqtSlot, pyqtSignal, QTimer, QCoreApplication

from PyQt6.QtGui import QColor, QIcon, QAction, QCursor



from core.voice_engine import VoiceEngine

from core.vision_engine import VisionEngine

from core.memory_manager import MemoryManager

from core.ai_brain import AIBrain

from core.reaction_manager import ReactionManager

from core.app_controller import AppController



BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_DIR = os.path.join(BASE_DIR, "config")

UI_3D_DIR = os.path.join(BASE_DIR, "ui_3d")

CHARACTERS_FILE = os.path.join(CONFIG_DIR, "characters.json")

SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")



PORT = 18989



class QuietHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, directory=UI_3D_DIR, **kwargs)



    def end_headers(self):

        # Chặn Chromium cache model 3D và HTML, luôn tải phiên bản mới nhất

        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")

        self.send_header("Pragma", "no-cache")

        self.send_header("Expires", "0")

        super().end_headers()



    def log_message(self, format, *args):

        pass



def start_local_server():

    socketserver.TCPServer.allow_reuse_address = True

    try:

        httpd = socketserver.TCPServer(("127.0.0.1", PORT), QuietHandler)

        httpd.serve_forever()

    except Exception as e:

        print(f"[HTTP Server] Info: {e}")



class WebBridge(QObject):

    """Cầu nối giữa HTML/JavaScript và Backend Python"""

    def __init__(self, settings, character, brain, voice_engine, vision_engine):

        super().__init__()

        self._settings = settings

        self._character = character

        self._brain = brain

        self._voice_engine = voice_engine

        self._vision_engine = vision_engine

        self._reaction_manager = ReactionManager()

        self._app_controller = AppController()

        self._window = None



    def set_window(self, win):

        self._window = win



    @pyqtSlot()

    def show_context_menu(self):

        """Kích hoạt menu chuột phải từ sự kiện JavaScript contextmenu"""

        if self._window:

            self._window.show_mora_context_menu(None)



    @pyqtSlot()

    def start_drag(self):

        """Kích hoạt kéo thả cửa sổ chuẩn Windows Native System Move"""

        if self._window and self._window.windowHandle():

            self._window.windowHandle().startSystemMove()



    @pyqtSlot(float)

    def adjust_scale(self, delta: float):

        """Điều chỉnh phóng to / thu nhỏ model qua con lăn chuột Ctrl + Wheel"""

        if self._window:

            cur = getattr(self._window, 'current_scale', 1.0)

            self._window.set_model_scale(cur + delta)



    @pyqtSlot(str)

    def trigger_hitbox_reaction(self, part: str):

        """Phản xạ xúc giác thông minh dựa trên ngữ cảnh tâm trạng và chủ đề cuộc trò chuyện"""

        try:

            history = []

            if hasattr(self._brain, 'memory_manager') and hasattr(self._brain.memory_manager, 'get_chat_history'):

                history = self._brain.memory_manager.get_chat_history()



            current_draft = ""

            if self._window and hasattr(self._window, 'chat_window') and hasattr(self._window.chat_window, 'input_field'):

                current_draft = self._window.chat_window.input_field.text().strip()



            context = self._reaction_manager.detect_context(history, current_draft=current_draft)

            reaction_text = self._reaction_manager.get_reaction(part, history, current_draft=current_draft)

            action_desc = self._reaction_manager.get_action_description(part, context)



            # Ghi nhớ tương tác này vào luồng hội thoại để câu chat kế tiếp hiểu được trọn vẹn ngữ cảnh!

            if hasattr(self._brain, 'memory_manager') and hasattr(self._brain.memory_manager, 'record_hitbox_interaction'):

                self._brain.memory_manager.record_hitbox_interaction(part, action_desc, reaction_text)



            self.speak_hitbox(reaction_text, part=part)

        except Exception as e:

            print(f"[Hitbox Error] {e}")



    @pyqtSlot(str)

    def speak_hitbox(self, text: str, part: str = "general"):

        """Phát âm thanh phản ứng khi tương tác chạm vào các bộ phận trên cơ thể Mora (Hybrid Voice)"""

        try:

            if self._window and hasattr(self._window, 'speech_popup'):

                self._window.speech_popup.show_message(text)



            if self._window and hasattr(self._window, 'chat_window'):

                self._window.chat_window.set_mora_text(text)



            if self._settings.get("voice_enabled", True):

                voice = self._character.get("voice", "vi-VN-HoaiMyNeural")

                rate = self._character.get("voice_speed", "+5%")

                # Hybrid Voice Engine: Ưu tiên phát từ Voice Bank cục bộ (0ms), fallback sang TTS

                self._voice_engine.play_hitbox_voice(part, fallback_text=text, voice=voice, rate=rate)

        except Exception as e:

            print(f"[Speak Hitbox Error] {e}")



    @pyqtSlot(str, result=str)

    def send_chat(self, text: str) -> str:

        # 1. Kiểm tra lệnh trao quyền mở / tắt ứng dụng, game hoặc tab web trên máy

        is_cmd, cmd_reply = self._app_controller.handle_command(text)

        if is_cmd:

            if hasattr(self._brain, 'memory_manager'):

                self._brain.memory_manager.add_chat_turn("user", text)

                self._brain.memory_manager.add_chat_turn("model", cmd_reply)

            if self._settings.get("voice_enabled", True):

                voice = self._character.get("voice", "vi-VN-HoaiMyNeural")

                rate = self._character.get("voice_speed", "+5%")

                self._voice_engine.speak(cmd_reply, voice=voice, rate=rate)

            return cmd_reply



        # 2. Xử lý hội thoại AI thông thường

        reply = self._brain.generate_reply(text, self._character, image_base64=None)

        if self._settings.get("voice_enabled", True):

            voice = self._character.get("voice", "vi-VN-HoaiMyNeural")

            rate = self._character.get("voice_speed", "+5%")

            self._voice_engine.speak(reply, voice=voice, rate=rate)

        return reply



    @pyqtSlot(result=str)

    def inspect_screen(self) -> str:

        if not self._settings.get("watch_screen_enabled", True):

            return "Chế độ xem màn hình đang tắt trong Cài Đặt!"



        img_b64 = self._vision_engine.capture_screen_base64()

        prompt = self._character.get("game_prompt", "Nhận xét màn hình này.")

        reply = self._brain.generate_reply(prompt, self._character, image_base64=img_b64)

        if self._settings.get("voice_enabled", True):

            voice = self._character.get("voice", "vi-VN-HoaiMyNeural")

            rate = self._character.get("voice_speed", "+5%")

            self._voice_engine.speak(reply, voice=voice, rate=rate)

        return reply



    @pyqtSlot(bool)

    def set_bubble_visible(self, visible: bool):

        self._settings["show_chat_bubble"] = visible

        try:

            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:

                json.dump(self._settings, f, indent=2, ensure_ascii=False)

        except Exception:

            pass

        if self._window:

            self._window.update_tray_menu()



    @pyqtSlot(result=bool)

    def get_bubble_visible(self) -> bool:

        return self._settings.get("show_chat_bubble", False)



class MoraChatWindow(QWidget):

    """Cửa sổ trò chuyện rời, luôn nằm bên cạnh Mora và không bao giờ đè lên người Mora"""

    reply_received = pyqtSignal(str)



    def __init__(self, parent_mora, bridge):

        super().__init__()

        self.mora = parent_mora

        self.bridge = bridge

        self.drag_position = None

        self.reply_received.connect(self.on_reply_received)

        self.init_ui()



    def init_ui(self):

        self.setWindowFlags(

            Qt.WindowType.FramelessWindowHint |

            Qt.WindowType.WindowStaysOnTopHint |

            Qt.WindowType.Tool

        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.setFixedSize(380, 165)



        layout = QVBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)



        # Khung viền RedMagic Cyberpunk

        self.container = QFrame(self)

        self.container.setObjectName("chatContainer")

        self.container.setStyleSheet("""

            #chatContainer {

                background-color: rgba(18, 19, 26, 245);

                border: 2px solid #ff2b51;

                border-radius: 16px;

            }

            .title-lbl {

                color: #ff4d6d;

                font-weight: 700;

                font-size: 13px;

                letter-spacing: 0.5px;

            }

            .live-badge {

                color: #10b981;

                font-weight: 700;

                font-size: 10px;

                border: 1px solid #10b981;

                border-radius: 4px;

                padding: 1px 6px;

                background-color: rgba(16, 185, 129, 38);

            }

            .close-btn {

                background: transparent;

                border: none;

                color: #ff85a1;

                font-size: 15px;

                font-weight: bold;

                padding: 0 4px;

            }

            .close-btn:hover {

                color: #ffffff;

            }

            .text-lbl {

                color: #f8fafc;

                font-size: 13px;

                line-height: 1.4;

                font-family: 'Segoe UI', system-ui, sans-serif;

            }

            QLineEdit {

                background: #0f1016;

                border: 1px solid #334155;

                border-radius: 8px;

                color: #ffffff;

                padding: 6px 10px;

                font-size: 12px;

            }

            QLineEdit:focus {

                border: 1px solid #ff2b51;

            }

            .send-btn {

                background-color: #3b82f6;

                color: white;

                border-radius: 8px;

                padding: 6px 12px;

                font-size: 12px;

                font-weight: bold;

                border: none;

            }

            .send-btn:hover {

                background-color: #60a5fa;

            }

            .inspect-btn {

                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ff2b51, stop:1 #e11d48);

                color: white;

                border-radius: 8px;

                padding: 6px 10px;

                font-size: 11px;

                font-weight: bold;

                border: none;

            }

            .inspect-btn:hover {

                background-color: #ff4d6d;

            }

        """)



        frame_layout = QVBoxLayout(self.container)

        frame_layout.setContentsMargins(14, 12, 14, 12)

        frame_layout.setSpacing(8)



        # 1. Hàng tiêu đề Header

        header_layout = QHBoxLayout()

        header_layout.setContentsMargins(0, 0, 0, 0)



        title = QLabel("✨ Mora 3D VTuber (RedMagic)")

        title.setProperty("class", "title-lbl")



        badge = QLabel("🔴 3D LIVE")

        badge.setProperty("class", "live-badge")



        self.sound_btn = QPushButton("🔊")

        self.sound_btn.setProperty("class", "close-btn")

        self.sound_btn.setToolTip("Bật / Tắt âm thanh giọng nói (Click để chuyển đổi)")

        self.sound_btn.clicked.connect(self.mora.toggle_voice)

        self.update_sound_btn_icon()



        close_btn = QPushButton("✕")

        close_btn.setProperty("class", "close-btn")

        close_btn.setToolTip("Đóng khung chat (Mở lại: Chuột phải vào Mora)")

        close_btn.clicked.connect(self.hide_chat)



        header_layout.addWidget(title)

        header_layout.addStretch()

        header_layout.addWidget(badge)

        header_layout.addWidget(self.sound_btn)

        header_layout.addWidget(close_btn)



        # 2. Vùng cuộn hiển thị câu thoại / phụ đề (Hỗ trợ lăn chuột cuộn đọc văn bản dài)

        self.scroll_area = QScrollArea(self.container)

        self.scroll_area.setWidgetResizable(True)

        self.scroll_area.setFixedHeight(68)

        self.scroll_area.setStyleSheet("""

            QScrollArea {

                background: transparent;

                border: none;

            }

            QScrollBar:vertical {

                border: none;

                background: rgba(15, 16, 22, 120);

                width: 6px;

                border-radius: 3px;

                margin: 0px;

            }

            QScrollBar::handle:vertical {

                background: #ff2b51;

                min-height: 18px;

                border-radius: 3px;

            }

            QScrollBar::handle:vertical:hover {

                background: #ff6b8b;

            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {

                height: 0px;

            }

        """)



        self.text_lbl = QLabel("Mora đã sẵn sàng theo dõi từng thao tác chuột của bạn!")

        self.text_lbl.setProperty("class", "text-lbl")

        self.text_lbl.setWordWrap(True)

        self.text_lbl.setStyleSheet("""

            color: #f8fafc;

            font-size: 13px;

            line-height: 1.45;

            font-family: 'Segoe UI', system-ui, sans-serif;

            background: transparent;

            border: none;

        """)

        self.text_lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.scroll_area.setWidget(self.text_lbl)



        # 3. Hàng nhập tin nhắn & nút bấm

        input_layout = QHBoxLayout()

        input_layout.setContentsMargins(0, 0, 0, 0)

        input_layout.setSpacing(6)



        self.input_field = QLineEdit()

        self.input_field.setPlaceholderText("Hỏi Mora điều gì đó... (Enter)")

        self.input_field.returnPressed.connect(self.on_send_chat)



        self.send_btn = QPushButton("➤")

        self.send_btn.setProperty("class", "send-btn")

        self.send_btn.setToolTip("Gửi câu hỏi")

        self.send_btn.clicked.connect(self.on_send_chat)



        self.inspect_btn = QPushButton("👁️ Soi")

        self.inspect_btn.setProperty("class", "inspect-btn")

        self.inspect_btn.setToolTip("Nhìn & nhận xét màn hình")

        self.inspect_btn.clicked.connect(self.on_inspect_screen)



        input_layout.addWidget(self.input_field)

        input_layout.addWidget(self.send_btn)

        input_layout.addWidget(self.inspect_btn)



        frame_layout.addLayout(header_layout)

        frame_layout.addWidget(self.scroll_area)

        frame_layout.addLayout(input_layout)



        layout.addWidget(self.container)



    def wheelEvent(self, event):

        """Cho phép lăn con chuột bất kỳ đâu trên khung chat để cuộn đọc văn bản dài"""

        delta = event.angleDelta().y()

        bar = self.scroll_area.verticalScrollBar()

        bar.setValue(bar.value() - delta // 2)

        event.accept()



    def mousePressEvent(self, event):

        if event.button() == Qt.MouseButton.LeftButton:

            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

            event.accept()



    def mouseMoveEvent(self, event):

        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position is not None:

            self.move(event.globalPosition().toPoint() - self.drag_position)

            event.accept()



    def mouseReleaseEvent(self, event):

        self.drag_position = None



    def update_position(self):

        """Tự động canh vị trí sang cạnh bên của Mora, tuyệt đối không đè lên Mora"""

        screen = QApplication.primaryScreen().geometry()

        # Mặc định nằm bên TRÁI Mora

        target_x = self.mora.x() - self.width() - 15

        target_y = self.mora.y() + 140



        # Nếu bên trái màn hình không đủ chỗ (Mora đứng sát góc trái), lật sang bên PHẢI Mora

        if target_x < 10:

            target_x = self.mora.x() + self.mora.width() + 15



        self.move(target_x, target_y)



    def set_mora_text(self, text: str):

        self.text_lbl.setText(text)

        self.scroll_area.verticalScrollBar().setValue(0)



    def on_send_chat(self):

        text = self.input_field.text().strip()

        if not text:

            return

        self.input_field.clear()

        self.text_lbl.setText("Mora 3D đang suy nghĩ...")

        self.mora.webview.page().runJavaScript("if (window.startSpeaking) window.startSpeaking();")



        def task():

            try:

                reply = self.bridge.send_chat(text)

                self.reply_received.emit(reply)

            except Exception as e:

                self.reply_received.emit(f"[Lỗi]: {e}")



        threading.Thread(target=task, daemon=True).start()



    def on_inspect_screen(self):

        self.text_lbl.setText("Mora 3D đang soi màn hình...")

        self.mora.webview.page().runJavaScript("if (window.startSpeaking) window.startSpeaking();")



        def task():

            try:

                reply = self.bridge.inspect_screen()

                self.reply_received.emit(reply)

            except Exception as e:

                self.reply_received.emit(f"[Lỗi]: {e}")



        threading.Thread(target=task, daemon=True).start()



    def on_reply_received(self, reply: str):

        self.text_lbl.setText(reply)

        self.scroll_area.verticalScrollBar().setValue(0)

        self.mora.webview.page().runJavaScript("setTimeout(() => { if (window.stopSpeaking) window.stopSpeaking(); }, 3500);")



    def set_mora_text(self, text: str):

        self.text_lbl.setText(text)

        self.scroll_area.verticalScrollBar().setValue(0)



    def update_sound_btn_icon(self):

        if hasattr(self, 'sound_btn'):

            v_on = self.bridge._settings.get("voice_enabled", True)

            self.sound_btn.setText("🔊" if v_on else "🔇")

            self.sound_btn.setToolTip("Giọng nói đang BẬT (Click để Tắt)" if v_on else "Giọng nói đang TẮT (Click để Bật)")



    def hide_chat(self):

        self.hide()

        self.bridge.set_bubble_visible(False)

        self.mora.update_tray_menu()



class MoraSpeechPopup(QWidget):

    """Bong bóng thoại mini nổi hoàn toàn bên ngoài cửa sổ Mora, tuyệt đối không bao giờ đè lên model"""

    def __init__(self, parent_mora):

        super().__init__()

        self.mora = parent_mora

        self.fade_timer = QTimer(self)

        self.fade_timer.setSingleShot(True)

        self.fade_timer.timeout.connect(self.hide)

        self.init_ui()



    def init_ui(self):

        self.setWindowFlags(

            Qt.WindowType.FramelessWindowHint |

            Qt.WindowType.WindowStaysOnTopHint |

            Qt.WindowType.Tool

        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)



        layout = QVBoxLayout(self)

        layout.setContentsMargins(6, 6, 6, 6)



        self.frame = QFrame(self)

        self.frame.setStyleSheet("""

            QFrame {

                background-color: rgba(18, 19, 26, 245);

                border: 2px solid #ff2b51;

                border-radius: 14px;

            }

        """)



        frame_layout = QVBoxLayout(self.frame)

        frame_layout.setContentsMargins(12, 10, 12, 10)



        self.label = QLabel(self.frame)

        self.label.setStyleSheet("""

            color: #ffffff;

            font-family: 'Segoe UI', system-ui, sans-serif;

            font-size: 13px;

            font-weight: 500;

            line-height: 1.45;

            background: transparent;

            border: none;

        """)

        self.label.setWordWrap(True)

        frame_layout.addWidget(self.label)



        layout.addWidget(self.frame)



    def show_message(self, text: str, timeout_ms: int = 5000):

        self.label.setText(text)

        self.label.adjustSize()

        # Chiều rộng vừa vặn câu chữ (tối đa 300px cho câu chào dài)

        self.setFixedWidth(min(300, max(190, len(text) * 7 + 40)))

        self.adjustSize()

        self.update_position()

        self.show()

        self.fade_timer.start(timeout_ms)



    def update_position(self):

        screen = QApplication.primaryScreen().geometry()

        # Nằm hoàn toàn bên ngoài, cách mép TRÁI cửa sổ Mora 12px

        target_x = self.mora.x() - self.width() - 12

        target_y = self.mora.y() + 80 # Ngang tầm đầu / vai



        # Nếu sát mép trái màn hình không đủ chỗ, đảo sang mép PHẢI cửa sổ Mora

        if target_x < 10:

            target_x = self.mora.x() + self.mora.width() + 12



        self.move(target_x, target_y)





class MoraSettingsDialog(QDialog):

    """Hộp thoại cài đặt API Key & AI Provider (Gemini / Grok / OpenAI / Ollama)"""

    def __init__(self, settings: dict, parent=None):

        super().__init__(parent)

        self.settings = settings

        self.setWindowTitle("⚙️ Cài Đặt Trí Tuệ Nhân Tạo Mora (AI Brain Settings)")

        self.setFixedSize(480, 520)

        self.setStyleSheet("""

            QDialog {

                background-color: #12131a;

                color: #f3f4f6;

                font-family: 'Segoe UI', Arial, sans-serif;

            }

            QLabel {

                color: #e5e7eb;

                font-size: 12px;

                font-weight: 600;

            }

            .sub-label {

                color: #9ca3af;

                font-size: 11px;

                font-weight: normal;

                margin-bottom: 4px;

            }

            QLineEdit, QComboBox {

                background-color: #1e202e;

                border: 1px solid #374151;

                border-radius: 8px;

                padding: 6px 10px;

                color: #ffffff;

                font-size: 12px;

            }

            QLineEdit:focus, QComboBox:focus {

                border: 1px solid #ff2b51;

            }

            QPushButton {

                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff2b51, stop:1 #ff6b8b);

                color: #ffffff;

                font-weight: 700;

                font-size: 13px;

                border: none;

                border-radius: 8px;

                padding: 9px 18px;

            }

            QPushButton:hover {

                background: #ff476f;

            }

            .btn-secondary {

                background: #26293b;

                color: #d1d5db;

                border: 1px solid #374151;

            }

            .btn-secondary:hover {

                background: #32364e;

                color: #ffffff;

            }

            .status-box {

                background-color: rgba(16, 185, 129, 20);

                border: 1px solid #10b981;

                border-radius: 8px;

                padding: 8px;

                color: #10b981;

                font-size: 11px;

            }

        """)

        self.init_ui()



    def init_ui(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(24, 20, 24, 20)

        layout.setSpacing(12)



        title = QLabel("🤖 Cấu Hình Trí Não AI Mora")

        title.setStyleSheet("font-size: 16px; font-weight: 800; color: #ff3b60; margin-bottom: 4px;")

        layout.addWidget(title)



        status = QLabel("🌐 Mặc định Online: Gemini / Grok / GPT | 🔌 Mất mạng: Tự động dùng Ollama")

        status.setProperty("class", "status-box")

        layout.addWidget(status)



        # 1. AI Provider chính

        lbl_p = QLabel("Nhà Cung Cấp AI Ưu Tiên (Khi Có Kết Nối Wifi/Internet):")

        layout.addWidget(lbl_p)

        self.cb_provider = QComboBox()

        self.cb_provider.addItems(["Google Gemini (Mặc định - Siêu tốc & Thông minh)", "xAI Grok (Grok 2 / Grok Beta)", "OpenAI ChatGPT (GPT-4o)"])

        prov = self.settings.get("ai_provider", "gemini").lower()

        if prov == "grok":

            self.cb_provider.setCurrentIndex(1)

        elif prov == "openai":

            self.cb_provider.setCurrentIndex(2)

        else:

            self.cb_provider.setCurrentIndex(0)

        layout.addWidget(self.cb_provider)



        # 2. Gemini API Key

        lbl_g = QLabel("1. Google Gemini API Key (Miễn Phí tại aistudio.google.com):")

        layout.addWidget(lbl_g)

        self.txt_gemini = QLineEdit()

        self.txt_gemini.setPlaceholderText("Dán mã AIzaSy... vào đây")

        self.txt_gemini.setEchoMode(QLineEdit.EchoMode.Password)

        self.txt_gemini.setText(self.settings.get("gemini_api_key", ""))

        layout.addWidget(self.txt_gemini)



        # 3. Grok API Key

        lbl_grk = QLabel("2. xAI Grok API Key (console.x.ai):")

        layout.addWidget(lbl_grk)

        self.txt_grok = QLineEdit()

        self.txt_grok.setPlaceholderText("Dán mã xai-... vào đây (nếu có)")

        self.txt_grok.setEchoMode(QLineEdit.EchoMode.Password)

        self.txt_grok.setText(self.settings.get("grok_api_key", ""))

        layout.addWidget(self.txt_grok)



        # 4. OpenAI API Key

        lbl_oai = QLabel("3. OpenAI API Key (platform.openai.com):")

        layout.addWidget(lbl_oai)

        self.txt_openai = QLineEdit()

        self.txt_openai.setPlaceholderText("Dán mã sk-... vào đây (nếu có)")

        self.txt_openai.setEchoMode(QLineEdit.EchoMode.Password)

        self.txt_openai.setText(self.settings.get("openai_api_key", ""))

        layout.addWidget(self.txt_openai)



        # 5. Offline Ollama Model

        lbl_ollama = QLabel("4. Mô Hình Offline Cục Bộ (Ollama):")

        layout.addWidget(lbl_ollama)

        self.txt_ollama = QLineEdit()

        self.txt_ollama.setText(self.settings.get("ollama_model", "llama3.2:latest"))

        layout.addWidget(self.txt_ollama)



        # 5. Tùy chọn Âm thanh & Giọng nói Mora

        self.chk_voice = QCheckBox("🔊 Bật Âm Thanh & Giọng Nói Mora (Hybrid Voice Pack + AI TTS)")

        self.chk_voice.setChecked(self.settings.get("voice_enabled", True))

        self.chk_voice.setStyleSheet("color: #ff6b8b; font-weight: 700; font-size: 12px; margin-top: 8px;")

        layout.addWidget(self.chk_voice)



        layout.addSpacing(10)



        # Button row

        btn_layout = QHBoxLayout()

        self.btn_save = QPushButton("💾 Lưu Cài Đặt")

        self.btn_save.clicked.connect(self.save_settings)

        btn_layout.addWidget(self.btn_save)



        self.btn_open_file = QPushButton("📄 Mở File JSON")

        self.btn_open_file.setProperty("class", "btn-secondary")

        self.btn_open_file.clicked.connect(self.open_json_file)

        btn_layout.addWidget(self.btn_open_file)



        self.btn_close = QPushButton("Đóng")

        self.btn_close.setProperty("class", "btn-secondary")

        self.btn_close.clicked.connect(self.close)

        btn_layout.addWidget(self.btn_close)



        layout.addLayout(btn_layout)



    def save_settings(self):

        idx = self.cb_provider.currentIndex()

        if idx == 1:

            self.settings["ai_provider"] = "grok"

        elif idx == 2:

            self.settings["ai_provider"] = "openai"

        else:

            self.settings["ai_provider"] = "gemini"



        self.settings["gemini_api_key"] = self.txt_gemini.text().strip()

        self.settings["grok_api_key"] = self.txt_grok.text().strip()

        self.settings["openai_api_key"] = self.txt_openai.text().strip()

        self.settings["ollama_model"] = self.txt_ollama.text().strip() or "llama3.2:latest"

        self.settings["voice_enabled"] = self.chk_voice.isChecked()

        if hasattr(self.parent(), 'chat_window') and hasattr(self.parent().chat_window, 'update_sound_btn_icon'):

            self.parent().chat_window.update_sound_btn_icon()

        if hasattr(self.parent(), 'update_tray_menu'):

            self.parent().update_tray_menu()

        if not self.chk_voice.isChecked() and hasattr(self.parent(), 'bridge') and hasattr(self.parent().bridge, '_voice_engine'):

            self.parent().bridge._voice_engine.stop_current_audio()



        try:

            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:

                json.dump(self.settings, f, indent=2, ensure_ascii=False)

            QMessageBox.information(self, "Thành Công", "Đã lưu cài đặt AI Brain thành công! Mora sẽ áp dụng ngay lập tức.")

            self.accept()

        except Exception as e:

            QMessageBox.critical(self, "Lỗi", f"Không thể lưu tệp settings.json: {e}")



    def open_json_file(self):

        import subprocess

        try:

            os.startfile(SETTINGS_FILE)

        except Exception:

            subprocess.Popen(["notepad.exe", SETTINGS_FILE])



class Mora3DWindow(QMainWindow):

    def __init__(self, bridge):

        super().__init__()

        self.bridge = bridge

        self.bridge.set_window(self)

        self.is_click_through = False

        self.current_scale = float(self.bridge._settings.get("model_scale", 1.0))

        self.current_scale = max(0.60, min(1.80, self.current_scale))



        self.init_window_flags()

        self.init_chat_window()

        self.init_web_engine()

        self.init_global_mouse_tracker()

        self.init_desktop_roamer()

        self.init_tray()



        # Đặt lịch hẹn pop-up chào mừng hồi tưởng trí nhớ hội thoại lần trước sau khi khởi động (~2.5s)

        QTimer.singleShot(2500, self.trigger_startup_memory_greeting)



    def trigger_startup_memory_greeting(self):

        """Pop up câu thoại chào mừng khởi động hồi tưởng chi tiết cuộc trò chuyện lần trước"""

        try:

            if hasattr(self.bridge, '_brain') and hasattr(self.bridge._brain, 'memory_manager'):

                greeting = self.bridge._brain.memory_manager.generate_startup_greeting(self.bridge._character)

            else:

                greeting = "Mora đã sẵn sàng đồng hành cùng Chủ nhân rồi đây nha!"



            # 1. Pop-up bong bóng thoại nổi bên cạnh Mora (hiển thị 8.5 giây)

            if hasattr(self, 'speech_popup'):

                self.speech_popup.show_message(greeting, timeout_ms=8500)



            # 2. Cập nhật vào cửa sổ chat nếu đang mở

            if hasattr(self, 'chat_window'):

                self.chat_window.set_mora_text(greeting)



            # 3. Phát giọng nói nếu bật voice

            if self.bridge._settings.get("voice_enabled", False):

                voice = self.bridge._character.get("voice", "vi-VN-HoaiMyNeural")

                rate = self.bridge._character.get("voice_speed", "+5%")

                # Hybrid Voice: Phát âm thanh chào hỏi từ Voice Bank nếu có

                self.bridge._voice_engine.play_greeting_voice([greeting], voice=voice, rate=rate)



            # 4. Hiệu ứng nhép môi lip-sync trong 4.5s

            self.webview.page().runJavaScript("if (window.startSpeaking) window.startSpeaking(); setTimeout(() => { if (window.stopSpeaking) window.stopSpeaking(); }, 4500);")

        except Exception as e:

            print(f"[Startup Greeting Error] {e}")



    def init_chat_window(self):

        self.chat_window = MoraChatWindow(self, self.bridge)

        self.speech_popup = MoraSpeechPopup(self)

        is_shown = self.bridge._settings.get("show_chat_bubble", False)

        if is_shown:

            self.chat_window.update_position()

            self.chat_window.show()

        else:

            self.chat_window.hide()



    def init_window_flags(self):

        # Thiết lập trong suốt tuyệt đối và luôn nổi trên mọi ứng dụng/tab/game

        self.setWindowFlags(

            Qt.WindowType.FramelessWindowHint |

            Qt.WindowType.WindowStaysOnTopHint |

            Qt.WindowType.Tool

        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)



        screen = QApplication.primaryScreen().geometry()

        # Khung hình gốc 440x720 mở rộng headroom để đỉnh đầu/sừng/tóc không bao giờ bị cắt viền

        win_w = round(440 * self.current_scale)

        win_h = round(720 * self.current_scale)

        pos_x = screen.width() - win_w - 30

        pos_y = screen.height() - win_h - 50

        self.setGeometry(pos_x, pos_y, win_w, win_h)



    def set_model_scale(self, scale: float):

        """Tùy chỉnh kích cỡ model và giữ cố định chân chạm đất (Anchor to floor)"""

        scale = round(max(0.60, min(1.80, scale)), 2)

        if abs(scale - self.current_scale) < 0.01:

            return



        old_w = self.width()

        old_h = self.height()

        old_x = self.x()

        old_y = self.y()



        self.current_scale = scale

        self.bridge._settings["model_scale"] = scale

        try:

            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:

                json.dump(self.bridge._settings, f, indent=2, ensure_ascii=False)

        except Exception:

            pass



        new_w = round(440 * self.current_scale)

        new_h = round(720 * self.current_scale)



        # Giữ cố định chân Mora trên sàn desktop và nở đều sang 2 bên

        feet_y = old_y + old_h

        center_x = old_x + old_w // 2



        new_x = center_x - new_w // 2

        new_y = feet_y - new_h



        screen = QApplication.primaryScreen().geometry()

        new_x = max(0, min(screen.width() - new_w, new_x))

        new_y = max(0, min(screen.height() - new_h, new_y))



        self.setGeometry(new_x, new_y, new_w, new_h)



        if hasattr(self, 'chat_window') and self.chat_window.isVisible():

            self.chat_window.update_position()

        if hasattr(self, 'speech_popup'):

            self.speech_popup.update_position()

            self.speech_popup.show_message(f"🔍 Kích thước Mora: {int(scale * 100)}%")



    def wheelEvent(self, event):

        """Thu phóng kích cỡ model nhanh bằng Ctrl + Cuộn chuột"""

        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:

            delta = 0.05 if event.angleDelta().y() > 0 else -0.05

            self.set_model_scale(self.current_scale + delta)

            event.accept()

        else:

            super().wheelEvent(event)



    def init_web_engine(self):

        self.webview = QWebEngineView(self)

        self.webview.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.webview.page().setBackgroundColor(QColor(0, 0, 0, 0)) # Hoàn toàn trong suốt



        # Khóa hoàn toàn menu mặc định của Chromium (Back, Reload, Save image...)

        # và kết nối vào Menu ngữ cảnh tùy chỉnh khi ấn chuột phải vào Mora

        self.webview.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self.webview.customContextMenuRequested.connect(self.show_mora_context_menu)



        self.channel = QWebChannel(self.webview.page())

        self.channel.registerObject("pyBridge", self.bridge)

        self.webview.page().setWebChannel(self.channel)



        self.webview.load(QUrl(f"http://127.0.0.1:{PORT}/index.html"))

        self.setCentralWidget(self.webview)



    def show_mora_context_menu(self, pos):

        """Menu tùy chọn phong cách RedMagic Cyberpunk khi nhấp chuột phải vào Mora"""

        menu = QMenu(self)

        menu.setStyleSheet("""

            QMenu {

                background-color: #12131a;

                color: #f1f5f9;

                border: 2px solid #ff2b51;

                border-radius: 12px;

                padding: 6px;

                font-family: 'Segoe UI', system-ui, sans-serif;

                font-size: 13px;

                font-weight: 600;

            }

            QMenu::item {

                padding: 8px 24px;

                border-radius: 6px;

            }

            QMenu::item:selected {

                background-color: #ff2b51;

                color: #ffffff;

            }

            QMenu::separator {

                height: 1px;

                background: #334155;

                margin: 4px 8px;

            }

        """)



        chat_visible = self.chat_window.isVisible()

        chat_text = "💬 Ẩn Khung Chat" if chat_visible else "💬 Hiện Khung Chat"

        chat_act = QAction(chat_text, self)

        chat_act.triggered.connect(self.toggle_chat_bubble)

        menu.addAction(chat_act)



        # Lựa chọn Bật / Tắt Giọng Nói nhanh

        voice_on = self.bridge._settings.get("voice_enabled", True)

        voice_text = "🔊 Tắt Giọng Nói (Mute)" if voice_on else "🔇 Bật Giọng Nói (Unmute)"

        voice_act = QAction(voice_text, self)

        voice_act.triggered.connect(self.toggle_voice)

        menu.addAction(voice_act)



        # Menu Kích Cỡ Model

        scale_menu = menu.addMenu("🔍 Kích Cỡ Model (Ctrl + Cuộn chuột)")

        scale_menu.setStyleSheet(menu.styleSheet())

        scales = [

            (0.75, "75% (Nhỏ gọn)"),

            (1.00, "100% (Mặc định)"),

            (1.25, "125% (Lớn)"),

            (1.50, "150% (Rất lớn)")

        ]

        for s_val, s_label in scales:

            act = QAction(s_label, self)

            act.setCheckable(True)

            if abs(self.current_scale - s_val) < 0.05:

                act.setChecked(True)

            act.triggered.connect(lambda checked, s=s_val: self.set_model_scale(s))

            scale_menu.addAction(act)



        reset_act = QAction("🔄 Đặt Lại Vị Trí", self)

        reset_act.triggered.connect(self.reset_pos)

        menu.addAction(reset_act)



        # Chế độ đi dạo tự do trên màn hình (Desktop Roam)

        roam_enabled = self.bridge._settings.get("roam_enabled", False)

        roam_text = "🚶 Tắt Chế Độ Đi Dạo" if roam_enabled else "🚶 Bật Chế Độ Đi Dạo"

        roam_act = QAction(roam_text, self)

        roam_act.triggered.connect(self.toggle_desktop_roam)

        menu.addAction(roam_act)



        config_act = QAction("⚙️ Cài Đặt (API Key)", self)

        config_act.triggered.connect(self.open_settings)

        menu.addAction(config_act)



        clear_act = QAction("🧹 Bắt Đầu Cuộc Trò Chuyện Mới", self)

        clear_act.triggered.connect(self.clear_chat_history)

        menu.addAction(clear_act)



        menu.addSeparator()



        exit_act = QAction("❌ Thoát", self)

        exit_act.triggered.connect(QApplication.instance().quit)

        menu.addAction(exit_act)



        menu.exec(QCursor.pos())



    def init_global_mouse_tracker(self):

        """Theo dõi vị trí chuột và vận tốc di chuyển cửa sổ toàn hệ thống Windows"""

        self.prev_win_x = self.x()

        self.prev_win_y = self.y()

        self.mouse_timer = QTimer(self)

        self.mouse_timer.setInterval(25) # 40 FPS

        self.mouse_timer.timeout.connect(self.track_global_mouse)

        self.mouse_timer.start()



    def init_desktop_roamer(self):

        """Khởi tạo hệ thống Desktop Roaming (Mora tự động đi tuần / đi dạo trên màn hình Desktop)"""

        self.roam_state = "IDLE" # "IDLE" hoặc "WALK"

        self.roam_direction = 1  # 1: sang phải, -1: sang trái

        self.roam_speed = 1.6    # Pixel mỗi frame (~50px/giây di chuyển thong thả, tự nhiên)

        self.roam_timer_elapsed = 0.0

        self.roam_idle_duration = 10.0 # Đứng yên ngắm nhìn 10-15s

        self.roam_walk_duration = 8.0  # Đi dạo 6-10s

        self.last_walk_notify = None



        self.roam_timer = QTimer(self)

        self.roam_timer.setInterval(33) # 30 FPS

        self.roam_timer.timeout.connect(self.update_desktop_roam)



        if self.bridge._settings.get("roam_enabled", False):

            self.roam_timer.start()



    def toggle_voice(self):

        """Bật / Tắt âm thanh giọng nói của Mora (Voice Toggle)"""

        current = self.bridge._settings.get("voice_enabled", True)

        new_state = not current

        self.bridge._settings["voice_enabled"] = new_state



        if not new_state and hasattr(self.bridge, '_voice_engine'):

            self.bridge._voice_engine.stop_current_audio()



        try:

            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:

                json.dump(self.bridge._settings, f, indent=2, ensure_ascii=False)

        except Exception:

            pass



        if hasattr(self, 'chat_window') and hasattr(self.chat_window, 'update_sound_btn_icon'):

            self.chat_window.update_sound_btn_icon()



        self.update_tray_menu()



        status_msg = "🔊 Giọng nói Mora: ĐÃ BẬT" if new_state else "🔇 Giọng nói Mora: ĐÃ TẮT"

        if hasattr(self, 'speech_popup'):

            self.speech_popup.show_message(status_msg)



    def update_tray_voice_text(self):

        if hasattr(self, 'voice_tray_action'):

            v_on = self.bridge._settings.get("voice_enabled", True)

            self.voice_tray_action.setText("🔊 Giọng Nói: BẬT" if v_on else "🔇 Giọng Nói: TẮT")



    def update_tray_roam_text(self):

        if hasattr(self, 'roam_tray_action'):

            roam_enabled = self.bridge._settings.get("roam_enabled", False)

            self.roam_tray_action.setText("🚶 Tắt Chế Độ Đi Dạo" if roam_enabled else "🚶 Bật Chế Độ Đi Dạo")



    def toggle_desktop_roam(self):

        """Bật / Tắt chế độ Mora đi dạo Desktop"""

        curr = self.bridge._settings.get("roam_enabled", False)

        new_val = not curr

        self.bridge._settings["roam_enabled"] = new_val

        try:

            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:

                json.dump(self.bridge._settings, f, indent=2, ensure_ascii=False)

        except Exception:

            pass



        self.update_tray_roam_text()



        if new_val:

            self.roam_state = "IDLE"

            self.roam_timer_elapsed = 0

            self.roam_timer.start()

            if hasattr(self, 'speech_popup'):

                self.speech_popup.show_message("🚶 Mora bắt đầu đi dạo cùng Chủ nhân nha!")

        else:

            self.set_roam_state("IDLE")

            self.roam_timer.stop()

            if hasattr(self, 'speech_popup'):

                self.speech_popup.show_message("🛑 Mora dừng chân đứng cạnh bạn nè!")



    def set_roam_state(self, state: str):

        self.roam_state = state

        self.roam_timer_elapsed = 0

        is_walking = (state == "WALK")

        self.notify_mora_walking(is_walking, self.roam_direction)



    def notify_mora_walking(self, is_walking: bool, direction: int):

        cur_key = (is_walking, direction)

        if self.last_walk_notify == cur_key:

            return

        self.last_walk_notify = cur_key

        try:

            js = f"if (window.setMoraWalking) window.setMoraWalking({'true' if is_walking else 'false'}, {direction});"

            self.webview.page().runJavaScript(js)

        except Exception:

            pass



    def update_desktop_roam(self):

        try:

            if not self.bridge._settings.get("roam_enabled", True):

                if self.roam_state != "IDLE":

                    self.set_roam_state("IDLE")

                return



            # 1. Phát hiện tương tác: Nếu chuột đang rê vào Mora, đang mở khung chat gõ phím, hoặc đang hiện popup nói chuyện -> Dừng lại ngay

            cursor_pos = QCursor.pos()

            rel_x = cursor_pos.x() - self.x()

            rel_y = cursor_pos.y() - self.y()

            is_hover = self.is_cursor_over_character(rel_x, rel_y)

            is_chat_busy = (

                hasattr(self, 'chat_window') and

                self.chat_window.isVisible() and

                hasattr(self.chat_window, 'input_field') and

                self.chat_window.input_field.hasFocus()

            )

            is_popup_busy = hasattr(self, 'speech_popup') and self.speech_popup.isVisible()



            if is_hover or is_chat_busy or is_popup_busy:

                if self.roam_state != "IDLE":

                    self.set_roam_state("IDLE")

                return



            dt = 0.033

            self.roam_timer_elapsed += dt



            if self.roam_state == "IDLE":

                if self.roam_timer_elapsed >= self.roam_idle_duration:

                    screen = QApplication.primaryScreen().geometry()

                    min_x = 25

                    max_x = screen.width() - self.width() - 25



                    cur_x = self.x()

                    if cur_x >= max_x - 120:

                        self.roam_direction = -1

                    elif cur_x <= min_x + 120:

                        self.roam_direction = 1

                    else:

                        import random

                        self.roam_direction = 1 if random.random() > 0.5 else -1



                    self.set_roam_state("WALK")

                    import random

                    self.roam_walk_duration = random.uniform(6.0, 11.0)



            elif self.roam_state == "WALK":

                screen = QApplication.primaryScreen().geometry()

                min_x = 25

                max_x = screen.width() - self.width() - 25



                new_x = self.x() + self.roam_direction * self.roam_speed

                if new_x > max_x:

                    new_x = max_x

                    self.roam_direction = -1

                    self.notify_mora_walking(True, self.roam_direction)

                elif new_x < min_x:

                    new_x = min_x

                    self.roam_direction = 1

                    self.notify_mora_walking(True, self.roam_direction)



                self.move(round(new_x), self.y())



                if hasattr(self, 'chat_window') and self.chat_window.isVisible():

                    self.chat_window.update_position()

                if hasattr(self, 'speech_popup') and self.speech_popup.isVisible():

                    self.speech_popup.update_position()



                if self.roam_timer_elapsed >= self.roam_walk_duration:

                    self.set_roam_state("IDLE")

                    import random

                    self.roam_idle_duration = random.uniform(9.0, 16.0)

        except Exception as e:

            pass



    def is_cursor_over_character(self, rel_x: int, rel_y: int) -> bool:

        w = self.width()

        h = self.height()

        if w <= 0 or h <= 0:

            return False

        # Nếu chuột nằm ngoài giới hạn khung cửa sổ

        if rel_x < 0 or rel_x > w or rel_y < 0 or rel_y > h:

            return False



        nx = rel_x / w

        ny = rel_y / h

        dx = nx - 0.50



        # 1. Đỉnh đầu, tai sừng & tóc (Bo góc tròn hình elip theo đúng dáng đầu của Mora, không bị hộp vuông)

        if 0.035 <= ny <= 0.24:

            # Tâm Y = 0.14, bán kính ngang Rx = 0.18, bán kính dọc Ry = 0.105

            if (dx / 0.18) ** 2 + ((ny - 0.14) / 0.105) ** 2 <= 1.0:

                return True



        # 2. Cổ & Vai (Xuôi dốc theo mỏm vai tự nhiên)

        if 0.24 < ny <= 0.31:

            shoulder_half_w = 0.10 + (ny - 0.24) / 0.07 * 0.19

            if abs(dx) <= shoulder_half_w:

                return True



        # 3. Ngực & Cánh tay khoanh (Bust & Folded Arms)

        if 0.31 < ny <= 0.44:

            if abs(dx) <= 0.31:

                return True



        # 4. Eo, Váy bó & Cánh hư không (Waist, Skirt & Void Wings)

        if 0.44 < ny <= 0.65:

            skirt_half_w = 0.15 + (ny - 0.44) / 0.21 * 0.12

            if abs(dx) <= skirt_half_w:

                return True



        # 5. Đùi, Đầu gối, Bắp chân & Giày bốt (Legs & Boots)

        if 0.65 < ny <= 0.96:

            legs_half_w = 0.15 - (ny - 0.65) / 0.31 * 0.06

            if abs(dx) <= legs_half_w:

                return True



        return False



    def update_click_through(self, rel_x: int, rel_y: int):

        """Tự động xuyên click chuột vào desktop/icon/cửa sổ bên dưới khi chuột nằm ngoài nhân vật"""

        try:

            hwnd = int(self.winId())

            if not hwnd:

                return



            # Nếu chuột trái đang được giữ (đang kéo rê model), giữ nguyên cửa sổ tương tác

            left_down = bool(user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000)

            over_char = self.is_cursor_over_character(rel_x, rel_y)

            should_be_interactive = over_char or left_down



            if should_be_interactive and self.is_click_through:

                # Xóa cờ WS_EX_TRANSPARENT để nhận click vào Mora

                style = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)

                user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, style & ~WS_EX_TRANSPARENT)

                self.is_click_through = False

            elif not should_be_interactive and not self.is_click_through:

                # Bật cờ WS_EX_TRANSPARENT để xuyên click chuột xuống màn hình desktop

                style = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)

                user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, style | WS_EX_TRANSPARENT)

                self.is_click_through = True

        except Exception:

            pass



    def track_global_mouse(self):

        cpos = QCursor.pos()

        rel_x = cpos.x() - self.x()

        rel_y = cpos.y() - self.y()



        # Cập nhật xuyên click chuột cho vùng nền trong suốt xung quanh nhân vật

        self.update_click_through(rel_x, rel_y)



        # Tọa độ tương đối so với mắt của Mora

        center_x = self.x() + self.width() / 2

        center_y = self.y() + int(self.height() * 0.18) # Vị trí mắt/đầu chính xác theo tỷ lệ model



        screen = QApplication.primaryScreen().geometry()

        range_w = screen.width() * 0.40

        range_h = screen.height() * 0.35



        norm_x = (cpos.x() - center_x) / range_w

        norm_y = (cpos.y() - center_y) / range_h



        norm_x = max(-1.0, min(1.0, norm_x))

        norm_y = max(-1.0, min(1.0, norm_y))



        # Tính toán vận tốc kéo thả di chuyển vị trí model trên desktop

        cur_win_x = self.x()

        cur_win_y = self.y()

        win_vx = float(cur_win_x - self.prev_win_x)

        win_vy = float(cur_win_y - self.prev_win_y)

        self.prev_win_x = cur_win_x

        self.prev_win_y = cur_win_y



        # Cập nhật vị trí khung chat & pop-up chạy theo Mora nếu đang mở

        if (cur_win_x != self.prev_win_x or cur_win_y != self.prev_win_y):

            if hasattr(self, 'chat_window') and self.chat_window.isVisible():

                self.chat_window.update_position()

            if hasattr(self, 'speech_popup') and self.speech_popup.isVisible():

                self.speech_popup.update_position()



        # Gửi tọa độ chuột và gia tốc di chuyển cho Three.js để quay đầu và tạo quán tính đung đưa tóc

        self.webview.page().runJavaScript(f"if (window.onGlobalMouseMove) window.onGlobalMouseMove({norm_x:.4f}, {norm_y:.4f}, {win_vx:.2f}, {win_vy:.2f});")



    def init_tray(self):

        self.tray = QSystemTrayIcon(self)

        icon_path = os.path.join(BASE_DIR, "assets", "mora_vtuber.png")

        if os.path.exists(icon_path):

            self.tray.setIcon(QIcon(icon_path))

        self.tray.setToolTip("✨ Mora 3D VTuber (RedMagic Cel-Shaded)")



        self.tray_menu = QMenu()



        self.chat_toggle_action = QAction(self)

        self.voice_tray_action = QAction(self)

        self.update_tray_menu()

        self.chat_toggle_action.triggered.connect(self.toggle_chat_bubble)

        self.tray_menu.addAction(self.chat_toggle_action)

        self.voice_tray_action.triggered.connect(self.toggle_voice)

        self.tray_menu.addAction(self.voice_tray_action)



        reset_action = QAction("🔄 Reset Vị Trí", self)

        reset_action.triggered.connect(self.reset_pos)

        self.tray_menu.addAction(reset_action)



        self.roam_tray_action = QAction(self)

        self.update_tray_roam_text()

        self.roam_tray_action.triggered.connect(self.toggle_desktop_roam)

        self.tray_menu.addAction(self.roam_tray_action)



        scale_tray_menu = self.tray_menu.addMenu("🔍 Kích Cỡ Model")

        scales = [

            (0.75, "75% (Nhỏ gọn)"),

            (1.00, "100% (Mặc định)"),

            (1.25, "125% (Lớn)"),

            (1.50, "150% (Rất lớn)")

        ]

        for s_val, s_label in scales:

            act = QAction(s_label, self)

            act.setCheckable(True)

            if abs(self.current_scale - s_val) < 0.05:

                act.setChecked(True)

            act.triggered.connect(lambda checked, s=s_val: self.set_model_scale(s))

            scale_tray_menu.addAction(act)



        config_action = QAction("⚙️ Mở Cài Đặt (API Key)", self)

        config_action.triggered.connect(self.open_settings)

        self.tray_menu.addAction(config_action)



        self.tray_menu.addSeparator()

        exit_action = QAction("❌ Thoát", self)

        exit_action.triggered.connect(QApplication.instance().quit)

        self.tray_menu.addAction(exit_action)



        self.tray.setContextMenu(self.tray_menu)

        self.tray.show()



    def update_tray_menu(self):

        is_shown = self.chat_window.isVisible() if hasattr(self, 'chat_window') else self.bridge._settings.get("show_chat_bubble", False)

        if is_shown:

            self.chat_toggle_action.setText("💬 Ẩn Khung Chat")

        else:

            self.chat_toggle_action.setText("💬 Hiện Khung Chat")

        self.update_tray_voice_text()



    def toggle_chat_bubble(self):

        cur = self.chat_window.isVisible()

        new_val = not cur

        self.bridge.set_bubble_visible(new_val)

        if new_val:

            self.chat_window.update_position()

            self.chat_window.show()

        else:

            self.chat_window.hide()

        self.update_tray_menu()



    def reset_pos(self):

        screen = QApplication.primaryScreen().geometry()

        self.move(screen.width() - self.width() - 30, screen.height() - self.height() - 50)

        if hasattr(self, 'chat_window') and self.chat_window.isVisible():

            self.chat_window.update_position()

        if hasattr(self, 'speech_popup') and self.speech_popup.isVisible():

            self.speech_popup.update_position()



    def clear_chat_history(self):

        if hasattr(self.bridge, '_brain') and hasattr(self.bridge._brain, 'memory_manager'):

            self.bridge._brain.memory_manager.clear_chat_history()

        if hasattr(self, 'chat_window'):

            self.chat_window.set_mora_text("Mora đã sẵn sàng cho cuộc trò chuyện mới!")

        if hasattr(self, 'speech_popup'):

            self.speech_popup.show_message("Mora đã sẵn sàng cho cuộc trò chuyện mới!")



    def open_settings(self):

        try:

            dialog = MoraSettingsDialog(self.bridge._settings, self)

            if dialog.exec():

                # Cập nhật cài đặt ngay lập tức vào AI Brain

                if hasattr(self.bridge, '_brain'):

                    self.bridge._brain.settings = self.bridge._settings

        except Exception as e:

            import subprocess

            try:

                os.startfile(SETTINGS_FILE)

            except Exception:

                subprocess.Popen(["notepad.exe", SETTINGS_FILE])



def main():

    server_thread = threading.Thread(target=start_local_server, daemon=True)

    server_thread.start()



    with open(CHARACTERS_FILE, "r", encoding="utf-8") as f:

        characters = json.load(f)

    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:

        settings = json.load(f)



    char_id = settings.get("active_character", "mora_redmagic")

    current_char = next((c for c in characters if c["id"] == char_id), characters[0])



    voice_engine = VoiceEngine()

    vision_engine = VisionEngine()

    memory_manager = MemoryManager(os.path.join(CONFIG_DIR, "memory.json"))

    ai_brain = AIBrain(settings, memory_manager)



    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL, True)

    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)



    app = QApplication(sys.argv)

    app.setApplicationName("Mora 3D VTuber")

    # Đảm bảo ứng dụng Desktop Pet luôn chạy ngầm và không tự ý tắt khi các cửa sổ pop-up/chat đóng

    app.setQuitOnLastWindowClosed(False)



    bridge = WebBridge(settings, current_char, ai_brain, voice_engine, vision_engine)

    window = Mora3DWindow(bridge)

    window.show()



    sys.exit(app.exec())



if __name__ == "__main__":

    main()

