import sqlite3
from parsing import extract_question_blocks, extract_response_blocks
import config

import logging
logger = logging.getLogger(__name__)


#error handlers

def _critical_handler(func):
    """A decorator that wraps Database methods to handle critical errors that stop the normal function of SFK
    
    Args:
        func: Function that has the possibility of a critical error
    Returns:
        Wrapped function with critical error handling applied
    """
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

def _error_handler(func):
    """A decorator that wraps Database methods to handle non-critical errors that disrupt the normal function of SFK
    
    Args:
        func: Function that has the possibility of a non-critical error
    Returns:
        Wrapped function or None if an error occurs
    """
    def wrapper(self, *args, **kwargs):
        try:
            result = func(self, *args, **kwargs)
            return result
        except Exception:
            logger.error("Database operation failed in %s.", func.__name__, exc_info=True)
    return wrapper

class Database:
    """Manages all SQLite database operations for SFK
    
    Attributes:
        conn (sqlite3.Connection): Database connection
        cursor (sqlite3.Cursor): Cursor used to execute SQL statements
    """
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    #insert functions

    @_critical_handler
    def insert_session(self, question_category: str, question_type: str, question_subtype: str | None, difficulty: int, today: str) -> int:
        """Inserts a new session record
    
        Args:
            question_category: Selected question category
            question_type: Selected question type
            question_subtype: Selected subtype, or None if not applicable
            difficulty: Difficulty level for the session
            today: Timestamp for when the session was created
        Returns:
            Session id for the current session
        """

        self.cursor.execute("""
            INSERT INTO sessions (question_category, question_type, question_subtype, difficulty, date)
            VALUES (?, ?, ?, ?, ?)
        """, (question_category, question_type, question_subtype, difficulty, today))

        self.conn.commit()
        session_id = self.cursor.lastrowid

        return session_id

    @_critical_handler
    def insert_questions(self, text: str, session_id: int) -> None:
        """Insert session question data
        
        Args:
            text: Contains all the text in a generated question document
            session_id: Used to link to questions to a session
        """

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

    @_critical_handler
    def insert_responses(self, text: str, session_id: int) -> None:
        """Insert a completed session's responses, grades, and explanations
        
        Args:
            text: Contains all the text in a completed question document
            session_id: Used to link to responses to a session
        """

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

    @_critical_handler
    def insert_subjects(self, subjects: list[str], session_id: int) -> None:
        """Insert a session's subject(s)
        
        Args:
            subjects: Contains subject(s) for a given session
            session_id: Used to link to responses to a session
        """
        for subject in subjects:
            self.cursor.execute("""
                INSERT INTO session_subjects (session_id, subject)
                VALUES (?, ?)
            """, (session_id, subject))

        self.conn.commit()

    @_error_handler
    def insert_favorites(self, question_id: int, date: str, note: str | None) -> str | None:
        """Add a question to favorites
        
        Args:
            question_id: Used to link to favorite to a question
            date: Date for when the favorite was added
            note: Reason for adding favorite (optional)
        Returns:
            "success" if everything worked or None if an error occurs
        """

        self.cursor.execute("""
            INSERT INTO favorites (question_id, date_added, note)
            VALUES (?, ?, ?)
        """, (question_id, date, note))
        
        self.conn.commit()

        return "success"

    #check info

    @_error_handler
    def check_favorite(self, question_id: int) -> bool | None:
        """Check if a question is in favorites table
        
        Args:
            question_id: Used to check for favorite
        Returns:
            Count to see if favorite exists or None if an error occurs
        """
  
        self.cursor.execute("""
                SELECT COUNT(*) FROM favorites
                WHERE question_id = ?
        """, (question_id,))
        
        return self.cursor.fetchone()[0] > 0

    @_error_handler    
    def check_graded(self, session_id: str) -> int | None:
        """Check if a question already exists in responses table
        
        Args:
            session_id: Used to get questions to check for responses
        Returns:
            Count to see if response exists or None if an error occurs
        """        
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM responses
            JOIN questions ON questions.id = responses.question_id
            WHERE questions.session_id = ?
        """, (session_id,))

        return self.cursor.fetchone()[0]

    #fetching functions

    @_critical_handler
    def fetch_favorites(self) -> list[tuple]:
        """Fetch all favorites table info
        
        Returns:
            List of all favorites with their respective question_id, date_added, and note (or None instead of note)
        """   
        self.cursor.execute("""
            SELECT question_id, date_added, note
            FROM favorites
            ORDER BY question_id
        """)

        return self.cursor.fetchall()

    @_critical_handler
    def fetch_questions_for_favorites(self, question_ids: list[int]) -> list[tuple]:
        """Fetch all questions linked to favorites
        
        Args:
            question_ids: List of question ids to link a question to its favorite
        Returns:
            List of all questions that have are favorited
        """   

        placeholders = ",".join("?" * len(question_ids))
        question_ids = tuple(question_ids)

        self.cursor.execute(f"""
                SELECT question_text
                FROM questions
                WHERE id IN ({placeholders})
                ORDER BY id
        """, (question_ids))

        return self.cursor.fetchall()

    @_critical_handler
    def fetch_topic_grades(self) -> list[tuple]:
        """Fetch all response grades with their date and question topic

        Returns:
            List of tuples containing date, topic, and grade for each response
        """

        self.cursor.execute("""
            SELECT sessions.date, questions.question_topic, responses.grade
            FROM sessions
            JOIN questions ON sessions.id = questions.session_id
            JOIN responses ON questions.id = responses.question_id
            ORDER BY sessions.date 
        """)

        return self.cursor.fetchall()

    @_error_handler
    def fetch_weak_topics(self, subject: str) -> list[tuple[str]] | None:
        """Fetch all topics and their grades for a subject
        
        Args:
            subject: Subject for a session
        Returns:
            List of tuples with the topic and grade
        """

        self.cursor.execute("""
            SELECT questions.question_topic, responses.grade
            FROM sessions                                 
            JOIN questions ON sessions.id = questions.session_id
            JOIN responses ON questions.id = responses.question_id
            JOIN session_subjects on sessions.id = session_subjects.session_id
            WHERE session_subjects.subject = ?
        """, (subject,))
                            
        return self.cursor.fetchall()

    @_critical_handler
    def fetch_sessions(self) -> list[tuple]:
        """Fetch all sessions and their records

        Returns:
            List of tuples containing question type, difficulty, date, and session id
        """

        self.cursor.execute("""
            SELECT sessions.question_type, sessions.difficulty, sessions.date, sessions.id
            FROM sessions                   
            ORDER BY sessions.date
        """)
        
        return self.cursor.fetchall()

    @_critical_handler
    def fetch_subjects(self, session_id: int) -> list[tuple]:
        """Fetch subject(s) associated with a session

        Args:
            session_id: Used to link subjects to a session
        Returns:
            List of tuples containing the subject(s)
        """

        self.cursor.execute("""
            SELECT session_subjects.subject
            FROM session_subjects
            WHERE session_subjects.session_id = ?
        """, (session_id,))
        
        return self.cursor.fetchall()

    @_critical_handler
    def fetch_session_scores(self, session_id: int) -> list[tuple]:
        """Fetch all question grades from a session

        Args:
            session_id: Used to link session to questions
        Returns:
            List of tuples containing a question's number and grade
        """

        self.cursor.execute("""
            SELECT questions.question_number, responses.grade
            FROM questions
            JOIN responses ON questions.id = responses.question_id
            WHERE questions.session_id = ?
        """, (session_id,))

        return self.cursor.fetchall()

    @_critical_handler
    def fetch_session_category_subtype(self, session_id: int) -> list[tuple]:
        """Fetch a session's category and subtype

        Args:
            session_id: Used to fetch a specific sessions data
        Returns:
            List of tuples containing a sessions's category and subtype (or None if no subtype)
        """

        self.cursor.execute("""
            SELECT sessions.question_category, sessions.question_subtype
            FROM sessions
            WHERE sessions.id = ?
        """, (session_id,))

        return self.cursor.fetchone()

    @_critical_handler
    def fetch_questions(self, session_id: int) -> list[tuple]:
        """Fetch the related questions table information from a session

        Args:
            session_id: Used to fetch questions table
        Returns:
            List of tuples containing all question information: id, number, topic, and the question itself
        """

        self.cursor.execute("""
            SELECT questions.id, questions.question_number, questions.question_topic, questions.question_text
            FROM questions  
            WHERE questions.session_id = ?
            ORDER BY question_number
        """, (session_id,))

        return self.cursor.fetchall()

    @_critical_handler
    def fetch_responses(self, question_ids: list[int]) -> list[tuple]:
        """Fetch the related responses table information for all questions from a session

        Args:
            question_ids: List of question ids used to link responses
        Returns:
            List of tuples containing all response information for a question; answer, grade, and explanation
        """

        placeholders = ",".join("?" * len(question_ids))

        self.cursor.execute(f"""
                SELECT responses.answer, responses.grade, responses.explanation
                FROM responses
                WHERE responses.question_id IN ({placeholders})
                ORDER BY responses.question_id
        """, tuple(question_ids))

        return self.cursor.fetchall()

    #update info

    @_error_handler
    def update_favorite_note(self, new_note: str, question_id: int) -> str | None:
        """Update the note of a favorited question

        Args:
            new_note: New note for the favorited question
            question_id: Question id used to find favorite
        Returns:
            "success" if everything worked or None if an error occurs
        """

        self.cursor.execute(f"""
                UPDATE favorites
                SET note = ?
                WHERE question_id = ?
        """, (new_note, question_id))

        self.conn.commit()

        return "success"

    #remove

    @_error_handler
    def delete_favorite(self, question_id: int) -> str | None:
        """Remove a favorited question

        Args:
            question_id: Question id used to find favorite
        Returns:
            "success" if everything worked or None if an error occurs
        """

        self.cursor.execute(f"""
                DELETE FROM favorites
                WHERE question_id = ?
        """, (question_id,))

        self.conn.commit()

        return "success"

    #initialization function

    @_critical_handler
    def initiate_db(self) -> None:
        """Create all database tables if they do not already exist"""

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY,
                question_category TEXT,
                question_type TEXT,
                question_subtype TEXT,
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