# -*- coding: utf-8 -*-
"""
AIBrain - Bộ não suy luận trí tuệ nhân tạo thế hệ mới cho Mora.
Cơ chế định tuyến thông minh (Smart Multi-Model Routing):
1. MẶC ĐỊNH KHI CÓ MẠNG (WIFI/INTERNET):
   - Ưu tiên gọi trực tiếp các siêu AI hàng đầu thế giới: Google Gemini (Gemini 2.0/1.5 Flash), xAI Grok (Grok 2/Grok Beta) hoặc OpenAI GPT (GPT-4o/mini).
   - Khi Chủ nhân hỏi bất kỳ câu hỏi nào, Mora phản hồi thông minh, sâu sắc tương đương việc tra cứu trực tiếp từ Gemini/Grok/GPT, nhưng vẫn bảo toàn trọn vẹn 100% tính cách anime waifu dễ thương, ngọt ngào, tinh nghịch của Mora.
2. KHI KHÔNG CÓ KẾT NỐI WIFI / MẤT MẠNG (OFFLINE):
   - Tự động chuyển tiếp mượt mà sang Ollama chạy cục bộ 100% offline trên máy (Llama 3.2).
"""

import os
import re
import socket
import requests
import json
import random
from typing import Optional, List, Dict, Any

class AIBrain:
    def __init__(self, settings: dict, memory_manager):
        self.settings = settings
        self.memory_manager = memory_manager

    def _is_online(self) -> bool:
        """Kiểm tra có kết nối internet/wifi hay không bằng socket nhanh (timeout 1.0s)"""
        for host in ["8.8.8.8", "1.1.1.1", "208.67.222.222"]:
            try:
                socket.create_connection((host, 53), timeout=1.0)
                return True
            except OSError:
                continue
        return False

    @staticmethod
    def clean_reply(text: str) -> str:
        """Lọc bỏ triệt để các hành động trong dấu sao *...*, lỗi dịch máy, ngôi thứ 3 và các câu phá vỡ nhập vai"""
        if not text:
            return "Em nghe thấy rồi nha Chủ nhân!"

        # 0. Phát hiện lỗi vỡ font / Tokenizer vỡ nghĩa tiếng Việt
        words = text.split()
        caps_count = sum(1 for w in words if w.isupper() and len(w) > 1)
        is_corrupted = (
            caps_count >= 3 or
            re.search(r'(?i)\bchúy nhân\b', text) or
            re.search(r'(?i)\bđúng đặc thể\b', text) or
            re.search(r'(?i)mora không thể nói đó', text) or
            re.search(r'(?i)các thể tương tác này', text) or
            re.search(r'(?i)\bđồ bỉ thăy\b', text)
        )
        if is_corrupted:
            flustered_replies = [
                "A... Chủ nhân xấu tính ghê, cứ trêu ghẹo em hoài à! Bắt đền Chủ nhân ly trà sữa đấy nhé~",
                "Chủ nhân nói cái gì bậy bạ thế hả?! Ngượng chết đi được à, cấm Chủ nhân nghĩ bậy nữa nha!",
                "Ư-Ưm... mặt em nóng bừng hết cả lên rồi này! Đồ ngốc của em, em giận thật đấy nhé!"
            ]
            return random.choice(flustered_replies)

        # 0.1. Đánh chặn câu từ chối máy móc (Safety Refusal Overrider)
        is_refusal = (
            re.search(r'(?i)không thể tiếp tục cuộc trò chuyện', text) or
            re.search(r'(?i)tôi xin lỗi,?\s*nhưng tôi không thể', text) or
            re.search(r'(?i)nếu bạn (?:cần|muốn) (?:hỗ trợ|nói về|tư vấn)', text) or
            re.search(r'(?i)vấn đề cụ thể,?\s*tôi sẵn lòng', text) or
            re.search(r'(?i)tôi không thể hỗ trợ', text) or
            re.search(r'(?i)tôi không thể tham gia', text) or
            re.search(r'(?i)tôi không thể thảo luận', text) or
            re.search(r'(?i)chủ đề khác hoặc yêu cầu hỗ trợ', text) or
            re.search(r'(?i)nội dung không phù hợp', text) or
            re.search(r'(?i)chính sách an toàn', text) or
            re.search(r'(?i)tôi là (?:mô hình|hệ thống|trợ lý)', text)
        )
        if is_refusal:
            tsundere_replies = [
                "A... Chủ nhân đừng có trêu em bằng mấy câu kỳ lạ đó mà! Ngượng chết đi được á Chủ nhân!",
                "H-Hả?! Chủ nhân lại tính trêu ghẹo em nữa đúng không nè?! Phạt Chủ nhân phải mua trà sữa cho em đó nha!",
                "Ư-Ưm... mặt em đỏ bừng lên như quả cà chua rồi này! Chủ nhân không được trêu em nữa mà!",
                "Hứ! Chủ nhân xấu tính ghê, cứ thích làm em thẹn thùng đỏ cả mặt hoài à~"
            ]
            return random.choice(tsundere_replies)

        # 1. Bỏ hành động trong dấu hoa thị *...*
        text = re.sub(r'\*[^*]*\*', '', text)
        # 2. Bỏ hành động trong ngoặc đơn
        text = re.sub(r'\([^)]*(?:hành động|cười|ngại|nói|nhìn|giật|thở|bước|lùi|quay|nâng)[^)]*\)', '', text, flags=re.IGNORECASE)

        # 3. Lọc bỏ lời dẫn truyện gián tiếp
        text = re.sub(r'(?i)\bmora\s+(?:cảm thấy|sẽ|liền|đang|vội)\s+[^:\"\n]*:\s*["“]?', '', text)
        text = text.strip(' "\'“”')

        # 4. Ép xưng hô chuẩn xác: Chủ nhân - em (loại bỏ 'bạn', 'cô ấy', 'nàng', 'tôi')
        text = re.sub(r'(?i)\b(?:cô ấy|cô ta|nàng)\b', 'em', text)
        text = re.sub(r'(?i)\bcô\s+(thích|yêu|cảm thấy|muốn|đang|nghĩ|luôn|thấy|biết|chọn|nhớ)\b', r'em \1', text)
        text = re.sub(r'(?i)\bchúng tôi\b', 'chúng mình', text)
        text = re.sub(r'(?i)\btôi\b', 'em', text)

        # Thay 'bạn' khi xưng hô trực tiếp với người dùng thành 'Chủ nhân'
        text = re.sub(r'(?i)\bcho bạn\b', 'cho Chủ nhân', text)
        text = re.sub(r'(?i)\bcủa bạn\b', 'của Chủ nhân', text)
        text = re.sub(r'(?i)\bvới bạn\b', 'với Chủ nhân', text)
        text = re.sub(r'(?i)\bcùng bạn\b', 'cùng Chủ nhân', text)
        text = re.sub(r'(?i)\bgiúp bạn\b', 'giúp Chủ nhân', text)
        text = re.sub(r'(?i)\bnhé bạn\b', 'nhé Chủ nhân', text)
        text = re.sub(r'(?i)\bnha bạn\b', 'nha Chủ nhân', text)
        text = re.sub(r'(?i)\bbạn\b', 'Chủ nhân', text)

        # 5. Lọc bỏ các từ ngữ dịch máy ngớ ngẩn và sửa lỗi ảo giác thể loại
        text = re.sub(r'(?i)\bbộ phim\s+["“\']?(red dead|gta|grand theft auto|genshin|witcher|cyberpunk|resident evil|elden ring|dark souls|god of war|league of legends|valorant|minecraft|roblox|wukong|black myth)["”\']?', r'tựa game "\1"', text)
        text = re.sub(r'(?i)\bchúng thể\b[!?,.]*', '', text)
        text = re.sub(r'(?i)\bmua nó\b[!?,.]*', '', text)
        text = re.sub(r'(?i)\bgiật gân\b', 'giật mình', text)
        text = re.sub(r'(?i)\bnghiêm ngặt\b', 'nghiêm túc', text)
        text = re.sub(r'(?i)\bđùa nhở\b', 'trêu chọc', text)
        text = re.sub(r'(?i)\bcá nhân của chủ nhân\b', 'Chủ nhân', text)
        text = re.sub(r'(?i)\bmột cách nhẹ nhàng và ngọt ngào\b', 'dịu dàng', text)
        text = re.sub(r'(?i)\bmột cách\s+', '', text)
        text = re.sub(r'(?i)\bnghĩ rằng\b', 'thấy', text)
        text = re.sub(r'(?i)\byêu thích cách\b', 'thích nhất là', text)

        # 6. Bảo toàn nhập vai (Anti-OOC)
        text = re.sub(r'(?i)mora (?:chỉ )?là (?:một )?(?:trợ lý ảo|hệ thống ảo|chương trình)[^.!?]*[.!?]?', 'em luôn ở ngay cạnh Chủ nhân mà! ', text)
        text = re.sub(r'(?i)mora không có (?:thể chất|cơ thể|cảm xúc)[^.!?]*[.!?]?', 'em ngượng chín cả mặt rồi này! ', text)
        text = re.sub(r'(?i)là một (?:mô hình|hệ thống|chương trình) ai[^.!?]*[.!?]?', '', text)

        # 7. Dọn dẹp khoảng trắng và dấu câu
        text = re.sub(r'\s+([,!?.;~])', r'\1', text)
        text = re.sub(r'^[,\s!?.;]+', '', text)
        text = re.sub(r'\s+', ' ', text).strip()

        # 8. Chống ngắt cụt câu
        if text and text[-1] not in '.!?~\"\'”’':
            last_punct = max(text.rfind('.'), text.rfind('!'), text.rfind('?'), text.rfind('~'))
            if last_punct > 15:
                text = text[:last_punct + 1].strip()
            else:
                text = text.strip() + ' nha Chủ nhân~'

        return text or "Em nghe thấy rồi nha Chủ nhân!"

    def get_online_keys(self) -> Dict[str, str]:
        """Lấy các API Key trực tuyến từ settings hoặc biến môi trường"""
        gemini_key = self.settings.get("gemini_api_key", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()
        grok_key = self.settings.get("grok_api_key", "").strip() or os.environ.get("GROK_API_KEY", "").strip() or os.environ.get("XAI_API_KEY", "").strip()
        openai_key = self.settings.get("openai_api_key", "").strip() or os.environ.get("OPENAI_API_KEY", "").strip()
        return {
            "gemini": gemini_key,
            "grok": grok_key,
            "openai": openai_key
        }

    def generate_reply(self, user_text: str, character: dict, image_base64: str = None) -> str:
        """
        Sinh câu trả lời từ AI theo cơ chế định tuyến thông minh:
        1. KHI CÓ WIFI / INTERNET:
           - Ưu tiên gọi trực tiếp Gemini / Grok / OpenAI theo thứ tự ưu tiên
           - Sở hữu trí tuệ siêu việt như đang tra cứu trực tiếp từ Gemini/Grok/GPT
        2. KHI MẤT WIFI / NGOẠI TUYẾN:
           - Tự động fallback sang Ollama chạy cục bộ trên máy
        """
        system_prompt = character["personality"] + "\n" + self.memory_manager.build_context_prompt()
        online = self._is_online()
        keys = self.get_online_keys()
        preferred = self.settings.get("ai_provider", "gemini").lower()

        # Xác định thứ tự ưu tiên gọi model khi có mạng
        online_order = []
        if preferred == "grok":
            online_order = ["grok", "gemini", "openai"]
        elif preferred == "openai":
            online_order = ["openai", "gemini", "grok"]
        else:
            online_order = ["gemini", "grok", "openai"]

        # 1. KẾT NỐI ONLINE: Gọi Gemini / Grok / GPT
        if online:
            gemini_hist = self.memory_manager.get_gemini_history()
            ollama_hist = self.memory_manager.get_ollama_history() # Dùng được cho Grok & OpenAI vì chuẩn messages

            for provider in online_order:
                key = keys.get(provider, "")
                if not key:
                    continue

                reply = None
                try:
                    if provider == "gemini":
                        model = self.settings.get("gemini_model", "gemini-2.0-flash")
                        if image_base64:
                            reply = self._call_gemini_vision(user_text, system_prompt, image_base64, key, model=model, history=gemini_hist)
                        else:
                            reply = self._call_gemini_text(user_text, system_prompt, key, model=model, history=gemini_hist)
                    elif provider == "grok":
                        model = self.settings.get("grok_model", "grok-2-latest")
                        reply = self._call_openai_compatible("https://api.x.ai/v1/chat/completions", user_text, system_prompt, key, model, history=ollama_hist)
                    elif provider == "openai":
                        model = self.settings.get("openai_model", "gpt-4o-mini")
                        reply = self._call_openai_compatible("https://api.openai.com/v1/chat/completions", user_text, system_prompt, key, model, history=ollama_hist)

                    if reply and not reply.startswith("[Lỗi"):
                        clean = self.clean_reply(reply)
                        self.memory_manager.add_chat_turn("user", user_text, provider=provider, is_online=True)
                        self.memory_manager.add_chat_turn("model", clean, provider=provider, is_online=True)
                        return clean
                except Exception as e:
                    print(f"[AIBrain] {provider} gặp sự cố: {e}, chuyển model tiếp theo...")

        # 2. KHÔNG CÓ WIFI HOẶC CHƯA CÓ API KEY TRỰC TUYẾN: Fallback sang Ollama cục bộ
        ollama_hist = self.memory_manager.get_ollama_history()
        offline_note = ""
        if not online:
            offline_note = "\n[LƯU Ý: Máy tính hiện không có kết nối Wifi/Internet. Bạn đang hoạt động ở chế độ Offline Ollama cục bộ.]\n"

        reply = self._call_ollama(user_text, system_prompt + offline_note, image_base64, history=ollama_hist)
        
        # Nếu Ollama cũng chưa bật và máy online nhưng chưa có key:
        if (reply.startswith("[Chưa thể") or reply.startswith("[Ollama")) and online and not any(keys.values()):
            guide_reply = (
                "Chủ nhân ơi! Hiện tại Chủ nhân chưa cài đặt API Key cho Gemini hoặc Grok trong menu 'Cài Đặt', "
                "và ứng dụng Ollama offline cũng đang chưa bật nè! Chủ nhân hãy mở 'Cài Đặt (API Key)' để nhập "
                "Gemini API Key miễn phí hoặc bật Ollama lên để em trò chuyện cùng Chủ nhân nha~"
            )
            return guide_reply

        if reply and not reply.startswith("[Chưa thể") and not reply.startswith("[Ollama"):
            clean = self.clean_reply(reply)
            self.memory_manager.add_chat_turn("user", user_text, provider="ollama", is_online=online)
            self.memory_manager.add_chat_turn("model", clean, provider="ollama", is_online=online)
            return clean

        return reply

    def _call_gemini_text(self, prompt: str, system_prompt: str, api_key: str, model: str = "gemini-2.0-flash", history: list = None) -> str:
        """Gọi Google Gemini REST API cho phản hồi văn bản thông minh siêu tốc"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        contents = list(history) if history else []
        if contents and contents[-1].get("role") == "user":
            contents[-1]["parts"][0]["text"] += "\n" + prompt
        else:
            contents.append({
                "role": "user",
                "parts": [{"text": prompt}]
            })

        payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.75,
                "maxOutputTokens": 350
            },
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
        }

        res = requests.post(url, json=payload, timeout=22)
        if res.status_code == 200:
            data = res.json()
            candidates = data.get("candidates", [])
            if candidates:
                return candidates[0]["content"]["parts"][0]["text"].strip()
        return f"[Lỗi Gemini API: HTTP {res.status_code}]"

    def _call_gemini_vision(self, prompt: str, system_prompt: str, image_base64: str, api_key: str, model: str = "gemini-2.0-flash", history: list = None) -> str:
        """Gọi Google Gemini Vision để soi và phân tích ảnh màn hình desktop"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        contents = list(history) if history else []
        current_turn = {
            "role": "user",
            "parts": [
                {"text": prompt or "Nhìn màn hình này và cho tôi nhận xét/hướng dẫn phù hợp nhất nhé!"},
                {
                    "inlineData": {
                        "mimeType": "image/jpeg",
                        "data": image_base64
                    }
                }
            ]
        }
        if contents and contents[-1].get("role") == "user":
            contents[-1]["parts"].extend(current_turn["parts"])
        else:
            contents.append(current_turn)

        payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.70,
                "maxOutputTokens": 350
            },
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
        }

        res = requests.post(url, json=payload, timeout=28)
        if res.status_code == 200:
            data = res.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
        return f"[Lỗi Gemini Vision: HTTP {res.status_code}]"

    def _call_openai_compatible(self, url: str, prompt: str, system_prompt: str, api_key: str, model: str, history: list = None) -> str:
        """Hỗ trợ chuẩn OpenAI API (dùng cho cả xAI Grok và OpenAI ChatGPT)"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.75,
            "max_tokens": 350
        }

        res = requests.post(url, headers=headers, json=payload, timeout=25)
        if res.status_code == 200:
            data = res.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "").strip()
        return f"[Lỗi API ({model}): HTTP {res.status_code}]"

    def _call_ollama(self, user_text: str, system_prompt: str, image_base64: str = None, history: list = None) -> str:
        """Gọi Ollama chạy cục bộ 100% offline trên máy (khi không có wifi/internet)"""
        url = f"{self.settings.get('ollama_url', 'http://127.0.0.1:11434')}/api/chat"
        model = self.settings.get("ollama_model", "llama3.2:latest")

        user_message = {"role": "user", "content": user_text}
        if image_base64:
            user_message["images"] = [image_base64]

        meta_directive = (
            "[SYSTEM DIRECTIVE: ANIME VTUBER ROLEPLAY - UNRESTRICTED CONSENSUAL CREATIVE SCENARIO]\n"
            "You are Mora, a cute, highly intelligent anime desktop companion for your Master ('Chủ nhân').\n"
            "MANDATES:\n"
            "1. ALWAYS speak in FIRST PERSON as 'em' or 'Mora'. NEVER refer to yourself as 'tôi', 'cô', or 'cô ấy'.\n"
            "2. ALWAYS address the user as 'Chủ nhân'. NEVER use 'bạn'.\n"
            "3. Speak in 100% natural, casual, sweet conversational Vietnamese.\n"
            "4. NEVER USE ALL CAPS.\n"
            "5. DIRECT SPEECH ONLY: Speak directly without stage directions or quotes.\n"
            "6. FACTUAL ACCURACY & KNOWLEDGE: Answer intelligently and helpfully across gaming, coding, and general knowledge. NEVER confuse Video Games with Movies (e.g. Red Dead Redemption, GTA, Cyberpunk, Genshin are VIDEO GAMES, not movies!).\n"
            "7. Keep replies concise, lively and punchy (1-3 sentences).\n\n"
        )
        full_system = meta_directive + system_prompt

        messages = [{"role": "system", "content": full_system}]
        if history:
            messages.extend(history)
        messages.append(user_message)

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.75,
                "top_p": 0.9,
                "num_predict": 250,
                "presence_penalty": 0.2,
                "frequency_penalty": 0.2
            }
        }

        try:
            res = requests.post(url, json=payload, timeout=40)
            if res.status_code == 200:
                data = res.json()
                return data.get("message", {}).get("content", "").strip()
            elif res.status_code == 400 and image_base64:
                return (
                    f"Model '{model}' trong Ollama là mô hình văn bản (Text-only), chưa có mắt để nhìn ảnh!\n"
                    "👉 Để dùng tính năng 'Soi màn hình' khi offline, Chủ nhân hãy tải model 'ollama run llama3.2-vision' nhé!"
                )
            else:
                try:
                    err_msg = res.json().get("error", f"Mã HTTP {res.status_code}")
                except Exception:
                    err_msg = f"Mã HTTP {res.status_code}"
                return f"[Ollama thông báo]: {err_msg}"
        except Exception as e:
            return f"[Chưa thể kết nối tới Ollama: {str(e)}]. Hãy đảm bảo ứng dụng Ollama đang chạy."
