
from generate_function import run_generate
from grade_function import run_grade
from analytics_function import run_analytics
from database import Database
from history import get_session_preview
from config import run_config, change_config, DB_PATH, DEBUG_MODE, LOG_FORMAT, LOG_FILE
from favorites import run_favorites

import os
import logging

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level = logging.DEBUG if DEBUG_MODE else logging.WARNING,
    format = LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def menu() -> None:

    db = Database(DB_PATH)
    db.initiate_db()

    final_config = run_config()

    fail_counter = 0

    while fail_counter < 3:
        goal = input("""Please choose one of the following: 
            Generate
            Grade
            Analyze
            History
            Favorites
            Settings        
        """).strip().lower()

        if goal == "generate":
            run_generate(db)#(from_favorites = False)
            break
        #elif goal == "generate from favorites":
            #run_generate(from_favorites = True)
            #break
        elif goal == "grade":
            run_grade(db)
            break
        elif goal == "analyze":
            run_analytics(db)
            break
        elif goal == "history":
            get_session_preview(db)
            break
        elif goal == "favorites":
            run_favorites(db)
            break
        elif goal == "settings":
            change_config(final_config)
            fail_counter = 0
            continue
        else:
            print("Error: Answer not recognized. Please try again.")
            fail_counter += 1

    if fail_counter >= 3:
        print("Too many failed attempts. Exiting.")
        exit()

if __name__ == "__main__":
    menu()