
import json
import os

import logging
logger = logging.getLogger(__name__)

CONFIG_PATH = "config.json"

#menu

DEBUG_MODE = False
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s — %(message)s"
LOG_FILE = "./logs/sfk.log"

#ai details | generate_function and grade_function
MODEL = "gemini-3.5-flash"

#database

DB_PATH = "sfk.db"
TEST_MODE = False

MAX_DOCUMENTS = None
MAX_WEAK_TOPICS = None
SESSIONS_PER_PAGE = None
FAVORITES_PER_PAGE = None

_settings_dict = {
    "1": {
        "setting": "Max Notes Documents",
        "variable": "MAX_DOCUMENTS",
        "value_range": "1-10"
    },
    "2": {
        "setting": "Max Weak Topics",
        "variable": "MAX_WEAK_TOPICS",
        "value_range": "1-50"
    },
    "3": {
        "setting": "Sessions Per Page",
        "variable": "SESSIONS_PER_PAGE",
        "value_range": "1-50"
    },
    "4": {
        "setting": "Favorites Per Page",
        "variable": "FAVORITES_PER_PAGE",
        "value_range": "1-50"
    }
}

def change_config(final_config: dict[str, int]) -> None:
    """Display and allow editing of user-configurable settings
    
    View existing settings user can change. Allows them to select, change the value, and then saves new value. Handles None returns or failed attempts by returning users to menu.

    Args:
        final_config: Dict containing the current state of the config
    """

    global MAX_DOCUMENTS
    global MAX_WEAK_TOPICS
    global SESSIONS_PER_PAGE
    global FAVORITES_PER_PAGE

    # 1 = MAX_DOCUMENTS, 2 = MAX_WEAK_TOPICS, 3 = SESSIONS_PER_PAGE, 4 = FAVORITES_PER_PAGE
    print("""Settings:
    1. Max Notes Documents - Maximum number of notes documents that can be used to generate questions
    2. Max Weak Topics - Maximum number of weak topics used to generate questions
    3. Sessions Per Page - How many session previews are available to see per page in history
    4. Favorites Per Page - How many favorites are available to see per page in favorites
    """)

    new_config = None
    fail_count_response = 0

    new_config = final_config.copy()

    while fail_count_response < 3:
        response = input("Enter the corresponding number to change a setting or 'back' to go back to the main menu: ").lower().strip()

        
        if response == "back":
            if new_config:
                with open(CONFIG_PATH, "w") as file:
                    json.dump(new_config, file)
                print("New config saved. Going back to main menu.")
                return
            else:
                print("Going back to main menu.")
                return
        elif response in _settings_dict:
            setting = _settings_dict[response]["setting"]
            variable = _settings_dict[response]["variable"]
            value_range = _settings_dict[response]["value_range"]
        else:
            print("Answer not recognized. Please try again.")
            fail_count_response += 1
            continue

        if new_config:
            current_value = new_config[variable]
        else:
            current_value = final_config[variable]
        new_value = _change_item(setting, current_value, value_range)
        if not new_value:
            return
        new_config[variable] = new_value
        if response == "1":
            MAX_DOCUMENTS = new_value
        elif response == "2":
            MAX_WEAK_TOPICS = new_value
        elif response == "3":
            SESSIONS_PER_PAGE = new_value
        elif response == "4":
            FAVORITES_PER_PAGE = new_value

        logger.debug("Successfully changed setting %s from %s to %s", variable, current_value, new_value)

    if fail_count_response >= 3:
        print("Too many failed attempts. Exiting back to main menu.")
        return

def _change_item(setting: str, current_value: int, value_range: str) -> int | None:
    """Change one setting in the config
    
    Args:
        setting: Current setting being changed
        current_value: Current value of the setting
        value_range: Acceptable range for new setting value

    Returns:
        New value for the setting or None if too many failed attempts
    """

    print(f"The current value of {setting} is {current_value}")

    fail_count_change = 0

    while fail_count_change < 3:
        try:
            new_value = int(input(f"Please input a new value from {value_range}"))
            limits = value_range.split("-")
            lower_limit = int(limits[0])
            upper_limit = int(limits[1])
            if lower_limit <= new_value <= upper_limit:
                print(f"Setting successfully changed to {new_value}")
                return new_value
            else:
                print(f"Please input a value from {value_range}")
                fail_count_change += 1
        except ValueError:
            print("Please enter a number.")
            fail_count_change += 1
    if fail_count_change >= 3:
        print("Going back to main menu.")
        return None

def _check_config(config: dict[str, int]) -> dict[str, int]:
    """Check that the config and it's values exist and are within the valid range
    
    Args:
        config: dict with all the settings and their values
    Returns:
        Final config dict where all values exist and are within the valid range
    """

    global MAX_DOCUMENTS
    global MAX_WEAK_TOPICS
    global SESSIONS_PER_PAGE
    global FAVORITES_PER_PAGE

    MAX_DOCUMENTS = config.get("MAX_DOCUMENTS", 5)
    if not isinstance(MAX_DOCUMENTS, int) or not 1 <= MAX_DOCUMENTS <= 10:
        MAX_DOCUMENTS = 5
    MAX_WEAK_TOPICS = config.get("MAX_WEAK_TOPICS", 10)
    if not isinstance(MAX_WEAK_TOPICS, int) or not 1 <= MAX_WEAK_TOPICS <= 50:
        MAX_WEAK_TOPICS = 10
    SESSIONS_PER_PAGE = config.get("SESSIONS_PER_PAGE", 10)
    if not isinstance(SESSIONS_PER_PAGE, int) or not 1 <= SESSIONS_PER_PAGE <= 50:
        SESSIONS_PER_PAGE = 10
    FAVORITES_PER_PAGE = config.get("FAVORITES_PER_PAGE", 10)
    if not isinstance(FAVORITES_PER_PAGE, int) or not 1 <= FAVORITES_PER_PAGE <= 50:
        FAVORITES_PER_PAGE = 10
    
    final_config = {
    "MAX_DOCUMENTS": MAX_DOCUMENTS,
    "MAX_WEAK_TOPICS": MAX_WEAK_TOPICS,
    "SESSIONS_PER_PAGE": SESSIONS_PER_PAGE,
    "FAVORITES_PER_PAGE": FAVORITES_PER_PAGE
    }
    return final_config

def run_config() -> dict[str, int]:
    """Orchestrates the reading and initializing of the config json
    
    Returns:
        Dict containing all settings and their values
    """

    default_config = {
    "MAX_DOCUMENTS": 5,
    "MAX_WEAK_TOPICS": 10,
    "SESSIONS_PER_PAGE": 10,
    "FAVORITES_PER_PAGE": 10
    }

    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as file:
                config = json.load(file)
            final_config = _check_config(config)
        except Exception as e:
            logger.warning("Problem loading %s, instating default settings.", CONFIG_PATH)
            with open(CONFIG_PATH, "w") as file:
                json.dump(default_config, file)
            final_config = _check_config(default_config)
    else:
        with open(CONFIG_PATH, "w") as file:
            json.dump(default_config, file)
        final_config = _check_config(default_config)

    return final_config


if __name__ == "__main__":
    run_config()
