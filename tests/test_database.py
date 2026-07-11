
from database import Database
import pytest

#handlers

def test_insert_session_critical_handler(test_db):
    test_db.conn.close()
    with pytest.raises(Exception):
        test_db.insert_session("Analytical", "Critical Analysis", None, 5, "2026-06-27")

def test_insert_favorites_error_handler(test_db):
    test_db.conn.close()
    result = test_db.insert_favorites(2, "2026-06-27", "This question is amazing")
    assert result is None

#insert functions

def test_insert_session(sample_session):
    assert sample_session is not None
    assert isinstance(sample_session, int)

def test_insert_questions(test_db, sample_session_with_questions):
    test_db.cursor.execute("SELECT COUNT(*) FROM questions WHERE session_id = ?", (sample_session_with_questions,))
    count = test_db.cursor.fetchone()[0]
    assert count == 5

def test_insert_responses(test_db, sample_session_with_responses):
    test_db.cursor.execute("SELECT COUNT(*) FROM responses JOIN questions ON questions.id = responses.question_id WHERE questions.session_id = ?", (sample_session_with_responses,))
    count = test_db.cursor.fetchone()[0]
    assert count == 5

def test_insert_subjects(test_db, sample_session) -> None:
    test_db.cursor.execute("SELECT COUNT(*) FROM session_subjects WHERE session_id = ?", (sample_session,))
    count = test_db.cursor.fetchone()[0]
    assert count == 1

def test_insert_favorites(test_db, sample_session_with_questions):
    test_db.cursor.execute("SELECT id FROM questions WHERE session_id = ?", (sample_session_with_questions,))
    question_id = test_db.cursor.fetchone()[0]
    response = test_db.insert_favorites(question_id, "2026-06-27", "This question is amazing")
    test_db.cursor.execute("SELECT COUNT(*) FROM favorites WHERE question_id = ?", (question_id,))
    count = test_db.cursor.fetchone()[0]
    assert response is not None
    assert response == "success"
    assert count == 1

#check info

def test_check_favorite(test_db, sample_favorite):
    response = test_db.check_favorite(sample_favorite)
    assert response is True

#fetching functions

def test_fetch_topic_grades(test_db, sample_session_with_responses):
    results = test_db.fetch_topic_grades()
    row = results[0]
    assert row[0] == "2026-06-14-04-37-PM" #date
    assert row[1] == "Slope-Intercept Form Equation" #topic
    assert row[2] == "Correct" #grade
    
def test_fetch_weak_topics(test_db, sample_session_with_responses):
    test_db.cursor.execute("SELECT subject FROM session_subjects WHERE session_id = ?", (sample_session_with_responses,))
    subject = test_db.cursor.fetchone()[0]
    results = test_db.fetch_weak_topics(subject)
    assert results is not None
    assert len(results) > 0
    row = results[0]
    assert row[0] == "Slope-Intercept Form Equation" #question_topic
    assert row[1] == "Correct" #grade

def test_check_graded(test_db, sample_session_with_responses):
    count = test_db.check_graded(sample_session_with_responses)
    assert count is not None
    assert isinstance(count, int)
    assert count == 5

def test_fetch_sessions(test_db, sample_session_with_responses):
    results = test_db.fetch_sessions()
    row = results[0]
    assert row[0] == "Multiple Choice" is not None #question_type
    assert row[1] == 1 #difficulty
    assert row[2] == "2026-06-14-04-37-PM" #date
    assert row[3] == sample_session_with_responses #session id

def test_fetch_subjects(test_db, sample_session):
    results = test_db.fetch_subjects(sample_session)
    assert len(results) == 1
    assert results[0][0] == "math"

def test_fetch_sessions_scores(test_db, sample_session_with_responses):
    results = test_db.fetch_session_scores(sample_session_with_responses)
    row = results[0]
    assert row[0] == 1 #question_number
    assert row[1] == "Correct" #grade

def test_fetch_session_category_subtype(test_db, sample_session):
    result = test_db.fetch_session_category_subtype(sample_session)
    assert result[0] == "Selected Response"
    assert result[1] == None

def test_fetch_questions(test_db, sample_session_with_questions):
    results = test_db.fetch_questions(sample_session_with_questions)
    row = results[0]
    assert row[0] == 1 #questions id
    assert row[1] == 1 #question_number
    assert row[2] == "Slope-Intercept Form Equation" #question_topic
    assert row[3] == "What is the standard slope-intercept form of a linear equation? A) y = mx + b B) y = x^2 C) a^2 + b^2 = c^2 D) E = mc^2" #question_text

def test_fetch_responses(test_db, sample_session_with_responses):
    rows = test_db.cursor.execute("SELECT questions.id FROM questions WHERE session_id = ?", (sample_session_with_responses,))
    question_ids = []
    for row in rows:
        question_ids.append(row[0])
    results = test_db.fetch_responses(question_ids)
    assert results[0][0] == "Im going to say the correct answer is.......... A" #answer
    assert results[0][1] == "Correct" #grade
    assert results[0][2] == "The student chose option A. The standard slope-intercept form of a linear equation is indeed y = mx + b, where 'm' represents the slope and 'b' represents the y-intercept." #explanation

def test_initiate_db(test_db):
    test_db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in test_db.cursor.fetchall()]
    assert "sessions" in tables
    assert "questions" in tables
    assert "responses" in tables
    assert "session_subjects" in tables
    assert "favorites" in tables

def test_fetch_favorites(test_db, sample_favorite):
    results = test_db.fetch_favorites()
    assert results
    assert results[0][0] == 1 #question_id
    assert results[0][1] == "2026-06-27" #date_added
    assert results[0][2] == "This question is amazing" #note

def test_fetch_questions_for_favorites(test_db, sample_favorite):
    test_db.cursor.execute("SELECT question_id FROM favorites")
    question_ids = test_db.cursor.fetchone()
    results = test_db.fetch_questions_for_favorites(question_ids)
    assert results
    assert results[0][0] == "What is the standard slope-intercept form of a linear equation? A) y = mx + b B) y = x^2 C) a^2 + b^2 = c^2 D) E = mc^2" #question_text

def test_update_favorite_note(test_db, sample_favorite):
    test_db.cursor.execute("SELECT question_id, note FROM favorites")
    fetch = test_db.cursor.fetchall()
    question_id = fetch[0][0]
    note = fetch[0][1]
    assert note == "This question is amazing"
    new_note = "I hate this question"
    result = test_db.update_favorite_note(new_note, question_id)
    assert result == "success"
    test_db.cursor.execute("SELECT note FROM favorites")
    new_note_fetch = test_db.cursor.fetchall()[0][0]
    assert new_note_fetch == "I hate this question"

def test_delete_favorite(test_db, sample_favorite):
    test_db.cursor.execute("SELECT question_id FROM favorites")
    question_id = test_db.cursor.fetchone()[0]
    result = test_db.delete_favorite(question_id)
    assert result == "success"
    test_db.cursor.execute("SELECT question_id FROM favorites WHERE question_id = ?", (question_id,))
    assert test_db.cursor.fetchone() is None
