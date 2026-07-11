
from google import genai
from dotenv import load_dotenv
import os
from datetime import datetime
from database import Database

import logging
logger = logging.getLogger(__name__)

from client import client

def _grade_answers(answers: str) -> tuple[str, str]:
    """Send session answers to the AI model for grading and extract results

    Handles API errors with retry logic. Weak topics are extracted from the response and returned separately; returns an empty string if none are found
    
    Args:
        answers: Text from a completed session document with questions and responses
    Returns:
        Tuple of (grading, weak_topics) where grading contains the full graded response and weak_topics contains identified weak topics, or an empty string if none
    """

    prompt = f"""
    You are a study assistant. Based on these answers to the given questions please grade them.
    For each grade please give a reason and if it's a wrong answer offer what went wrong.
    Remember to keep it in a format that's understandable in a Microsoft notepad document.
    As well, if there are equally wrong topics just put the first alphabetical topic (at the same amount wrong) first in the chain relatively.
    Please label the weak topics, if there are any, as there respective grades. If more than one question of the same topic is missed write the topic name and grade on separate lines equal to the distribution of the grade.
    If all answers are correct do not include any Weak Topics section and don't include the section title.
    Start directly with topic title listing all covered topics separated by commas in the order of which they are asked in each question at the top of your response.
    As well, include the topic title directly above each question. When listing the topic above each question JUST list that question's topic.
    As well, please list the question difficulty above each question a shown in the example below.
    Do not include any extra introduction or explanation other than what's listed.
    For problems involving math please show your work.
    Format each one as:
    Grading:
    Topic Title: [topic]
    Question Difficulty: [difficulty]
    Q: [question given]
    A: [answer given]
    G: [Correct / Partially Correct / Incorrect]
    E: [explanation]
    Weak Topics:
    - [topic that got Incorrect] [grade]
    - [topic that got Partially Correct] [grade]
    Questions and Answers:
    {answers}
    """
    while True:
        try:
            response = client.models.generate_content(
            model = "gemini-3.5-flash",
            contents = prompt
            )
            break
        except Exception as e:
            if "503" in str(e):
                logger.warning("Gemini is currently unavailable due to high demand. Please try again in a moment.")
            else:
                logger.error("Generation failed.", exc_info=True)
            retry = input("Would you like to try generating again? (y/n): ").strip().lower()
            if retry != 'y':
                raise RuntimeError("Question generation failed.") from e

    parts_grade = response.text.split("Weak Topics:")
    grading = parts_grade[0]

    if len(parts_grade) > 1 and len(parts_grade[1].strip()) > 5:
        weak_topics = parts_grade[1]
    else:
        weak_topics = ""

    return grading, weak_topics

def _validate_manual_entry(filename: str) -> tuple[bool, str | None]:
    """Validate a manually entered question document filename
    
    Args:
        filename: Manually entered file to validate
    Returns:
        Tuple of (is_valid, error_message), where error_message is empty if validation succeeds
    """

    extension = os.path.splitext(filename)[1]
    if extension != ".txt":
        return False, f"Unsupported file type: {extension}"

    if os.path.dirname(filename) not in {"", "."}:
        return False, "Please enter only the filename, not a path"
    
    if not os.path.exists(filename):
        return False, f"File '{filename}' not found in current directory"

    if not os.access(filename, os.R_OK):
        return False, f"Cannot read '{filename}' — check permissions"

    return True, None

def _confirm_document(question_document: str) -> tuple[bool, int | None, str | None]:
    """Display a preview and ask the user to confirm the selected document

    Generates preview to allow user to view document. Handles errors from input or reading document.

    Args:
        question_document: Name of document with suffix read to get answers
    Returns:
        Tuple of (confirmed, session_id, answers), if confirmation fails or an error occurs, session_id and answers are None
    """

    fail_count_confirm = 0
    
    try:
        with open(question_document, "r") as f:
            answers = f.read()

        lines = answers.split("\n")
        preview = "\n".join(lines[:25])
        print("Document preview: ")
        print(f"{preview}")

        while fail_count_confirm < 3:
            document_confirm = input("Is this the correct document? (y/n)").strip().lower()
            if document_confirm == "y":
                session_id = int(lines[0].replace("Session ID:", "").strip())
                return True, session_id, answers
            elif document_confirm == "n":
                return False, None, None
            else:
                print("Invalid response. Please input a valid response (y/n).")
                fail_count_confirm += 1
        if fail_count_confirm >= 3:
            print("Too many failed attempts. Exiting.")
            exit()
    except (FileNotFoundError, OSError) as e:
        logger.warning("Failed to open document: %s", e)
        print("Questions document extraction failed. Please try another notes document.")
        return False, None, None
    
def _check_already_graded(db: Database, session_id: int) -> bool:
    """Check if the selected session has already been graded

    Args:
        db: Database instance used to check database for existing session grades
        session_id: Links answer document to database
    Returns:
        True if grading should continue, otherwise False
    """

    fail_count_warn = 0

    count = db.check_graded(session_id)

    if count is None:
        print("Could not retrieve previous grade information due to a local database issue. Continuing on.")
        return True

    if count > 0:
        while fail_count_warn < 3:
            warn_response = input("Warning: This session has already been graded. Continue anyway? (y/n) ").strip().lower()
            if warn_response == "y":
                return True
            elif warn_response == "n":
                return False
            else:
                print("Invalid response. Please input a valid response (y/n).")
                fail_count_warn += 1
        if fail_count_warn >= 3:
            print("Too many failed attempts. Exiting.")
            exit()
    return True

def _get_session_subject(db: Database, session_id: int) -> str | None:
    """Extract subject(s) from database

    Args:
        db: Database instance used to fetch subject(s)
        session_id: Used to link answer document to subject(s)
    Returns:
        Subject(s) formatted or None if there is an error
    """

    subjects = db.fetch_subjects(session_id)

    if not subjects:
        return None
    
    return " ".join(subject[0] for subject in subjects)
    
def _get_answer_document(db: Database) -> tuple[str, str]:
    """Prompt the user to select an answer document for grading

    Displays available answer documents, supports manual entry, validates the selection, confirms the chosen document, and checks for previous grading
    
    Args:
        db: Database instance to pass onto required functions
    Returns:
        Tuple of (answers, subject), where answers contains the full document contents
    """

    fail_count_answered_document = 0
    fail_count_read_document = 0
    fail_manual_entry = 0
    answers = None

    answered_documents = [file for file in os.listdir(".") if "questions" in file]

    while fail_count_answered_document < 3 and fail_count_read_document < 3:
        document_count = len(answered_documents)

        print("Answered Questions: ")
        for i, file in enumerate(answered_documents, start = 1):
            print(f"{i}. {file}")
        print(f"{document_count + 1}. Manual entry")

        try:
            answered_document = int(input("Please choose one of the above documents by entering the corresponding number (e.g. 1, 2, 3). "))
            if answered_document == document_count + 1:
                while fail_manual_entry < 3:
                    manual_entry = input("Please enter the full filename (including the extension): ")
                    is_valid, manual_error = _validate_manual_entry(manual_entry)
                    if is_valid:
                        answered_documents.append(manual_entry)
                        break
                    else:
                        print(f"{manual_error}. Please try again")
                        fail_manual_entry += 1
                        continue
                if fail_manual_entry >= 3:
                    print("Too many failed attempts. Please try another document.")
                    continue
        except ValueError:
            print("The document chosen was not recognized. Please try again.")
            fail_count_answered_document +=1
            continue
        try:
            question_document = answered_documents[answered_document - 1]
        except IndexError:
            print("Chosen document not in range. Please try again.")
            continue

        confirmed, session_id, answers = _confirm_document(question_document)
        if confirmed and session_id and answers:
            continue_on = _check_already_graded(db, session_id)
            if continue_on:
                subject = _get_session_subject(db, session_id)
                if not subject or len(subject) < 1:
                    print("Please choose another document.")
                    continue
                return answers, subject
            if not continue_on:
                print("Please choose another document.")
                continue
        else:
            fail_count_answered_document = 0
            fail_count_read_document = 0
            fail_manual_entry = 0
            answers = None
            continue
    if fail_count_answered_document >= 3 or fail_count_read_document >= 3:
        print("Too many failed attempts. Exiting.")
        exit()

def run_grade(db: Database) -> None:
    """Orchestrate the calling of required functions and creating of graded document

    Gets text and session id from graded document. Feeds AI model and gets graded version. Creates the graded and weak topic files. Insert graded and response information into database.
    
    Args:
        db: Database instance to pass into functions when needed to retrieve information
    """

    today = datetime.now().strftime("%Y-%m-%d-%I-%M-%p")

    answers, subject = _get_answer_document(db)

    try:
        grade, weak_topics = _grade_answers(answers)
    except RuntimeError as e:
        logger.critical(e)
        raise

    session_id = int(answers.split("\n")[0].replace("Session ID:", "").strip())

    header = f"Session ID: {session_id}\n\n"
    final_grade_output = header + grade 

    db.insert_responses(grade, session_id)

    with open(f"graded {subject} answers {today}.txt", "w") as f:
        f.write(final_grade_output)
        print(f"Grades saved to 'graded {subject} answers {today}.txt'")

    if len(weak_topics) > 1 and len(weak_topics.strip()) > 5:
        with open(f"weak {subject} topics {today}.txt", "w") as f:
            f.write(weak_topics)
        print(f"Weak topics saved to 'weak {subject} topics {today}.txt'")
    else:
        print("No weak topics found.")

if __name__ == "__main__":
    run_grade()
