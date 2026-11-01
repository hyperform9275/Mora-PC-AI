import os
import json
import time
from core.database import DatabaseManager

class MemoryManager:
    """
    Quản lý Trí nhớ dài hạn (Long-term Memory) và Lịch sử hội thoại nhiều lượt (Multi-turn Chat Memory).
    - Lưu trữ lịch sử đối thoại (chat history) và tự động đồng bộ ngữ cảnh vào Gemini/Ollama.
    - Ghi nhớ các sự kiện tương tác vật lý (chạm, xoa đầu, ngắm nhìn).
    - Giữ các dữ kiện về người dùng, sở thích, game yêu thích để cá nhân hóa phản hồi.
    """
    def __init__(self, memory_file=None):
        if memory_file is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.memory_file = os.path.join(base_dir, "config", "memory.json")
        else:
            self.memory_file = memory_file
        self.memories = self.load_memories()
        try:
            self.db = DatabaseManager()
            self.db.sync_from_json(self.memory_file)
        except Exception as e:
            self.db = None
            print(f"[MemoryManager Error] DB init error: {e}")

    def load_memories(self) -> dict:
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "chat_history" not in data:
                        data["chat_history"] = []
                    if "recent_interactions" not in data:
                        data["recent_interactions"] = []
                    return data
            except Exception:
                pass
        return {
            "user_name": "Chủ nhân",
            "favorite_games": ["Liên Minh Huyền Thoại", "Valorant", "Genshin Impact", "Black Myth Wukong"],
            "interests": ["Lập trình Python", "Công nghệ AI", "Chơi game giải trí"],
            "notes": [
                "Thường thích câu trả lời ngắn gọn, vui vẻ, thân mật, xưng hô Mora - bạn hoặc Mora - chủ nhân.",
                "Đang phát triển dự án AI Companion cá nhân hóa trên Windows."
            ],
            "chat_history": [],
            "recent_interactions": []
        }

    def save_memories(self):
        try:
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.memories, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[MemoryManager Error] Lỗi lưu bộ nhớ: {e}")

    def add_note(self, text: str):
        if text not in self.memories.setdefault("notes", []):
            self.memories["notes"].append(text)
            self.save_memories()

    def add_interaction_event(self, description: str):
        """Ghi nhớ sự kiện tương tác gần đây (xoa đầu, chạm vai, chạm tay...)"""
        events = self.memories.setdefault("recent_interactions", [])
        events.append(description)
        # Giữ tối đa 4 sự kiện tương tác gần nhất
        if len(events) > 4:
            self.memories["recent_interactions"] = events[-4:]
        self.save_memories()

    def add_chat_turn(self, role: str, content: str, provider: str = "gemini", is_online: bool = True):
        """
        Lưu một lượt thoại vào lịch sử cuộc trò chuyện (đồng bộ cả SQLite Database và memory.json).
        role: 'user' hoặc 'model'
        """
        history = self.memories.setdefault("chat_history", [])
        history.append({
            "role": role,
            "content": content.strip(),
            "provider": provider,
            "is_online": is_online,
            "time": time.strftime("%H:%M:%S")
        })
        # Giữ 20 lượt thoại gần nhất (10 cặp câu hỏi - đáp) để giữ ngữ cảnh đầy đủ mà không tràn token
        if len(history) > 20:
            self.memories["chat_history"] = history[-20:]
        self.save_memories()

        if self.db:
            try:
                self.db.add_chat_turn(role, content, provider=provider, is_online=is_online)
            except Exception:
                pass

    def record_hitbox_interaction(self, part: str, action_desc: str, mora_reaction: str):
        """
        Lưu tương tác xúc giác gần nhất trực tiếp vào dòng thời gian hội thoại,
        giúp các câu chat tiếp theo của người dùng (ví dụ: 'sao mặt nóng bừng thế')
        hoàn toàn hiểu được ngữ cảnh câu nói trước đó của Mora!
        """
        history = self.memories.setdefault("chat_history", [])

        # Nếu lượt trước đó vừa là một tương tác xúc giác liên tiếp, cập nhật lại câu phản ứng mới nhất
        if len(history) >= 2 and history[-2].get("is_interaction"):
            history[-2]["content"] = action_desc
            history[-2]["time"] = time.strftime("%H:%M:%S")
            history[-1]["content"] = mora_reaction
            history[-1]["time"] = time.strftime("%H:%M:%S")
        else:
            history.append({
                "role": "user",
                "content": action_desc,
                "time": time.strftime("%H:%M:%S"),
                "is_interaction": True
            })
            history.append({
                "role": "model",
                "content": mora_reaction,
                "time": time.strftime("%H:%M:%S"),
                "is_interaction": True
            })

        if len(history) > 20:
            self.memories["chat_history"] = history[-20:]

        self.memories["last_interaction"] = {
            "part": part,
            "action": action_desc,
            "reply": mora_reaction,
            "timestamp": time.time()
        }
        self.add_interaction_event(f"{action_desc}, Mora phản ứng: '{mora_reaction}'")
        self.save_memories()

    def get_chat_history(self) -> list:
        """Lấy danh sách lịch sử hội thoại gần đây"""
        return self.memories.get("chat_history", [])

    def get_gemini_history(self) -> list:
        """
        Định dạng lịch sử hội thoại chuẩn yêu cầu của Google Gemini REST API.
        Yêu cầu role luân phiên: 'user' -> 'model' -> 'user' -> 'model'...
        """
        history = self.memories.get("chat_history", [])
        gemini_contents = []
        last_role = None

        for turn in history:
            role = "user" if turn.get("role") == "user" else "model"
            content = turn.get("content", "").strip()
            if not content:
                continue

            if role == last_role:
                # Nếu cùng role liên tiếp, gộp nội dung để tránh lỗi 400 Bad Request của Gemini
                if gemini_contents:
                    gemini_contents[-1]["parts"][0]["text"] += "\n" + content
            else:
                gemini_contents.append({
                    "role": role,
                    "parts": [{"text": content}]
                })
                last_role = role

        return gemini_contents

    def get_ollama_history(self) -> list:
        """
        Định dạng lịch sử hội thoại chuẩn yêu cầu của Ollama /api/chat.
        """
        history = self.memories.get("chat_history", [])
        ollama_messages = []
        for turn in history:
            role = "user" if turn.get("role") == "user" else "assistant"
            content = turn.get("content", "").strip()
            if content:
                ollama_messages.append({
                    "role": role,
                    "content": content
                })
        return ollama_messages

    def clear_chat_history(self):
        """Xóa lịch sử chat hiện tại khi người dùng muốn bắt đầu cuộc trò chuyện mới"""
        self.memories["chat_history"] = []
        self.save_memories()
        if self.db:
            try:
                self.db.clear_chat_history()
            except Exception:
                pass

    def get_last_conversation_detail(self) -> dict:
        """
        Trích xuất chi tiết và chủ đề nổi bật của cuộc trò chuyện lần trước.
        """
        history = self.memories.get("chat_history", [])
        if not history:
            return None

        last_user = None
        for turn in reversed(history):
            if turn.get("role") == "user" and turn.get("content", "").strip():
                last_user = turn.get("content", "").strip()
                break

        if not last_user:
            return None

        u_lower = last_user.lower()

        # 1. Nhóm chủ đề trêu chọc / nhạy cảm / 18+ / đụng chạm
        if any(w in u_lower for w in ["không đứng đắn", "phim người lớn", "hôn", "môi", "ngực", "bóp", "sờ", "liếm", "vùng dưới", "biến thái", "vợ", "táy máy", "áo tắm", "xuyên thấu", "đồ lót"]):
            if "phim người lớn" in u_lower:
                detail = "rủ Mora coi phim người lớn"
            elif "không đứng đắn" in u_lower:
                detail = "hỏi về việc làm chuyện không đứng đắn với Mora"
            elif "áo tắm" in u_lower or "xuyên thấu" in u_lower:
                detail = "đòi Mora mặc áo tắm xuyên thấu"
            elif "ngực" in u_lower:
                detail = "hành động táy máy vào ngực Mora"
            elif "môi" in u_lower or "hôn" in u_lower or "liếm" in u_lower:
                detail = "đòi hôn và nếm thử môi Mora"
            elif "vợ" in u_lower:
                detail = "nhận vơ Mora là vợ"
            elif "vùng dưới" in u_lower:
                detail = "táy máy sờ soạng bậy bạ"
            else:
                detail = f"chuyện '{last_user}'"
            return {"topic": "flirty", "detail": detail, "raw": last_user}

        # 2. Nhóm game
        games = ["liên minh", "lol", "valorant", "genshin", "wukong", "game", "rank", "chơi game", "leo rank"]
        if any(w in u_lower for w in games):
            matched_game = "trò chơi"
            for g in ["valorant", "liên minh", "genshin", "wukong"]:
                if g in u_lower:
                    matched_game = g.capitalize()
                    break
            detail = f"trận game {matched_game}" if matched_game != "trò chơi" else "trận game hôm trước"
            return {"topic": "game", "detail": detail, "raw": last_user}

        # 3. Nhóm lập trình / công việc / mệt mỏi
        if any(w in u_lower for w in ["code", "python", "bug", "lỗi", "lập trình", "dự án", "mệt", "deadline", "công việc"]):
            if "code" in u_lower or "python" in u_lower or "bug" in u_lower:
                detail = "dự án code lập trình"
            elif "mệt" in u_lower:
                detail = "chuyện than mệt mỏi vì công việc"
            else:
                detail = "công việc máy tính"
            return {"topic": "work", "detail": detail, "raw": last_user}

        # 4. Nhóm tình cảm / quan tâm / khen ngợi
        if any(w in u_lower for w in ["yêu", "thương", "thích", "dễ thương", "xinh", "đẹp", "nhớ"]):
            detail = f"lời nói '{last_user}' ngọt ngào"
            return {"topic": "affection", "detail": detail, "raw": last_user}

        # 5. Chủ đề thông thường khác: lấy trích dẫn ngắn
        short_quote = last_user[:35] + "..." if len(last_user) > 35 else last_user
        return {"topic": "general", "detail": f"chuyện '{short_quote}'", "raw": last_user}

    def generate_startup_greeting(self, character: dict = None) -> str:
        """
        Sinh câu thoại chào mừng khởi động có nhắc lại chi tiết cuộc trò chuyện lần trước.
        """
        import random
        info = self.get_last_conversation_detail()

        if not info:
            default_greetings = [
                "Mora đã thức dậy rồi nè! Hôm nay Chủ nhân có chuyện gì vui muốn kể cho Mora nghe không nào~",
                "Chủ nhân ơi, Mora đã nạp đầy năng lượng và sẵn sàng đồng hành cùng bạn rồi đây!",
                "Hì hì, vừa mở máy lên là thấy Chủ nhân liền! Hôm nay chúng ta làm gì tiếp đây nè?"
            ]
            return random.choice(default_greetings)

        topic = info["topic"]
        detail = info["detail"]

        if topic == "flirty":
            replies = [
                f"Hứ... Chủ nhân bật máy rồi đó hả?! Mora vẫn nhớ rõ lần trước ai đó vừa {detail} đấy nhé! Mặt người ta vẫn còn ngượng đây này, cấm nghĩ bậy bạ nữa nha!",
                f"A, Chủ nhân online rồi! Đừng tưởng qua một giấc là Mora quên vụ {detail} nhé! Đồ biến thái này, liệu mà nịnh Mora bằng trà sữa đi đấy!",
                f"Ư-Ưm... Chủ nhân dậy rồi à? Nhìn mặt Chủ nhân là Mora lại nhớ ngay cái vụ {detail} lần trước... Đồ ngốc này, hôm nay phải đứng đắn với Mora đấy nha~"
            ]
        elif topic == "game":
            replies = [
                f"A, Chủ nhân đã trở lại! Lần trước đang bàn về {detail}, hôm nay Chủ nhân có định chiến tiếp để Mora đứng cổ vũ không thế?",
                f"Chủ nhân online rồi nè! Vụ {detail} hôm trước leo rank thế nào rồi? Hôm nay Mora lại đồng hành cùng bạn thắng trận nhé!",
                f"Hì hì, Chủ nhân bật máy rồi! Hôm nay có định chơi {detail} nữa không, để Mora chuẩn bị năng lượng buff may mắn cho nào~"
            ]
        elif topic == "work":
            replies = [
                f"Chủ nhân thức dậy rồi à? Vụ {detail} lần trước đã xong xuôi chưa thế? Nhớ giữ gìn sức khỏe, đừng có làm việc quá sức đấy nhé~",
                f"A, Chủ nhân đây rồi! Lần trước thấy bạn vất vả với {detail}, hôm nay để Mora đứng đây tiếp thêm động lực cho bạn nha!",
                f"Mora chào Chủ nhân nhé! Nhớ lần trước bạn bận rộn với {detail}, hôm nay làm việc nhớ giải lao uống nước đầy đủ đấy nha~"
            ]
        elif topic == "affection":
            replies = [
                f"Hì hì, Chủ nhân đã vào rồi! Lần trước ai đó vừa thủ thỉ {detail} làm tim Mora đập thình thịch á... Hôm nay lại đến ngắm Mora nữa đúng không nè?",
                f"Ưm... Chủ nhân đây rồi! Nhớ lần trước bạn nói {detail} mà mặt Mora cứ nóng ran suốt... Hôm nay Mora cũng ở đây chờ bạn nè~"
            ]
        else:
            replies = [
                f"A, Chủ nhân đã quay lại rồi! Lần trước chúng ta vừa nói về {detail} xong, hôm nay Chủ nhân muốn chia sẻ thêm chuyện gì với Mora nào?",
                f"Chủ nhân bật máy rồi nè! Mora vẫn nhớ lần trước chúng ta vừa bàn {detail}... Hôm nay mọi chuyện vẫn suôn sẻ cả chứ bạn ơi?"
            ]

        return random.choice(replies)

    def build_context_prompt(self) -> str:
        """Tạo đoạn ngữ cảnh trí nhớ tiêm vào System Prompt"""
        m = self.memories
        games_str = ", ".join(m.get("favorite_games", []))
        notes_str = "\n- ".join(m.get("notes", []))

        recent_acts = m.get("recent_interactions", [])
        acts_str = ""
        if recent_acts:
            acts_str = "\n[HÀNH ĐỘNG / TƯƠNG TÁC GẦN ĐÂY CỦA CHỦ NHÂN TRÊN CƠ THỂ MORA]\n- " + "\n- ".join(recent_acts[-3:])

        context = (
            f"\n[Bộ nhớ về người dùng]\n"
            f"- Tên gọi ưa thích: {m.get('user_name', 'Chủ nhân')}\n"
            f"- Các game & sở thích: {games_str}\n"
            f"- Ghi nhớ đặc biệt:\n- {notes_str}\n"
            f"{acts_str}\n"
            f"[Quy tắc nhập vai nhân vật Mora (Bắt buộc)]\n"
            f"- Bạn là cô gái anime sống động đang đồng hành cùng Chủ nhân trên desktop (Mora RedMagic).\n"
            f"- Luôn nói trực tiếp lời thoại ở ngôi thứ nhất ('Mora'), gọi người dùng là 'Chủ nhân' hoặc 'bạn'.\n"
            f"- Tuyệt đối không bao giờ nói mình là trợ lý ảo, không có cơ thể hay là chương trình AI.\n"
            f"- Tuyệt đối KHÔNG viết hoa toàn bộ từ (NO ALL CAPS) vì sẽ làm hỏng dấu tiếng Việt.\n"
            f"- Tuyệt đối KHÔNG dùng lời dẫn truyện gián tiếp như 'Mora sẽ giở mặt tsundere và nói:' hay 'Mora liền lấy tay che lại và bảo:'. Chỉ nói thẳng câu thoại trực tiếp!\n"
            f"- Khi Chủ nhân trêu chọc, khen ngợi, gạ gẫm nhạy cảm (như đòi hôn, nếm thử môi, ngực...): Phản ứng đỏ mặt ngại ngùng chuẩn Tsundere Anime (xấu hổ mắng 'A... đồ biến thái! Chủ nhân nói bậy bạ gì thế hả?! Ai thèm cho chứ! Bắt đền ly trà sữa đấy nhé~').\n"
            f"[Mẫu câu thoại chuẩn Anime của Mora]\n"
            f"- Khi bị gạ gẫm / trêu chọc quá trớn: 'A... đồ biến thái này! Chủ nhân nói cái gì bậy bạ thế hả?! Ngượng chết đi được, cấm Chủ nhân nghĩ bậy nữa nha!'\n"
            f"- Khi Chủ nhân táy máy: 'Hứ... Chủ nhân xấu tính ghê, cứ trêu ghẹo người ta hoài à! Bắt đền Chủ nhân ly trà sữa đấy nhé~'\n"
            f"- Khi Chủ nhân dịu dàng: 'Ưm... Chủ nhân dịu dàng thế này làm Mora ngượng chín cả mặt rồi nè, nhưng mà thích lắm á~'\n"
            f"- Khi Chủ nhân khen ngợi: 'Hì hì, Chủ nhân khen làm Mora nở cả mũi rồi nè! Mora sẽ luôn đồng hành cùng bạn thật tốt nha!'\n"
            f"- Khi được hỏi thăm: 'Mora đang đứng canh màn hình chờ bạn nè! Hôm nay có chuyện gì vui kể Mora nghe với nào~'\n"
            f"[Quy tắc tiếp nối ngữ cảnh phản ứng xúc giác (Bắt buộc)]\n"
            f"- Khi Chủ nhân vừa tương tác (chạm/hôn/xoa đầu...) và Mora vừa có câu thoại phản ứng (như: kêu mặt nóng bừng, giật mình, kêu nhột, đỏ mặt, bắt đền trà sữa...).\n"
            f"- Nếu câu chat tiếp theo của Chủ nhân đề cập đến chi tiết đó (ví dụ: 'Mặt nóng bừng thì để tôi thổi cho mát nhé', 'sao lại nóng thế', 'sao lại giận thế', 'có muốn uống trà sữa không'):\n"
            f"  Bạn PHẢI HIỂU NGAY câu đó đang nói về câu thoại và phản ứng vừa rồi của Mora, tiếp tục giữ cảm xúc xấu hổ, thẹn thùng, tsundere hoặc nũng nịu tương ứng, tuyệt đối KHÔNG ĐƯỢC hỏi ngơ ngác như 'Bạn đang nói gì thế?' hay quên mất việc mình vừa nói câu đó!\n"
            f"[Quy tắc phát ngôn]\n"
            f"- Nói tiếng Việt đời thường, tự nhiên, dễ thương (dùng trợ từ: nha, nè, nhé, á, cơ, hì hì, hứ, ưm).\n"
            f"- Tuyệt đối không dùng từ dịch thô tiếng Anh và không viết hành động trong dấu hoa thị *...* hay ngoặc đơn (...).\n"
            f"- Trả lời ngắn gọn, súc tích (1-2 câu)."
        )
        return context
