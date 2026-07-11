from database import Database
import math
from config import SESSIONS_PER_PAGE
from datetime import datetime

import logging
logger = logging.getLogger(__name__)

def _get_session_list(db: Database) -> list[dict[str, any]]:
    """Get and compile all sessions and info
    
    Args:
        db: Database instance used to fetch session info
    Returns:
        List of session dicts that contain a summary of session info
    """

    session_list = []

    sessions = db.fetch_sessions()

    if not sessions:
        print("No sessions found in database. Complete a full session first.")
        exit()

    for row in sessions:
        question_type = row[0].lower()
        difficulty = row[1]
        date = row[2]
        session_id = row[3]

        subjects_raw = db.fetch_subjects(session_id)

        if not subjects_raw:
            logger.warning("No subjects found for session '%s'", session_id)
            continue
        subjects = [row[0].lower() for row in subjects_raw]


        rows_scores = db.fetch_session_scores(session_id)

        scores = []

        if not rows_scores:
            print(f"No responses found for session {session_id}. Please finish the session or remove it.")
            continue

        total_questions = len(rows_scores)

        for row in rows_scores:

            if row[1] == "Correct":
                score = 1.0
            elif row[1] == "Partially Correct":
                score = .5
            else:
                score = 0.0
            scores.append(score)

        grade_avg = sum(scores) / len(scores)

        session = {
            "date": date,
            "session_id": session_id,
            "subjects": subjects,
            "question_type": question_type,
            "difficulty": difficulty,
            "grade": f"{grade_avg:.2f}",
            "total_questions": total_questions
        }
        session_list.append(session)

    session_list.sort(key=lambda x: x["date"])
    logger.debug("get_session_list returned %s sessions", len(session_list))

    if not session_list:
        print("No valid sessions found. Please complete a graded session or remove incomplete ones.")
        exit()

    return session_list

def get_session_preview(db: Database) -> None:
    """Display a paginated preview of previous study sessions

    Fetches session data from function, formats session summaries, and allows the user to navigate pages or select a session to view full details
    
    Args:
        db: Database passed into required functions
    """
    
    session_list = _get_session_list(db)

    page_total = math.ceil(len(session_list)/SESSIONS_PER_PAGE)

    current_page = 1

    while True:
    
        start = (current_page - 1) * SESSIONS_PER_PAGE
        end = min(start + SESSIONS_PER_PAGE, len(session_list))

        print(f"Session Previews Page {current_page}/{page_total}")

        for i, session in enumerate(session_list[start:end], start = start + 1):
            if len(session["subjects"]) > 1:
                subjects = " ".join(subject for subject in session["subjects"])
                text_subject = "Subjects: " + subjects
            else:
                text_subject = "Subject: " + session["subjects"][0]
            print(f"""
    {i}. {session["date"]}
    Session ID: {session["session_id"]}
    Difficulty: {session["difficulty"]}
    {text_subject}
    You answered {session["total_questions"]} {session["question_type"]} questions.
    Your final grade was {session["grade"]}    
    """)
        
        while True:
            if current_page == 1:
                session_response = input("Please choose one of the above sessions by entering the corresponding number (e.g. 1, 2, 3). Or, enter n/e to view the next page/exit. ").lower().strip()
            elif current_page == page_total:
                session_response = input("Please choose one of the above sessions by entering the corresponding number (e.g. 1, 2, 3). Or, enter b/e to view the previous page/exit. ").lower().strip()
            else:
                session_response = input("Please choose one of the above sessions by entering the corresponding number (e.g. 1, 2, 3). Or, enter n/b/e to view the next/previous page/exit. ").lower().strip()
            if session_response == "n" and current_page < page_total:
                current_page += 1
                break
            elif session_response == "b" and current_page != 1:
                current_page -= 1
                break
            elif session_response == "e":
                exit()
            elif session_response == "n":
                print("You are already on the last page.")
            elif session_response == "b":
                print("You are already on the first page.")
            else:
                try:
                    session_response = int(session_response)
                    if start + 1 <= session_response <= end:
                        if len(session["subjects"]) > 1:
                            subjects = " ".join(subject for subject in session_list[session_response - 1]["subjects"])
                            text_subject = "Subjects: " + subjects
                        else:
                            text_subject = "Subject: " + session_list[session_response - 1]["subjects"][0]
                        _get_full_session(session_list[session_response - 1], text_subject)
                        break
                    else:
                        print("Invalid session. Please try again.")
                except ValueError:
                    print("Invalid response. Please try again.")

def _get_full_session(db: Database, session_prev: dict[str, any], text_subject: str) -> None:
    """Display a detailed view of a selected study session

    Uses session data from the database and the session preview to display questions, responses, grades, and explanations. Allows the user to add questions to their favorites

    Args:
        db: Database used to retrieve session details
        session_prev: Dict containing selected session info summary
        text_subject: Formatted str to display subject(s) for the selected session
    """

    subtype_addon = ""

    session = session_prev
    session_id = session["session_id"]
    
    category_subtype_row = db.fetch_session_category_subtype(session_id)

    if not category_subtype_row:
        logger.warning("Failed to fetch question category for session %s.", session_id)
        print("Could not load session data. Please try another session.")
        return
    
    category = category_subtype_row[0]
    subtype = category_subtype_row[1]

    session["question_category"] = category
    if subtype:
        subtype_addon = f" — {subtype}"

    question_info = db.fetch_questions(session_id)
    
    question_ids = []
    question_numbers = []
    question_topics = []
    question_texts = []

    if not question_info:
        logger.warning("Failed to fetch question information for session %s.", session_id)
        print("Could not load session data. Please try another session.")
        return

    for row in question_info:
        question_ids.append(row[0])
        question_numbers.append(row[1])
        question_topics.append(row[2])
        question_texts.append(row[3])
    
    responses_raw = db.fetch_responses(question_ids)

    responses = []

    if not responses_raw:
        logger.warning("Failed to fetch response information for session %s.", session_id)
        print("Could not load session data. Please try another session.")
        return

    for row in responses_raw:

        response = {
            "answer": row[0],
            "grade": row[1],
            "explanation": row[2]
        }

        responses.append(response)

    print(f"""
    {session["date"]}
    Session ID: {session["session_id"]}
    Subjects: {text_subject}
    Question Type: {session["question_category"]} — {session["question_type"]}{subtype_addon}
    Difficulty: {session["difficulty"]}
    Questions: {session["total_questions"]}
    Grade: {session["grade"]}
    """)

    for x in range(int(session["total_questions"])):
        print(f"""
    {question_numbers[x]}
    Topic Title: {question_topics[x]}
    Q: {question_texts[x]}
    A: {responses[x]["answer"]}
    G: {responses[x]["grade"]}
    E: {responses[x]["explanation"]}
    """)

    fail_count_add_fav = 0
    
    while fail_count_add_fav < 3:
        add_fav = input("Would you like to add a question to your favorites? (y/n) ").lower().strip()
        if add_fav == "y":
            _add_favorite(db, question_ids)
            break
        elif add_fav == "n":
            break
        else:
            print("Invalid response. Please input a valid response (y/n).")
            fail_count_add_fav += 1
    if fail_count_add_fav >= 3:
        print("Too many failed attempts. Moving on.")

    fail_count_go_on = 0

    while fail_count_go_on < 3:
        go_on = input("Would you like to view another session? (y/n) ").lower().strip()
        if go_on == "y":
            break
        elif go_on == "n":
            exit()
        else:
            print("Invalid response. Please input a valid response (y/n).")
            fail_count_go_on += 1
    if fail_count_go_on >= 3:
        print("Too many failed attempts. Exiting.")
        exit()

def _add_favorite(db: Database, question_ids: list[int]) -> None:
    """Prompts user to input favorite

    Uses user input to identify a question, checks whether the question is already favorited, and adds the favorite to the database. Handles invalid input and retry attempts

    Args:
        db: Database used to input and check favorites
        question_ids: All question ids used to link selected question to favorite in database
    """

    while True:
        fail_count_favorite = 0
        add_another = False

        while fail_count_favorite < 3:
            try:
                question_number = int(input("Please enter the corresponding question number. ").strip())
                question_id = question_ids[question_number - 1]

                already_favorited = db.check_favorite(question_id)

                if already_favorited:
                    print(f"Question {question_number} is already in your favorites.")
                elif already_favorited is None:
                    print("Could not check favorites. Please try again.")
                else:
                    date = datetime.now().strftime("%Y-%m-%d")
                    note = input("Add a note (optional, press Enter to skip): ").strip()
                    if not note:
                        note = None
                    result = db.insert_favorites(question_id, date, note)
                    if result:
                        print(f"Question {question_number} added to favorites.")
                    else:
                        print(f"Could not save favorite for question {question_number}.")
                fail_count_another = 0
                while fail_count_another < 3:
                    another_response = input("Would you like to add another favorite? (y/n) ").lower().strip()
                    if another_response == "y":
                        add_another = True
                        break
                    elif another_response == "n":
                        return
                    else:
                        print("The question chosen was not recognized. Please try again.")
                        fail_count_another += 1
                if fail_count_another >= 3:
                    print(f"Too many failed attempts. Moving on.")
                    return
                if add_another:
                    break
            except (ValueError, IndexError):
                print("The question chosen was not recognized. Please try again.")
                fail_count_favorite += 1 
        if fail_count_favorite >= 3:
            print("Too many failed attempts. Moving on.")
            return

if __name__ == "__main__":
    get_session_preview()