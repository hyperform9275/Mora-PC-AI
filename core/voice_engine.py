import os
import sys
import random
import threading
import ctypes
import tempfile
import subprocess
import glob

class VoiceEngine:
    """
    Hệ thống Âm thanh & Giọng nói Mora Hybrid (Hybrid Voice Architecture):
    1. Local Voice Bank (assets/voice_bank/):
       - Chứa các file ghi âm mẫu (.mp3, .wav) phân loại theo từng bộ phận cơ thể & tình huống.
       - Phát phản ứng tức thì (0ms latency), không phụ thuộc vào kết nối mạng, siêu mượt.
    2. Dynamic AI Neural Speech (Edge-TTS):
       - Tự động tổng hợp giọng nói waifu thời gian thực cho các câu trả lời trí tuệ nhân tạo (Gemini, Grok, GPT, Ollama).
    """
    AVAILABLE_VOICES = {
        "vi_female": {"id": "vi-VN-HoaiMyNeural", "name": "Hoài My (Nữ - Tiếng Việt dễ thương)"},
        "vi_male": {"id": "vi-VN-NamMinhNeural", "name": "Nam Minh (Nam - Tiếng Việt chuẩn)"},
        "ja_anime": {"id": "ja-JP-NanamiNeural", "name": "Nanami (Nữ - Anime Nhật Bản)"},
        "en_cyber": {"id": "en-US-AvaNeural", "name": "Ava (Nữ - AI Tiếng Anh)"}
    }

    PART_MAPPINGS = {
        "patting": "patting",
        "head": "head",
        "face": "face",
        "lips": "lips",
        "chest": "chest",
        "belly": "belly",
        "pelvis": "pelvis",
        "neck": "neck",
        "shoulders": "shoulders",
        "arms": "arms",
        "thighs": "thighs",
        "legs": "legs"
    }

    FALLBACK_CHAINS = {
        "thighs": ["thighs", "legs", "pelvis"],
        "legs": ["legs", "thighs"],
        "belly": ["belly", "chest"],
        "chest": ["chest", "belly"],
        "lips": ["lips", "face", "head"],
        "neck": ["neck", "shoulders", "head"],
        "shoulders": ["shoulders", "neck", "arms"],
        "arms": ["arms", "shoulders"],
        "face": ["face", "head"],
        "head": ["head", "patting"],
        "patting": ["patting", "head"],
        "pelvis": ["pelvis"]
    }

    def __init__(self, base_dir: str = None):
        self.winmm = ctypes.windll.winmm
        self.is_playing = False
        self._lock = threading.Lock()
        
        if base_dir is None:
            self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        else:
            self.base_dir = base_dir

        self.voice_bank_dir = os.path.join(self.base_dir, "assets", "voice_bank")
        self.temp_dir = tempfile.gettempdir()
        self.current_audio_file = os.path.join(self.temp_dir, "mora_voice.mp3")

    def stop_current_audio(self):
        """Dừng âm thanh đang phát ngay lập tức"""
        try:
            self.winmm.mciSendStringW("stop mora_audio", None, 0, 0)
            self.winmm.mciSendStringW("close mora_audio", None, 0, 0)
            self.is_playing = False
        except Exception:
            pass

    def play_audio_file(self, file_path: str, on_finished=None) -> bool:
        """
        Phát trực tiếp một file audio (.mp3, .wav) từ Voice Bank trong luồng riêng.
        Phản hồi ngay tức thì (0ms latency), không đơ giao diện.
        """
        if not file_path or not os.path.exists(file_path):
            return False

        def run_thread():
            with self._lock:
                try:
                    self.stop_current_audio()

                    # Lấy short path để đảm bảo mciSendStringW luôn tương thích với đường dẫn Unicode tiếng Việt
                    buf = ctypes.create_unicode_buffer(500)
                    ctypes.windll.kernel32.GetShortPathNameW(os.path.abspath(file_path), buf, 500)
                    short_path = buf.value or os.path.abspath(file_path)

                    self.winmm.mciSendStringW("close mora_audio", None, 0, 0)
                    open_cmd = f'open "{short_path}" type mpegvideo alias mora_audio'
                    self.winmm.mciSendStringW(open_cmd, None, 0, 0)
                    self.is_playing = True
                    self.winmm.mciSendStringW("play mora_audio wait", None, 0, 0)
                    self.winmm.mciSendStringW("close mora_audio", None, 0, 0)
                except Exception as e:
                    print(f"[VoiceEngine Audio Play Error] {e}")
                finally:
                    self.is_playing = False
                    if on_finished:
                        on_finished()

        thread = threading.Thread(target=run_thread, daemon=True)
        thread.start()
        return True

    def get_voice_for_part(self, part: str) -> str | None:
        """
        Tìm kiếm file âm thanh trong Local Voice Bank tương ứng với bộ phận va chạm.
        Hỗ trợ fallback sang các bộ phận lân cận nếu thư mục bộ phận hiện tại chưa có file.
        """
        chain = self.FALLBACK_CHAINS.get(part, [part])
        for p in chain:
            dir_path = os.path.join(self.voice_bank_dir, "reactions", p)
            if os.path.isdir(dir_path):
                candidates = []
                for ext in ("*.mp3", "*.wav"):
                    for f in glob.glob(os.path.join(dir_path, ext)):
                        try:
                            if os.path.getsize(f) > 1000:
                                candidates.append(f)
                        except OSError:
                            pass
                if candidates:
                    return random.choice(candidates)
        return None

    def get_voice_for_greeting(self) -> str | None:
        """Tìm file âm thanh chào hỏi khởi động từ Voice Bank"""
        greet_dir = os.path.join(self.voice_bank_dir, "greetings")
        if os.path.isdir(greet_dir):
            candidates = []
            for ext in ("*.mp3", "*.wav"):
                for f in glob.glob(os.path.join(greet_dir, ext)):
                    try:
                        if os.path.getsize(f) > 1000:
                            candidates.append(f)
                    except OSError:
                        pass
            if candidates:
                return random.choice(candidates)
        return None

    def play_hitbox_voice(self, part: str, fallback_text: str = "", voice: str = "vi-VN-HoaiMyNeural", rate: str = "+5%", on_finished=None) -> bool:
        """
        [Cơ chế Hybrid] Ưu tiên tìm trong Voice Bank cục bộ:
        - Nếu có file audio: Phát ngay lập tức 0ms (Local Instant Play).
        - Nếu chưa có: Tự động dùng Edge-TTS đọc fallback_text (Online TTS Fallback).
        """
        local_file = self.get_voice_for_part(part)
        if local_file:
            return self.play_audio_file(local_file, on_finished=on_finished)
        elif fallback_text:
            self.speak(fallback_text, voice=voice, rate=rate, on_finished=on_finished)
            return False
        return False

    def play_greeting_voice(self, greetings: list, voice: str = "vi-VN-HoaiMyNeural", rate: str = "+5%", on_finished=None) -> bool:
        """[Cơ chế Hybrid] Chào hỏi: ưu tiên file audio cục bộ, nếu chưa có thì dùng TTS"""
        local_file = self.get_voice_for_greeting()
        if local_file:
            return self.play_audio_file(local_file, on_finished=on_finished)
        elif greetings:
            txt = random.choice(greetings)
            self.speak(txt, voice=voice, rate=rate, on_finished=on_finished)
            return False
        return False

    def speak(self, text: str, voice: str = "vi-VN-HoaiMyNeural", rate: str = "+5%", on_finished=None):
        """
        Nói một câu thoại tự do qua Edge-TTS (dành cho đối thoại AI Gemini/Grok hoặc soi màn hình).
        Chạy trong luồng riêng biệt, không làm lag giao diện.
        """
        def run_thread():
            try:
                self.stop_current_audio()
                clean_text = "".join(c for c in text if c.isprintable() and ord(c) < 10000)
                clean_text = clean_text.replace("...", ",").replace("~", "").replace("*", "").rstrip("! ")
                if not clean_text.strip():
                    clean_text = text

                # Dùng subprocess gọi module edge_tts độc lập, ổn định tuyệt đối
                cmd = [
                    sys.executable, "-m", "edge_tts",
                    "--text", clean_text,
                    "--voice", voice,
                    "--rate", rate,
                    "--write-media", self.current_audio_file
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
                
                if res.returncode == 0 and os.path.exists(self.current_audio_file) and os.path.getsize(self.current_audio_file) > 1000:
                    self.play_audio_file(self.current_audio_file, on_finished=on_finished)
                else:
                    if on_finished:
                        on_finished()
            except Exception as e:
                print(f"[VoiceEngine TTS Error] {e}")
                if on_finished:
                    on_finished()

        thread = threading.Thread(target=run_thread, daemon=True)
        thread.start()
