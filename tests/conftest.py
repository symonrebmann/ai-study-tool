import pytest
import sqlite3
from database import Database
import config
config.TEST_MODE = True

@pytest.fixture
def test_db():
    db = Database(":memory:")
    db.initiate_db()
    yield db
    db.conn.close()

@pytest.fixture
def sample_session(test_db):
    session_id = test_db.insert_session("Selected Response", "2. Multiple Choice", 1, "2026-06-14-04-37-PM")
    test_db.insert_subjects(["math"], session_id)
    return session_id

@pytest.fixture
def sample_session_with_questions(test_db, sample_session, sample_questions_text):
    text = sample_questions_text
    test_db.insert_questions(text, sample_session)
    return sample_session

@pytest.fixture
def sample_session_with_responses(test_db, sample_session_with_questions, sample_responses_text):
    text = sample_responses_text

    test_db.insert_responses(text, sample_session_with_questions)
    return sample_session_with_questions

@pytest.fixture
def sample_favorite(test_db, sample_session_with_questions):
    test_db.cursor.execute("SELECT id FROM questions WHERE session_id = ?", (sample_session_with_questions,))
    question_id = test_db.cursor.fetchone()[0]
    date = "2026-06-27"
    note = "This question is amazing"
    test_db.insert_favorites(question_id, date, note)
    return question_id

@pytest.fixture
def sample_questions_text():
    return """Session ID: 2

Slope-Intercept Form Equation, Definition of Slope, Definition of Y-intercept, Parallel Lines Slopes, Perpendicular Lines Slopes

Topic Title: Slope-Intercept Form Equation
Question Difficulty: Pure surface-level recall
Q: What is the standard slope-intercept form of a linear equation?
A) y = mx + b
B) y = x^2
C) a^2 + b^2 = c^2
D) E = mc^2
A: ______

Topic Title: Definition of Slope
Question Difficulty: Pure surface-level recall
Q: In the equation y = mx + b, what does the letter 'm' represent?
A) Slope
B) Banana
C) Circle
D) Elephant
A: ______

Topic Title: Definition of Y-intercept
Question Difficulty: Pure surface-level recall
Q: In the equation y = mx + b, what does the letter 'b' represent?
A) Y-intercept
B) Apple juice
C) Maximum speed
D) Temperature
A: ______

Topic Title: Parallel Lines Slopes
Question Difficulty: Pure surface-level recall
Q: What is true about the slopes of parallel lines?
A) They are equal.
B) They are imaginary.
C) They do not exist.
D) They are always purple.
A: ______

Topic Title: Perpendicular Lines Slopes
Question Difficulty: Pure surface-level recall
Q: Perpendicular lines have slopes that are what?
A) Negative reciprocals
B) Friendly neighbors
C) Exactly zero
D) Extremely loud
A: ______"""


@pytest.fixture
def sample_responses_text():
    return """Session ID: 2

Slope-Intercept Form Equation, Definition of Slope, Definition of Y-intercept, Parallel Lines Slopes, Perpendicular Lines Slopes

Grading:
Topic Title: Slope-Intercept Form Equation
Question Difficulty: Pure surface-level recall
Q: What is the standard slope-intercept form of a linear equation?
A) y = mx + b
B) y = x^2
C) a^2 + b^2 = c^2
D) E = mc^2
A: Im going to say the correct answer is.......... A
G: Correct
E: The student chose option A. The standard slope-intercept form of a linear equation is indeed y = mx + b, where 'm' represents the slope and 'b' represents the y-intercept.

Grading:
Topic Title: Definition of Slope
Question Difficulty: Pure surface-level recall
Q: In the equation y = mx + b, what does the letter 'm' represent?
A) Slope
B) Banana
C) Circle
D) Elephant
A: The correct answer is A.
G: Correct
E: The student chose option A. In the slope-intercept equation y = mx + b, the variable 'm' represents the slope of the line.

Grading:
Topic Title: Definition of Y-intercept
Question Difficulty: Pure surface-level recall
Q: In the equation y = mx + b, what does the letter 'b' represent?
A) Y-intercept
B) Apple juice
C) Maximum speed
D) Temperature
A: This is easy. It's A
G: Correct
E: The student chose option A. In the slope-intercept equation y = mx + b, the constant 'b' represents the y-intercept.

Grading:
Topic Title: Parallel Lines Slopes
Question Difficulty: Pure surface-level recall
Q: What is true about the slopes of parallel lines?
A) They are equal.
B) They are imaginary.
C) They do not exist.
D) They are always purple.
A: Frick idk.... maybe.... D?
G: Incorrect
E: The student chose option D, but the correct answer is A. Parallel lines run in the same direction and never intersect, which means they must have identical steepness. Therefore, the slopes of parallel lines are always equal.

Grading:
Topic Title: Perpendicular Lines Slopes
Question Difficulty: Pure surface-level recall
Q: Perpendicular lines have slopes that are what?
A) Negative reciprocals
B) Friendly neighbors
C) Exactly zero
D) Extremely loud
A: Well, it has smth to do with recipricals I think but definitely not negative so uhhhh C?
G: Incorrect
E: The student chose option C, but the correct answer is A. Perpendicular lines intersect at a 90-degree angle. Their slopes are negative (or opposite) reciprocals of one another (for example, a line with a slope of 2 is perpendicular to a line with a slope of -1/2). The student recalled the word "reciprocals" but incorrectly assumed they were not negative, leading them to select C."""