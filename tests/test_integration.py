
import pytest
from database import Database
from analytics_function import generate_report

def test_generate_store_history(test_db, sample_session_with_responses):

    sessions = test_db.fetch_sessions()
    assert len(sessions) == 1
    
    session_id = sessions[0][3]
    subjects = test_db.fetch_subjects(session_id)
    assert len(subjects) == 1
    assert subjects[0][0] == "math"

    questions = test_db.fetch_questions(session_id)
    assert len(questions) == 5
    
    responses = test_db.fetch_responses([q[0] for q in questions])
    assert len(responses) == 5

def test_store_analytics(test_db, sample_session_with_responses):

    rows = test_db.fetch_topic_grades()
    assert len(rows) == 5
    
    topic_groups = {}
    for row in rows:
        date = row[0]
        topic = row[1]
        grade = row[2]
        if grade == "Correct":
            score = 1.0
        elif grade == "Partially Correct":
            score = 0.5
        else:
            score = 0.0
        if topic not in topic_groups:
            topic_groups[topic] = []
        topic_groups[topic].append({"date": date, "grade": grade, "score": score})
    
    report = generate_report(topic_groups)
    assert isinstance(report, str)
    assert "Weakness Ranking" in report
    assert len(report) > 0

def test_store_favorites_workflow(test_db, sample_session_with_questions):
    questions = test_db.fetch_questions(sample_session_with_questions)
    question_id = questions[0][0]
    
    result = test_db.insert_favorites(question_id, "2026-06-27", "good question")
    assert result == "success"
    
    already_favorited = test_db.check_favorite(question_id)
    assert already_favorited is True
    
    already_favorited_again = test_db.check_favorite(question_id)
    assert already_favorited_again is True

def test_create_fetch_change_remove_favorite(test_db, sample_session_with_questions):
    questions = test_db.fetch_questions(sample_session_with_questions)
    question_id = questions[0][0]

    result = test_db.insert_favorites(question_id, "2026-06-27", "This question is amazing")
    assert result == "success"

    fetch_favorite = test_db.fetch_favorites()
    question_id = fetch_favorite[0][0]
    assert fetch_favorite
    assert question_id == 1 #question_id
    assert fetch_favorite[0][1] == "2026-06-27" #date_added
    assert fetch_favorite[0][2] == "This question is amazing" #note

    question = test_db.fetch_questions_for_favorites(question_id)
    assert question
    assert question[0][0] == "What is the standard slope-intercept form of a linear equation? A) y = mx + b B) y = x^2 C) a^2 + b^2 = c^2 D) E = mc^2" #question_text

    new_note = "I hate this question"
    change = test_db.update_favorite_note(new_note, question_id)
    assert change == "success"
    test_db.cursor.execute("SELECT note FROM favorites")
    new_note_fetch = test_db.cursor.fetchall()[0][0]
    assert new_note_fetch == "I hate this question"

    result = test_db.delete_favorite(question_id)
    assert result == "success"
    test_db.cursor.execute("SELECT question_id FROM favorites WHERE question_id = ?", (question_id,))
    assert test_db.cursor.fetchone() is None