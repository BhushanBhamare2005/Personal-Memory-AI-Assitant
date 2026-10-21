"""
SQLite Database Management for User Profiles and Conversations
"""
import os
import logging
import sqlite3
from typing import List, Dict, Optional, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manage SQLite database for user data"""
    
    def __init__(self, db_path: str = "data/memory.db"):
        """Initialize database manager"""
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.conn = None
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def _init_db(self):
        """Initialize database schema"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT UNIQUE,
                profile_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                user_message TEXT,
                assistant_response TEXT,
                sources TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # Memories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                content TEXT,
                memory_type TEXT,
                importance_score REAL DEFAULT 0.5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # Documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                filename TEXT,
                file_path TEXT,
                chunk_count INTEGER,
                total_pages INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # User Preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL UNIQUE,
                preferences_data TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        conn.commit()
        logger.info("Database initialized")
    
    async def add_user(
        self,
        user_id: str,
        name: str = None,
        email: str = None
    ) -> bool:
        """Add a new user"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO users (id, name, email)
                VALUES (?, ?, ?)
            """, (user_id, name, email))
            conn.commit()
            logger.info(f"User {user_id} added")
            return True
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            
            if row:
                profile = dict(row)
                if profile.get("profile_data"):
                    profile["profile_data"] = json.loads(profile["profile_data"])
                return profile
            return None
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    async def update_user_profile(
        self,
        user_id: str,
        profile_data: Dict[str, Any]
    ) -> bool:
        """Update user profile"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users
                SET profile_data = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (json.dumps(profile_data), user_id))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return False
    
    async def add_conversation(
        self,
        user_id: str,
        user_message: str,
        assistant_response: str,
        sources: List[Dict] = None
    ) -> bool:
        """Add conversation to database"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversations (user_id, user_message, assistant_response, sources)
                VALUES (?, ?, ?, ?)
            """, (
                user_id,
                user_message,
                assistant_response,
                json.dumps(sources) if sources else None
            ))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding conversation: {e}")
            return False
    
    async def get_recent_conversations(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """Get recent conversations"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM conversations
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, limit))
            
            rows = cursor.fetchall()
            conversations = []
            for row in rows:
                conv = dict(row)
                if conv.get("sources"):
                    conv["sources"] = json.loads(conv["sources"])
                conversations.append(conv)
            
            return conversations
        except Exception as e:
            logger.error(f"Error getting conversations: {e}")
            return []
    
    async def add_memory(
        self,
        user_id: str,
        content: str,
        memory_type: str = "note",
        importance_score: float = 0.5
    ) -> int:
        """Add memory for user"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO memories (user_id, content, memory_type, importance_score)
                VALUES (?, ?, ?, ?)
            """, (user_id, content, memory_type, importance_score))
            conn.commit()
            return int(cursor.lastrowid)
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            raise
    
    async def get_user_memories(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[Dict]:
        """Get user memories"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM memories
                WHERE user_id = ?
                ORDER BY importance_score DESC, created_at DESC
                LIMIT ?
            """, (user_id, limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting memories: {e}")
            return []
    
    async def add_document(
        self,
        doc_id: str,
        user_id: str,
        filename: str,
        file_path: str,
        chunk_count: int,
        total_pages: int = 0,
        metadata: Dict = None
    ) -> bool:
        """Add document to database"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO documents
                (id, user_id, filename, file_path, chunk_count, total_pages, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id,
                user_id,
                filename,
                file_path,
                chunk_count,
                total_pages,
                json.dumps(metadata) if metadata else None
            ))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False
    
    async def get_user_documents(self, user_id: str) -> List[Dict]:
        """Get user's documents"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM documents WHERE user_id = ?
            """, (user_id,))
            
            rows = cursor.fetchall()
            documents = []
            for row in rows:
                doc = dict(row)
                if doc.get("metadata"):
                    doc["metadata"] = json.loads(doc["metadata"])
                documents.append(doc)
            
            return documents
        except Exception as e:
            logger.error(f"Error getting documents: {e}")
            return []
    
    async def set_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """Set user preferences"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO preferences (user_id, preferences_data)
                VALUES (?, ?)
            """, (user_id, json.dumps(preferences)))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error setting preferences: {e}")
            return False
    
    async def get_preferences(self, user_id: str) -> Optional[Dict]:
        """Get user preferences"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT preferences_data FROM preferences WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            if row and row[0]:
                return json.loads(row[0])
            return None
        except Exception as e:
            logger.error(f"Error getting preferences: {e}")
            return None
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
