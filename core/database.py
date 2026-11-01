# -*- coding: utf-8 -*-
"""
Database Manager for Mora PC AI
Provides robust, persistent SQLite database storage for:
- Full conversation history (multi-turn chat logs with provider tracking)
- Knowledge memories (facts, topics, user preferences)
- Physical hitbox interactions
- Two-way sync with memory.json for human readability & backward compatibility
"""

import os
import sqlite3
import json
import time
from typing import List, Dict, Any, Optional

class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.db_path = os.path.join(base_dir, "config", "mora.db")
        else:
            self.db_path = db_path
        
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Khởi tạo cấu trúc các bảng dữ liệu trong SQLite"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Bảng lịch sử trò chuyện (Chat History)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    provider TEXT DEFAULT 'gemini',
                    is_online INTEGER DEFAULT 1,
                    timestamp REAL NOT NULL,
                    time_str TEXT NOT NULL,
                    is_interaction INTEGER DEFAULT 0
                )
            """)

            # 2. Bảng hồ sơ người dùng & ghi nhớ sở thích (User Profile & Knowledge)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profile (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # 3. Bảng tri thức & sự kiện ghi nhớ (Knowledge Memory)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    fact TEXT NOT NULL,
                    importance INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL
                )
            """)

            # 4. Bảng nhật ký tương tác xúc giác (Interactions)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    part TEXT NOT NULL,
                    action_desc TEXT NOT NULL,
                    reaction TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    time_str TEXT NOT NULL
                )
            """)

            conn.commit()

    def sync_from_json(self, json_path: str):
        """Nhập dữ liệu từ memory.json vào SQLite nếu database còn trống"""
        if not os.path.exists(json_path):
            return
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as cnt FROM chat_history")
                count = cursor.fetchone()["cnt"]
                if count > 0:
                    return # Đã có dữ liệu trong SQLite

                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Nạp thông tin người dùng
                user_name = data.get("user_name", "Chủ nhân")
                cursor.execute("INSERT OR REPLACE INTO user_profile (key, value, updated_at) VALUES (?, ?, ?)",
                               ("user_name", user_name, time.strftime("%Y-%m-%d %H:%M:%S")))
                
                games = json.dumps(data.get("favorite_games", []), ensure_ascii=False)
                cursor.execute("INSERT OR REPLACE INTO user_profile (key, value, updated_at) VALUES (?, ?, ?)",
                               ("favorite_games", games, time.strftime("%Y-%m-%d %H:%M:%S")))

                # Nạp ghi chú
                for note in data.get("notes", []):
                    cursor.execute("INSERT INTO knowledge_memory (category, topic, fact, created_at) VALUES (?, ?, ?, ?)",
                                   ("note", "general", note, time.strftime("%Y-%m-%d %H:%M:%S")))

                # Nạp lịch sử trò chuyện
                for turn in data.get("chat_history", []):
                    cursor.execute("""
                        INSERT INTO chat_history (role, content, provider, is_online, timestamp, time_str, is_interaction)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        turn.get("role", "user"),
                        turn.get("content", ""),
                        turn.get("provider", "gemini"),
                        1,
                        time.time(),
                        turn.get("time", time.strftime("%H:%M:%S")),
                        1 if turn.get("is_interaction") else 0
                    ))

                conn.commit()
                print("[DatabaseManager] Synced data from memory.json into mora.db successfully!")
        except Exception as e:
            print(f"[DatabaseManager Error] sync_from_json error: {e}")

    def add_chat_turn(self, role: str, content: str, provider: str = "gemini", is_online: bool = True, is_interaction: bool = False):
        """Lưu một lượt trò chuyện vào SQLite"""
        try:
            now = time.time()
            time_str = time.strftime("%H:%M:%S")
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO chat_history (role, content, provider, is_online, timestamp, time_str, is_interaction)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (role, content.strip(), provider, 1 if is_online else 0, now, time_str, 1 if is_interaction else 0))
                conn.commit()
        except Exception as e:
            print(f"[DatabaseManager Error] Lỗi add_chat_turn: {e}")

    def get_recent_chat(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Lấy danh sách các lượt chat gần nhất"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT role, content, provider, is_online, timestamp, time_str, is_interaction
                    FROM (
                        SELECT * FROM chat_history ORDER BY id DESC LIMIT ?
                    ) ORDER BY id ASC
                """, (limit,))
                rows = cursor.fetchall()
                return [
                    {
                        "role": r["role"],
                        "content": r["content"],
                        "provider": r["provider"],
                        "is_online": bool(r["is_online"]),
                        "time": r["time_str"],
                        "is_interaction": bool(r["is_interaction"])
                    }
                    for r in rows
                ]
        except Exception as e:
            print(f"[DatabaseManager Error] Lỗi get_recent_chat: {e}")
            return []

    def clear_chat_history(self):
        """Xóa sạch lịch sử trò chuyện khi bắt đầu phiên mới"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM chat_history")
                conn.commit()
        except Exception as e:
            print(f"[DatabaseManager Error] Lỗi clear_chat_history: {e}")

    def add_interaction(self, part: str, action_desc: str, reaction: str):
        """Lưu tương tác xúc giác vào SQLite"""
        try:
            now = time.time()
            time_str = time.strftime("%H:%M:%S")
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO interactions (part, action_desc, reaction, timestamp, time_str)
                    VALUES (?, ?, ?, ?, ?)
                """, (part, action_desc, reaction, now, time_str))
                conn.commit()
        except Exception as e:
            print(f"[DatabaseManager Error] Lỗi add_interaction: {e}")

    def add_knowledge(self, category: str, topic: str, fact: str, importance: int = 1):
        """Lưu một sự kiện hoặc tri thức vào bộ nhớ lâu dài"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO knowledge_memory (category, topic, fact, importance, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (category, topic, fact, importance, time.strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
        except Exception as e:
            print(f"[DatabaseManager Error] Lỗi add_knowledge: {e}")

    def get_all_knowledge(self) -> List[Dict[str, Any]]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT category, topic, fact, importance, created_at FROM knowledge_memory ORDER BY id DESC")
                return [dict(r) for r in cursor.fetchall()]
        except Exception as e:
            print(f"[DatabaseManager Error] Lỗi get_all_knowledge: {e}")
            return []
