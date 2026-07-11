
from database import Database
from datetime import datetime
import math
from config import FAVORITES_PER_PAGE

import logging
logger = logging.getLogger(__name__)

def _get_favorites(db: Database) -> tuple[list[dict[str, any]], list[int]]:
    """Get all the favorites and their info

    Args:
        db: Database instance used to retrieve topic grade data
    Returns:
        A tuple of (favorites_list, question_ids) where favorites_list contains dicts with question_id, date_added, and note and question_ids contains all question ids in favorites
    """

    favorites_list = []
    question_ids = []

    favorites = db.fetch_favorites()

    if not favorites:
            print("No favorites found in database. Please add at least one favorite first.")
            exit()

    for row in favorites:
        question_id = row[0]
        date_added = row[1]
        note = row[2]

        favorite = {
            "question_id": question_id,
            "date_added": date_added,
            "note": note
        }
        
        favorites_list.append(favorite)
        question_ids.append(question_id)
        
    logger.debug("get_favorites returned %s favorites", len(favorites_list))

    return favorites_list, question_ids

def _get_questions(db: Database, favorites_list: list[dict[str, any]], question_ids: list[int]) -> list[dict[str, any]]:
    """Get all the questions related to each favorite

    Args:
        db: Database instance used to retrieve favorited questions
        favorites_list: List of favorites dicts with question_id, date_added, and note
        question_ids: All question ids with favorites used for fetching related questions
    Returns:
        List of favorites dicts with question_id, date_added, note, and question
    """

    questions = db.fetch_questions_for_favorites(question_ids)

    if len(favorites_list) != len(questions):
        logger.warning("Mismatch: %s favorites but %s questions returned", len(favorites_list), len(questions))

    for favorite, question in zip(favorites_list, questions):
        favorite["question"] = question

    favorites_list.sort(key=lambda x: x["date_added"], reverse = True)

    return favorites_list

def _favorites_preview(db: Database, favorites_questions: list[dict]) -> None:
    """Generate a paginated preview of all favorites for viewing, editing, or removal

    Displays favorites in pages, allowing user to select a favorite to change or remove. Calls exit on too many failed attempts or if the user chooses to exit.

    Args:
        db: Database instance passed on to change or remove favorite
        favorites_questions: List of favorites dicts with question_id, date_added, note, and question
    """

    page_total = math.ceil(len(favorites_questions)/FAVORITES_PER_PAGE)

    current_page = 1

    while True:
    
        start = (current_page - 1) * FAVORITES_PER_PAGE
        end = min(start + FAVORITES_PER_PAGE, len(favorites_questions))

        print(f"Favorite Previews Page {current_page}/{page_total}")

        for i, favorite in enumerate(favorites_questions[start:end], start = start + 1):
            print(f"""
    {i}. {favorite["date_added"]}
    Question:
    {favorite["question"]}
    Note:
    {favorite["note"]}
    """)
        
        while True:

            if current_page == 1:
                response = input("Please choose one of the above favorites by entering the corresponding number (e.g. 1, 2, 3). Or, enter n/e to view the next page/exit. ").lower().strip()
            elif current_page == page_total:
                response = input("Please choose one of the above favorites by entering the corresponding number (e.g. 1, 2, 3). Or, enter b/e to view the previous page/exit. ").lower().strip()
            else:
                response = input("Please choose one of the above favorites by entering the corresponding number (e.g. 1, 2, 3). Or, enter n/b/e to view the next/previous page/exit. ").lower().strip()
            if response == "n" and current_page < page_total:
                current_page += 1
                break
            elif response == "b" and current_page != 1:
                current_page -= 1
                break
            elif response == "e":
                exit()
            elif response == "n":
                print("You are already on the last page.")
            elif response == "b":
                print("You are already on the first page.")
            else:
                try:
                    response = int(response)
                    if start + 1 <= response <= end:
                        fail_count_choice = 0
                        favorite = favorites_questions[response - 1]
                        question = favorite["question"]
                        question_id = favorite["question_id"]
                        while fail_count_choice < 3:
                            choice = input("Please select one of the following options: change or remove?").lower().strip()
                            if choice == "change":
                                _change_favorite(db, question, question_id)
                                break
                            elif choice == "remove":
                                _remove_favorite(db, question, question_id)
                                break
                            else:
                                print("Answer not recognized. Please try again.")
                                fail_count_choice += 1
                        if fail_count_choice >= 3:
                            print("Too many failed attempts. Exiting.")
                            exit()
                        break
                    else:
                        print("Invalid favorite. Please try again.")
                except ValueError:
                    print("Invalid response. Please try again.")

def _change_favorite(db: Database, question: str, question_id: int) -> None:
    """Change the note on a favorited question

    Args:
        db: Database instance used to change favorite
        question: Text of the favorited question
        question_id: Used to find favorite in database
    """


    print(f"""
        Question:
        {question}
    """)

    new_note = input("Please enter the new note: ")

    status = db.update_favorite_note(new_note, question_id)

    if status:
        print("Note updated.")
    else:
        print("Could not update the note due to a local database issue.")

    _go_again()

def _remove_favorite(db: Database, question: str, question_id: int) -> None:
    """Remove a favorited question

    Args:
        db: Database instance used to remove favorite
        question: Text of the favorited question
        question_id: Used to find favorite in database
    """
    fail_count_confirm = 0

    while fail_count_confirm < 3:
        print(f"""
        Question:
        {question}
        """)
        confirm = input("Are you sure you want to remove this question from your favorites? (y/n) ").strip().lower()

        if confirm == "y":
            status = db.delete_favorite(question_id)
            if status:
                print("Favorite removed.")
            else:
                print("Could not remove the favorite due to a local database issue.")
            break
        elif confirm == "n":
            break
        else:
            print("Invalid response. Please input a valid response (y/n).")
            fail_count_confirm += 1
    if fail_count_confirm >= 3:
        print("Too many failed attempts. Exiting.")
        exit()

    _go_again()

def _go_again() -> None:
    """Continue or stop if user wants to change or remove another favorite"""
    
    fail_count_go_again = 0

    while fail_count_go_again < 3:
        go_again = input("Would you like to change or remove another favorite? (y/n) ").lower().strip()
        if go_again == "y":
            break
        elif go_again == "n":
            exit()
        else:
            print("Invalid response. Please input a valid response (y/n).")
            fail_count_go_again += 1
    if fail_count_go_again >= 3:
        print("Too many failed attempts. Exiting.")
        exit()

def run_favorites(db: Database) -> None:
    """Orchestrate the calling of required functions to preview and change or remove favorites
    
    Args:
        db: Database instance used to pass onto functions
    """

    favorites_list, question_ids = _get_favorites(db)

    favorites_questions = _get_questions(db, favorites_list, question_ids)

    _favorites_preview(db, favorites_questions)

if __name__ == "__main__":
    run_favorites()