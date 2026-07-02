import sqlite3
from parsing import extract_question_blocks, extract_response_blocks
import config

import logging
logger = logging.getLogger(__name__)


#error handlers

def critical_handler(func):
    def wrapper(self, *args, **kwargs):
        try:
            result = func(self, *args, **kwargs)
            return result
        except Exception:
            logger.critical("Database operation failed in %s.", func.__name__, exc_info=True)
            if config.TEST_MODE:
                raise
            print("Exiting.")
            exit()
    return wrapper

def error_handler(func):
    def wrapper(self, *args, **kwargs):
        try:
            result = func(self, *args, **kwargs)
            return result
        except Exception:
            logger.error("Database operation failed in %s.", func.__name__, exc_info=True)
    return wrapper

class Database:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    #insert functions

    @critical_handler
    def insert_session(self, question_category: str, question_type: str, difficulty: int, today: str) -> int:
        
        question_type = question_type.split(".")[1].strip()
        
        self.cursor.execute("""
            INSERT INTO sessions (question_category, question_type, difficulty, date)
            VALUES (?, ?, ?, ?)
        """, (question_category, question_type, difficulty, today))

        self.conn.commit()
        session_id = self.cursor.lastrowid

        return session_id

    @critical_handler
    def insert_questions(self, text: str, session_id: int) -> None:
        question_number = 0
        question_blocks = extract_question_blocks(text)
        for block in question_blocks:
            question_number += 1
            question_topic = block["topic"]
            question_text = block["question"]
            self.cursor.execute("""
                INSERT INTO questions (session_id, question_number, question_topic, question_text)
                VALUES (?, ?, ?, ?)
            """, (session_id, question_number, question_topic, question_text))

        self.conn.commit()

    @critical_handler
    def insert_responses(self, text: str, session_id: int) -> None:
        response_blocks= extract_response_blocks(text)

        question_ids = []

        self.cursor.execute("""
            SELECT id FROM questions           
            WHERE session_id = ?            
            ORDER BY question_number           
        """, (session_id,))
        
        for row in self.cursor.fetchall():
            question_ids.append(row[0])

        for block, question_id in zip(response_blocks, question_ids):
            answer = block["answer"]
            grade = block["grade"]
            explanation = block["explanation"]
            self.cursor.execute("""
                INSERT INTO responses (question_id, answer, grade, explanation)
                VALUES (?, ?, ?, ?)
            """, (question_id, answer, grade, explanation))
        
        self.conn.commit()

    @critical_handler
    def insert_subjects(self, text: list[str], session_id: int) -> None:
        for item in text:
            self.cursor.execute("""
                INSERT INTO session_subjects (session_id, subject)
                VALUES (?, ?)
            """, (session_id, item))

        self.conn.commit()

    @error_handler
    def insert_favorites(self, question_id: int, date: str, note: str) -> str | None:
        self.cursor.execute("""
            INSERT INTO favorites (question_id, date_added, note)
            VALUES (?, ?, ?)
        """, (question_id, date, note))
        
        self.conn.commit()

        return "success"

    #check info

    @error_handler
    def check_favorite(self, question_id: int) -> bool | None:
        self.cursor.execute("""
                SELECT COUNT(*) FROM favorites
                WHERE question_id = ?
        """, (question_id,))
        
        return self.cursor.fetchone()[0] > 0

    #fetching functions

    @critical_handler
    def fetch_favorites(self) -> list[tuple]:
        self.cursor.execute("""
            SELECT question_id, date_added, note
            FROM favorites
            ORDER BY question_id
        """)

        return self.cursor.fetchall()

    @critical_handler
    def fetch_questions_for_favorites(self, question_ids: list[int]) -> list[tuple]:
        if isinstance(question_ids, int):
            question_ids = (question_ids,)
            placeholders = "?"
        else:
            placeholders = ",".join("?" * len(question_ids))
            question_ids = tuple(question_ids)

        self.cursor.execute(f"""
                SELECT question_text
                FROM questions
                WHERE id IN ({placeholders})
                ORDER BY id
        """, (question_ids))

        return self.cursor.fetchall()

    @critical_handler
    def fetch_topic_grades(self) -> list[tuple]:
        self.cursor.execute("""
            SELECT sessions.date, questions.question_topic, responses.grade
            FROM sessions
            JOIN questions ON sessions.id = questions.session_id
            JOIN responses ON questions.id = responses.question_id
            ORDER BY sessions.date 
        """)

        return self.cursor.fetchall()

    @error_handler
    def fetch_weak_topics(self, subject: str) -> list[tuple] | None:
        self.cursor.execute("""
            SELECT questions.question_topic, responses.grade
            FROM sessions                                 
            JOIN questions ON sessions.id = questions.session_id
            JOIN responses ON questions.id = responses.question_id
            JOIN session_subjects on sessions.id = session_subjects.session_id
            WHERE session_subjects.subject = ?
        """, (subject,))
                            
        return self.cursor.fetchall()

    @error_handler
    def check_graded(self, session_id: str) -> int | None:
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM responses
            JOIN questions ON questions.id = responses.question_id
            WHERE questions.session_id = ?
        """, (session_id,))

        return self.cursor.fetchone()[0]

    @critical_handler
    def fetch_sessions(self) -> list[tuple]:
        self.cursor.execute("""
            SELECT sessions.question_type, sessions.difficulty, sessions.date, sessions.id
            FROM sessions                   
            ORDER BY sessions.date
        """)
        
        return self.cursor.fetchall()

    @critical_handler
    def fetch_subjects(self, session_id: int) -> list[tuple]:
        self.cursor.execute("""
            SELECT session_subjects.subject
            FROM session_subjects
            WHERE session_subjects.session_id = ?
        """, (session_id,))
        
        return self.cursor.fetchall()

    @critical_handler
    def fetch_session_scores(self, session_id: int) -> list[tuple]:
        self.cursor.execute("""
            SELECT questions.question_number, responses.grade
            FROM questions
            JOIN responses ON questions.id = responses.question_id
            WHERE questions.session_id = ?
        """, (session_id,))

        return self.cursor.fetchall()

    @critical_handler
    def fetch_session_category(self, session_id: int) -> list[tuple]:
        self.cursor.execute("""
            SELECT sessions.question_category
            FROM sessions
            WHERE sessions.id = ?
        """, (session_id,))

        return self.cursor.fetchone()

    @critical_handler
    def fetch_questions(self, session_id: int) -> list[tuple]:
        self.cursor.execute("""
            SELECT questions.id, questions.question_number, questions.question_topic, questions.question_text
            FROM questions  
            WHERE questions.session_id = ?
            ORDER BY question_number
        """, (session_id,))

        return self.cursor.fetchall()

    @critical_handler
    def fetch_responses(self, question_ids: list[int]) -> list[tuple]:
        placeholders = ",".join("?" * len(question_ids))

        self.cursor.execute(f"""
                SELECT responses.answer, responses.grade, responses.explanation
                FROM responses
                WHERE responses.question_id IN ({placeholders})
                ORDER BY responses.question_id
        """, tuple(question_ids))

        return self.cursor.fetchall()

    #update info

    @error_handler
    def update_favorite_note(self, new_note: str, question_id: int) -> str | None:
        self.cursor.execute(f"""
                UPDATE favorites
                SET note = ?
                WHERE question_id = ?
        """, (new_note, question_id))

        return "success"

    #remove

    @error_handler
    def delete_favorite(self, question_id: int) -> str | None:
        self.cursor.execute(f"""
                DELETE FROM favorites
                WHERE question_id = ?
        """, (question_id,))

        return "success"

    #initialization function

    @critical_handler
    def initiate_db(self) -> None:

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY,
                question_category TEXT,
                question_type TEXT,
                difficulty INTEGER,
                date TEXT
            );
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY,
                session_id INTEGER,
                question_number INTEGER,
                question_topic TEXT,
                question_text TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY,
                question_id INTEGER,
                answer TEXT,
                grade TEXT,
                explanation TEXT,
                FOREIGN KEY (question_id) REFERENCES questions(id)
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_subjects (
            id INTEGER PRIMARY KEY,
            session_id INTEGER,
            subject TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
            );
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY,
            question_id INTEGER,
            date_added TEXT,
            note TEXT,
            FOREIGN KEY (question_id) REFERENCES questions(id)
            );                     
        """)