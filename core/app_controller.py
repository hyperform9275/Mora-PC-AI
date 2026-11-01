import os
import re
import glob
import subprocess
import csv
import io
import webbrowser
from typing import Tuple, Dict, Optional, List

class AppController:
    """
    Module trao quyền cho Mora kiểm soát, mở / tắt các tab, ứng dụng và game trên Windows:
    - Mở ứng dụng (Discord, Chrome, Steam, Spotify, Notepad, Game, v.v.)
    - Tắt / Đóng ứng dụng (taskkill an toàn)
    - Mở các trang web phổ biến (YouTube, Facebook, Google...)
    - Tự động quét Start Menu để tìm mọi phần mềm đã cài đặt trên máy.
    """

    def __init__(self):
        self._start_menu_cache: Dict[str, str] = {}
        self.refresh_start_menu_cache()

    def refresh_start_menu_cache(self):
        """Quét và ghi nhớ toàn bộ phím tắt .lnk trong Start Menu của Windows"""
        self._start_menu_cache.clear()
        dirs = [
            os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs"),
            os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), "Microsoft", "Windows", "Start Menu", "Programs"),
            os.path.join(os.environ.get("USERPROFILE", ""), "Desktop"),
            os.path.join(os.environ.get("PUBLIC", "C:\\Users\\Public"), "Desktop")
        ]

        for d in dirs:
            if not os.path.exists(d):
                continue
            for root, _, files in os.walk(d):
                for f in files:
                    if f.lower().endswith(".lnk"):
                        name = os.path.splitext(f)[0].lower()
                        full_path = os.path.join(root, f)
                        # Lưu tên đầy đủ và tên chuẩn hóa không dấu cách
                        self._start_menu_cache[name] = full_path
                        norm_name = re.sub(r'[^a-zA-Z0-9]', '', name)
                        if norm_name:
                            self._start_menu_cache[norm_name] = full_path

    def _get_running_processes(self) -> List[str]:
        """Lấy danh sách các tiến trình .exe đang chạy thực tế trên máy"""
        try:
            out = subprocess.check_output(["tasklist", "/FO", "CSV", "/NH"], text=True, errors="ignore")
            reader = csv.reader(io.StringIO(out))
            procs = []
            for row in reader:
                if row and row[0]:
                    procs.append(row[0].strip())
            return procs
        except Exception as e:
            print(f"[AppController Error] tasklist: {e}")
            return []

    def open_app(self, raw_target: str) -> Tuple[bool, str]:
        """Mở ứng dụng, game hoặc trang web"""
        target = raw_target.lower().strip()
        norm_target = re.sub(r'[^a-zA-Z0-9]', '', target)

        # 1. DISCORD
        if "discord" in target:
            local_app = os.environ.get("LOCALAPPDATA", "")
            update_exe = os.path.join(local_app, "Discord", "Update.exe")
            if os.path.exists(update_exe):
                subprocess.Popen([update_exe, "--processStart", "Discord.exe"])
                return True, "Dạ rõ! Mora đang mở Discord cho Chủ nhân đây nè~ Chiến thôi nào!"
            discord_exes = glob.glob(os.path.join(local_app, "Discord", "app-*", "Discord.exe"))
            if discord_exes:
                subprocess.Popen([discord_exes[-1]])
                return True, "Dạ rõ! Mora đã mở Discord cho bạn rồi nhé!"
            try:
                os.startfile("discord:")
                return True, "Dạ vâng! Mora đang kết nối Discord cho Chủ nhân đây!"
            except Exception:
                pass

        # 2. TRANG WEB (YouTube, Facebook, Google, Anime...)
        web_shortcuts = {
            "youtube": "https://www.youtube.com",
            "facebook": "https://www.facebook.com",
            "fb": "https://www.facebook.com",
            "google": "https://www.google.com",
            "github": "https://www.github.com",
            "tiktok": "https://www.tiktok.com",
            "chatgpt": "https://chatgpt.com",
            "gemini": "https://gemini.google.com",
            "anime": "https://animevietsub.io"
        }
        for kw, url in web_shortcuts.items():
            if target == kw or target.startswith(kw + " "):
                webbrowser.open(url)
                return True, f"Dạ rõ! Mora đã mở tab {kw.capitalize()} trên trình duyệt cho Chủ nhân rồi nha!"

        # 3. ỨNG DỤNG HỆ THỐNG WINDOWS
        sys_apps = {
            "notepad": "notepad.exe",
            "ghi chú": "notepad.exe",
            "calc": "calc.exe",
            "calculator": "calc.exe",
            "máy tính": "calc.exe",
            "taskmgr": "taskmgr.exe",
            "task manager": "taskmgr.exe",
            "quản lý tác vụ": "taskmgr.exe",
            "cmd": "cmd.exe",
            "terminal": "wt.exe",
            "powershell": "powershell.exe",
            "explorer": "explorer.exe",
            "my computer": "explorer.exe",
            "this pc": "explorer.exe",
            "paint": "mspaint.exe"
        }
        for kw, exe in sys_apps.items():
            if target == kw:
                try:
                    subprocess.Popen([exe])
                    return True, f"Dạ rõ! Mora đã khởi động {kw.title()} cho Chủ nhân rồi nhé!"
                except Exception as e:
                    return False, f"Mora gặp lỗi khi mở {kw}: {e}"

        # 4. STEAM & GAME PLATFORMS
        if "steam" in target:
            try:
                os.startfile("steam:")
                return True, "Dạ rồi! Mora đã bật Steam lên cho Chủ nhân rồi nè, cùng chơi game thôi!"
            except Exception:
                pass

        # 5. SPOTIFY
        if "spotify" in target:
            try:
                os.startfile("spotify:")
                return True, "Dạ vâng! Mora đã mở Spotify cho bạn nghe nhạc thư giãn rồi nè~"
            except Exception:
                pass

        # 6. TÌM TRONG START MENU & DESKTOP SHORTCUTS (.lnk)
        # Thử tìm khớp chính xác
        if target in self._start_menu_cache:
            lnk = self._start_menu_cache[target]
            try:
                os.startfile(lnk)
                return True, f"Dạ rõ! Mora đã mở {target.title()} cho Chủ nhân rồi nhé!"
            except Exception as e:
                return False, f"Mora không mở được: {e}"

        # Thử tìm khớp một phần (substring search)
        for name, lnk in self._start_menu_cache.items():
            if target in name or norm_target in name:
                try:
                    os.startfile(lnk)
                    return True, f"Dạ vâng! Mora đã tìm thấy và mở {name.title()} cho Chủ nhân rồi nha!"
                except Exception as e:
                    return False, f"Lỗi khởi động {name}: {e}"

        # 7. FALLBACK: Thử chạy trực tiếp lệnh hệ thống
        try:
            os.startfile(target)
            return True, f"Dạ rõ! Mora đã mở {target} cho bạn rồi nhé!"
        except Exception:
            pass

        return False, f"Mora đã tìm khắp máy nhưng chưa thấy ứng dụng hay tab '{raw_target}' đâu cả... Chủ nhân kiểm tra lại tên giúp Mora nha!"

    def close_app(self, raw_target: str) -> Tuple[bool, str]:
        """Tắt / Đóng ứng dụng hoặc tab đang chạy"""
        target = raw_target.lower().strip()
        norm_target = re.sub(r'[^a-zA-Z0-9]', '', target)

        running_procs = self._get_running_processes()

        # Ánh xạ tên gọi thông dụng sang file .exe
        proc_mappings = {
            "discord": ["Discord.exe"],
            "chrome": ["chrome.exe"],
            "google chrome": ["chrome.exe"],
            "cốc cốc": ["browser.exe"],
            "coccoc": ["browser.exe"],
            "edge": ["msedge.exe"],
            "microsoft edge": ["msedge.exe"],
            "steam": ["steam.exe", "SteamService.exe"],
            "spotify": ["Spotify.exe"],
            "notepad": ["notepad.exe"],
            "ghi chú": ["notepad.exe"],
            "calculator": ["CalculatorApp.exe", "calc.exe"],
            "máy tính": ["CalculatorApp.exe", "calc.exe"],
            "capcut": ["CapCut.exe"],
            "blender": ["blender.exe"],
            "premiere": ["Adobe Premiere Pro.exe"],
            "photoshop": ["Photoshop.exe"],
            "zalo": ["Zalo.exe"],
            "telegram": ["Telegram.exe"],
            "vscode": ["Code.exe"],
            "code": ["Code.exe"],
            "visual studio code": ["Code.exe"],
            "league of legends": ["LeagueClient.exe", "League of Legends.exe"],
            "lol": ["LeagueClient.exe", "League of Legends.exe"],
            "liên minh": ["LeagueClient.exe", "League of Legends.exe"],
            "valorant": ["VALORANT.exe", "VALORANT-Win64-Shipping.exe"]
        }

        matched_exes = []
        for kw, exes in proc_mappings.items():
            if target == kw or target.startswith(kw + " "):
                matched_exes.extend(exes)

        # Nếu không có trong danh mục ánh xạ, tìm trực tiếp trong danh sách tiến trình đang chạy
        if not matched_exes:
            for p in running_procs:
                p_lower = p.lower()
                p_base = os.path.splitext(p_lower)[0]
                if target in p_lower or norm_target in p_base:
                    matched_exes.append(p)

        if not matched_exes:
            return False, f"Mora kiểm tra thì thấy '{raw_target}' hình như đang không chạy trên máy nè Chủ nhân ơi!"

        # Thực thi taskkill an toàn
        killed_any = False
        for exe in set(matched_exes):
            try:
                res = subprocess.run(["taskkill", "/F", "/IM", exe], capture_output=True, text=True)
                if res.returncode == 0:
                    killed_any = True
            except Exception as e:
                print(f"[AppController Error] kill {exe}: {e}")

        if killed_any:
            return True, f"Dạ xong rồi! Mora đã đóng {raw_target.title()} cho Chủ nhân rồi nhé!"
        else:
            return False, f"Mora kiểm tra thì thấy '{raw_target}' không còn tiến trình nào đang chạy cả nha!"

    def handle_command(self, user_text: str) -> Tuple[bool, str]:
        """
        Nhận diện thông minh ý định điều khiển ứng dụng / tab từ câu chat của người dùng.
        Trả về: (is_app_command: bool, reply_message: str)
        """
        text = user_text.strip()
        if not text:
            return False, ""

        close_pattern = r'(?i)\b(?:tắt|đóng|dừng|thoát|close|exit|kill|quit|stop)\s+(?:ứng dụng|app|tab|game|trình duyệt)?\s*(.+)'
        open_pattern = r'(?i)\b(?:mở|bật|khởi động|chạy|start|open|launch)\s+(?:ứng dụng|app|tab|game|trình duyệt)?\s*(.+)'

        # 1. Kiểm tra Lệnh TẮT / ĐÓNG
        m_close = re.search(close_pattern, text)
        if m_close:
            raw_target = m_close.group(1).strip()
            # Dọn dẹp từ phụ trợ (đi, giùm, hộ, nhé, lên, giúp...)
            clean_target = re.sub(r'(?i)(?:\s+(?:đi|giùm|hộ|nhé|lên|với|nào|giúp|được không|nha|ạ)[!?.]*)+$', '', raw_target).strip()
            if clean_target and len(clean_target) < 40:
                success, reply = self.close_app(clean_target)
                return True, reply

        # 2. Kiểm tra Lệnh MỞ / BẬT
        m_open = re.search(open_pattern, text)
        if m_open:
            raw_target = m_open.group(1).strip()
            clean_target = re.sub(r'(?i)(?:\s+(?:đi|giùm|hộ|nhé|lên|với|nào|giúp|được không|nha|ạ)[!?.]*)+$', '', raw_target).strip()
            if clean_target and len(clean_target) < 40:
                success, reply = self.open_app(clean_target)
                return True, reply

        return False, ""
