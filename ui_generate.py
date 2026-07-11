
_question_category_dict = {
"1": "Analytical",
"2": "Extended Written Response",
"3": "Selected Response",
"4": "Short Written Response",
"5": "STEM-Specific"
}

_question_type_dict = {
"Analytical": ["Analogy", "Categorization/Sorting", "Cause and Effect", "Error Identification", "Interpretation", "Prediction"],
"Extended Written Response": ["Essay", "Free Response", "Peer Review", "Research/Find", "Scenario/Case Study"],
"Selected Response": ["Matching", "Multiple Choice", "Multiple-select", "Ordering/Sequencing", "True/False"],
"Short Written Response": ["Classify", "Define", "Fill in the Blank", "Identify", "Numerical Response", "Passage Completion", "Short Answer"],
"STEM-Specific": ["Code Writing/Debugging", "Derivation", "Problem-Solving", "Proof"]
}

_question_subtype_dict = {
"Essay": ["Argumentative", "Compare and Contrast", "Expository", "Narrative", "Persuasive", "Reflective"],
"Free Response": ["Analyze", "Describe", "Discuss", "Evaluate", "Outline", "Summarize"],
}

def _select_question_format() -> str:
    """Prompt the user to select a question category
    
    Returns:
        Chosen question category str
    """

    fail_count = 0

    while fail_count < 3:
        print("""Question Formats:
1. Analytical
2. Extended Written Response
3. Selected Response
4. Short Written Response
5. STEM-Specific""")
        question_format = input("Please choose one of the above question formats by entering the corresponding number (e.g. 1, 2, 3). ").strip()
        if question_format in _question_category_dict:
            break
        else:
            fail_count += 1
            print("The question format chosen was not recognized. Please try again.")
    if fail_count >= 3:
        print("Too many failed attempts. Exiting.")
        exit()

    return _question_category_dict[question_format]

def _select_question_type(question_category: str) -> tuple[str | None, str | None]:
    """Prompt the user to select a question type

    Args:
        question_category: Used in category dict to get question type list
    Returns:
        Tuple (question_type, question_subtype) where question_type is the chosen type and question_subtype is the chosen subtype (if applicable) or both None when the user wants to go back
    """

    fail_count = 0

    while fail_count < 3:
        print("Question Types:")
        options = _question_type_dict[question_category]
        for i, option in enumerate(options, start=1):
            print(f"{i}. {option}")
        print(f"{len(options) + 1}. Back")
        try:
            response_type = int(input("Please choose one of the above question types by entering the corresponding number (e.g. 1, 2, 3). ").strip())
            if response_type == len(options) + 1:
                return None, None
            question_type = options[response_type - 1]
            if question_type in _question_subtype_dict:
                question_subtype = _select_question_subtype(question_type)
                if not question_subtype:
                    continue
                return question_type, question_subtype
            else:
                return question_type, None
        except (ValueError, IndexError):
            print("The question type chosen was not recognized. Please try again.")
            fail_count += 1
    if fail_count >= 3:
        print("Too many failed attempts. Exiting.")
        exit()

def _select_question_subtype(question_type: str) -> str | None:
    """Prompt the user to select a question subtype

    Args:
        question_type: Used in subtype dict to get question subtype list
    Returns:
        Str containing question subtype or None when the user wants to go back
    """

    fail_count = 0

    while fail_count < 3:
        print("Question subtypes:")
        options = _question_subtype_dict[question_type]
        for i, option in enumerate(options, start=1):
            print(f"{i}. {option}")
        print(f"{len(options) + 1}. Back")
        try:
            response_subtype = int(input("Please choose one of the above question subtypes by entering the corresponding number (e.g. 1, 2, 3). ").strip())
            if response_subtype == len(options) + 1:
                return None
            question_subtype = options[response_subtype - 1]
            return question_subtype
        except (ValueError, IndexError):
            print("The question type chosen was not recognized. Please try again.")
            fail_count += 1
    if fail_count >= 3:
        print("Too many failed attempts. Exiting.")
        exit()

def _select_question_amount(question_max: int, question_topic: bool, topic_max: int | None) -> tuple[int, int | None]:
    """Prompt the user to select the question and, optionally, topic amount

    Args:
        question_max: Maximum number of questions the user may request
        question_topic: Whether the user should also choose the number of topics
        topic_max: Maximum number of topics the user may request, or None if topics are not used
    Returns:
        Tuple (question_amount, topic_amount) where question_amount is chosen question amount and topic_amount is chosen topic amount or None if not applicable
    """

    topic_amount = None
    fail_count = 0

    while fail_count < 3:
        try:
            question_amount = int(input(f"How many questions would you like? (1 - {question_max}): "))
            if question_topic:
                topic_amount = int(input(f"How many essay topics would you like to be able to choose from (per question)? (1 - {topic_max}) "))
            if question_amount > question_max:
                print(f"Error: Too many questions. Please try an amount {question_max} or under.")
                fail_count += 1
            elif question_amount <= 0:
                print("Error: Please enter a positive integer.")
                fail_count += 1
            elif question_topic and topic_amount <= 0:
                print("Error: Please enter a positive integer.")
                fail_count += 1
            elif question_topic and topic_amount > topic_max:
                print(f"Error: Too many topics. Please try an amount {topic_max} or under.")
                fail_count += 1
            else:                    
                break
        except ValueError:
            print("Error: Please enter a valid integer.")
            fail_count += 1   
    if fail_count >= 3:
        print("Too many failed attempts. Exiting.")
        exit()
    
    return question_amount, topic_amount

def _get_question_amount(question_type: str | None) -> tuple[int, int | None]:
    """Prompt the user to select the question and, optionally, topic amount

    Args:
        question_type: Determines question_max, question_topic, and topic_max
    Returns:
        Tuple (question_amount, topic_amount) where question_amount is chosen question amount and topic_amount is chosen topic amount or None if not applicable
    """

    question_topic = False
    topic_max = None

    if question_type == "Essay":
        question_max = 5
        question_topic = True
        topic_max = 5
    elif question_type == "Free Response":
        question_max = 10
    else:
        question_max = 25

    return _select_question_amount(question_max, question_topic, topic_max)

def _question_difficulty() -> int:
    """Prompt the user to select the session difficulty

    Returns:
        Chosen question difficulty
    """

    fail_count = 0
    while fail_count < 3:
        try:
            difficulty = int(input("Please choose a difficulty 1-10: ").strip())
            if difficulty > 10:
                print("Please enter a number 1-10")
                fail_count += 1
            elif difficulty < 1:
                print("Please enter a number 1-10")
                fail_count += 1
            else:
                fail_count_2 = 0
                while fail_count_2 < 3:
                    diff_confirm = input(f"Are you sure you want a difficulty of {difficulty}/10? (y/n): ").strip().lower()
                    if diff_confirm == "y":
                        return difficulty
                    if diff_confirm == "n":
                        break
                    else:
                        print("Please choose y/n.")
                        fail_count_2 += 1
                        continue
                if fail_count_2 >= 3:
                    print("Too many failed attempts. Exiting.")
                    exit()
        except (ValueError, IndexError):
            print("Error: Please enter a valid integer.")
            fail_count += 1
    if fail_count >= 3:
        print("Too many failed attempts. Exiting.")
        exit()

def get_question_info() -> tuple[str, str, str | None, int, int | None, int]:
    """Orchestrate the calling of required functions prompting the user to choose required session info

    Returns:
        Tuple (question_category, question_type, question_subtype, question_amount, topic_amount, difficulty):
        -question_category contains session question category
        -question_type contains session question type
        -question_subtype contains session question subtype or None if not applicable
        -question_amount contains amount of questions in session
        -topic_amount contains session topic amount or None if not applicable
        -difficulty contains session difficulty
    """

    while True:

        question_category = _select_question_format()

        question_type, question_subtype = _select_question_type(question_category)

        if not question_type and not question_subtype:
            continue
        break

    question_amount, topic_amount = _get_question_amount(question_type)

    difficulty = _question_difficulty()

    return question_category, question_type, question_subtype, question_amount, topic_amount, difficulty