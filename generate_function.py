
import os
from datetime import datetime
from database import Database
import pdfplumber
import PIL.Image

import logging
logger = logging.getLogger(__name__)

from client import client
from config import MODEL, MAX_DOCUMENTS, MAX_WEAK_TOPICS

def generate_questions(notes: str, weak_topics: str, ai_weak_topic_text: str, question_amount: int, ai_instructions: str, essay_topic_instruction: str | None, question_difficulty_prompt: str) -> str:
    prompt = f"""
    You are a study assistant. Based on these notes-and if there are any weak topics-generate {question_amount} practice questions. You must generate exactly {question_amount} questions. No more, no less. {essay_topic_instruction}
    {ai_instructions}
    Please write the questions to these difficulty specifications. {question_difficulty_prompt}
    STRICT ENFORCEMENT:
    You must strictly follow the Core Rule for Question Type. Do NOT generate any question formats 
    mentioned in the Difficulty Level Rule if they contradict the requested format. For example, if the 
    Question Type is 'Problem-Solving', do NOT under any circumstances generate Multiple Choice, 
    True/False, or Matching questions, even if they are mentioned in the difficulty description.
    For each question, and provide a space for answering but do not include the answer.
    Start directly with topic title listing all covered topics separated by commas in the order of which they are asked in each question at the top of your response. Topic names must be short—a maximum of 5 words. Do not combine multiple topics (such as x and z) as one topic.
    As well, include the topic title directly above each question. When listing the topic above each question JUST list that question's topic. The Topic Title above each question must contain exactly one topic with no commas.
    As well, please list the question difficulty above each question a shown in the example below.
    The parts in brackets such as "[topic]," "[difficulty]," "[question]," and "[answer space]" are place holders. Replace those with the relevant information and DONT leave the brackets.
    Do NOT include any extra introduction, explanation, or information other than what's listed.
    Format each one as:
    Topic Title: [topic]
    Question Difficulty: [difficulty]
    Q: [question]
    A: [answer space]
    And, remember to keep it in a format that's understandable in a Microsoft notepad document.
    Notes:
    {notes}
    {ai_weak_topic_text}
    {weak_topics}
    """

    while True:
        try:
            response = client.models.generate_content(
                model = MODEL,
                contents = prompt
            )
            logger.debug("Prompt length: %s chars", len(prompt))
            return response
        except Exception as e:
            if "503" in str(e):
                logger.warning("Gemini is currently unavailable due to high demand. Please try again in a moment.")
            else:
                logger.error("Generation failed.", exc_info=True)
            retry = input("Would you like to try generating again? (y/n): ").strip().lower()
            if retry != 'y':
                print("Exiting application.")
                exit()

def get_question_type() -> tuple[str, str | None, str]:

    question_format_dict = {
        "1": ["1. Analogy", "2. Categorization/Sorting", "3. Cause and Effect", "4. Error Identification", "5. Interpretation", "6. Prediction", "7. Back"],
        "2": {
            "1. Essay": ["1. Argumentative", "2. Compare and Contrast", "3. Expository", "4. Narrative", "5. Persuasive", "6. Reflective", "7. Back"],
            "2. Free Response": ["1. Analyze", "2. Describe", "3. Discuss", "4. Evaluate", "5. Outline", "6. Summarize", "7. Back"],
            "3. Peer Review": [],
            "4. Research/Find": [],
            "5. Scenario/Case Study": [],
            "6. Back": []
            },
        "3": ["1. Matching", "2. Multiple Choice", "3. Multiple-select", "4. Ordering/Sequencing", "5. True/False", "6. Back"],
        "4": ["1. Classify", "2. Define", "3. Fill in the Blank", "4. Identify", "5. Numerical Response", "6. Passage Completion", "7. Short Answer", "8. Back"],
        "5": ["1. Code Writing/Debugging", "2. Derivation", "3. Problem-Solving", "4. Proof", "5. Back"]
        }


    while True:
        fail_count_question_type = 0
        while True:
            print("""Question Formats:
1. Analytical:
2. Extended Written Response:
3. Selected Response:
4. Short Written Response:
5. STEM-Specific:""")
            question_format = input("Please choose one of the above question formats by entering the corresponding number (e.g. 1, 2, 3). ").strip()
            if question_format in question_format_dict:
                break
            else:
                fail_count_question_type += 1
                print("The question format chosen was not recognized. Please try again.")
                if fail_count_question_type >= 3:
                    print("Too many failed attempts. Exiting.")
                    exit()

        fail_count_question_type = 0
        if question_format == "1":
            question_category = "Analytical"
        elif question_format == "2":
            question_category = "Extended Written Response"
        elif question_format == "3":
            question_category = "Selected Response"
        elif question_format == "4":
            question_category = "Short Written Response"
        elif question_format == "5":
            question_category = "STEM-Specific"
        else:
            question_category = None

        while True:
            print("Question Types:")
            content = question_format_dict[question_format]
            if isinstance(content, list):
                print("\n".join(content))
            elif isinstance(content, dict):
                print("\n".join(content.keys()))
            try:
                response_type = int(input("Please choose one of the above question types by entering the corresponding number (e.g. 1, 2, 3). ").strip())
                if isinstance(content, list):
                    question_type = content[response_type - 1]
                    if question_type.split(".")[1].strip() == "Back":
                        break
                    return get_instructions(question_type), question_category, question_type
                elif isinstance(content, dict):
                    keys = list(content.keys())
                    if response_type == 1:
                        print("Question subtypes:")
                        print("\n".join(content["1. Essay"]))
                        response_subtype = int(input("Please choose one of the above question subtypes by entering the corresponding number (e.g. 1, 2, 3). ").strip())
                        question_type = content["1. Essay"][response_subtype - 1]
                        if question_type.split(".")[1].strip() == "Back":
                            continue
                        question_category = "Essay"
                        return get_instructions(question_type), question_category, question_type
                    elif response_type == 2:
                        print("Question subtypes:")
                        print("\n".join(content["2. Free Response"]))
                        response_subtype = int(input("Please choose one of the above question subtypes by entering the corresponding number (e.g. 1, 2, 3). ").strip())
                        question_type = content["2. Free Response"][response_subtype - 1]
                        if question_type.split(".")[1].strip() == "Back":
                            continue
                        question_category = "Free Response"
                        return get_instructions(question_type), question_category, question_type
                    elif response_type == 3:
                        question_type = "3. Peer Review"
                        return get_instructions(question_type), question_category, question_type
                    elif response_type == 4:
                        question_type = "4. Research/Find"
                        return get_instructions(question_type), question_category, question_type
                    elif response_type == 5:
                        question_type = "5. Scenario/Case Study"
                        return get_instructions(question_type), question_category, question_type
                    elif keys[response_type - 1].split(".")[1].strip() == "Back":
                        break
                    else:
                        print("The question type chosen was not recognized. Please try again.")
                        fail_count_question_type += 1
            except (ValueError, IndexError):
                print("The question type chosen was not recognized. Please try again.")
                fail_count_question_type += 1
            if fail_count_question_type >= 3:
                print("Too many failed attempts. Exiting.")
                exit()
    

def get_instructions(question_type: str) -> str:
    
    instructions = {
    "Analogy": "Please generate all the questions in an analogy format. Present a relationship between two concepts (from the notes) and ask the student to identify or complete a similar relationship.",
    "Analyze": "Please generate all the questions in the form of a free response question that asks the student to analyze the content of a excerpt, writing, data, etc. to answer a question.",
    "Argumentative": "Please generate all the questions in the form of an argumentative essay prompt.",
    "Categorization/Sorting": "Please generate all the questions in a categorization/sorting format. Provide a list of items and ask the student to sort or categorize them. Make the number of items to sort/categorize equal to the total number of questions. Make sure the unsorted provided list is in a randomized order.",
    "Cause and Effect": "Please generate all the questions in a cause and effect format.",
    "Classify": "Please generate all the questions in a short response format that asks the student to classify a work, essay, data, etc.",
    "Code Writing/Debugging": "Please generate all the questions in a format that asks the student to alternate between writing code for an objective and debugging code to allow something to happen.",
    "Compare and Contrast": "Please generate all the questions in the form of an essay prompt that asks the student to compare and contrast topics.",
    "Define": "Please generate all the questions in a short response format that asks the student to define a term, concept, word, etc.",
    "Derivation": "Please generate all the questions in a format that asks the student to derive an equation based on given equations. Please supply the relevant equations, but not all given equations need to be used in the derivation.",
    "Describe": "Please generate all the questions in a in the form of a free response question that asks the student to describe the content of a excerpt, writing, data, etc.",
    "Discuss": "Please generate all the questions in a in the form of a free response question that asks the student to discuss the content of a excerpt, writing, data, etc.",
    "Error Identification": "Please generate all the questions in an error identification format. Please create a passage, situation, calculation, etc. that has an error within it. Then ask the student to find the error.",
    "Evaluate": "Please generate all the questions in a in the form of a free response question that asks the student to evaluate the content of a excerpt, writing, data, etc.",
    "Expository": "Please generate all the questions in the form of an essay prompt that asks the student to write an expository essay.",
    "Fill in the Blank": "Please generate all the questions in a fill-in-the-blank format.",
    "Identify": "Please generate all the questions in a short response format that asks the student to identify an aspect about a work, essay, data, etc.",
    "Interpretation": "Please generate all the questions in a interpretation format. Give a calculation, situation, passage, etc. and ask the student to interpret it.",
    "Matching": "Please generate all the questions in a matching format with the number of options equal to the number of questions. Each question should have a corresponding answer that can be matched. Make sure the matched provided list is in a randomized order.",
    "Multiple Choice": "Please generate all the questions in a multiple choice format with 4 options (A, B, C, D) for each question.",
    "Multiple-select": "Please generate all the questions in a multiple-select format with 4-6 options for each question (with the number of correct answers ranging from 1 to all per question).",
    "Narrative": "Please generate all the questions in the form of an essay prompt that asks the student to write a narrative essay.",
    "Numerical Response": "Please generate all the questions in a numeric response format where the student answers a question with a numeric response.",
    "Ordering/Sequencing": "Please generate all the questions in an ordering/sequencing format. Make sure the unordered provided list is in a randomized order.",
    "Outline": "Please generate all the questions in a in the form of a free response question that asks the student to outline the content of a excerpt, writing, data, etc.",
    "Passage Completion": "Please generate all the questions in a short response that asks the student to complete a passage.",
    "Peer Review": "Please generate all the questions in the form of a extended response question that asks the student to peer-review an essay, paragraph, experiment, etc. that you generate. Ensure the provided work has areas for improvement for the student to identify and comment on.",
    "Persuasive": "Please generate all the questions in the form of an essay prompt that asks the student to write a persuasive essay.",
    "Prediction": "Please generate all the questions in a prediction format. Give a calculation, situation, passage, etc. and ask the student to predict an outcome based upon it.",
    "Problem-Solving": "Please generate all the questions in a format that asks the student to solve a problem related to the notes. Each problem should have a clear, definitive answer.",
    "Proof": "Please generate all the questions in the form of a mathematical, scientific, or logical proof.",
    "Research/Find": "Please generate all the questions in the form of an extended response question that asks the student to research and write about a topic or to find information about a topic that is closely related to the notes but not contained within.",
    "Reflective": "Please generate all the questions in the form of an essay prompt that asks the student to reflect on their understanding of the topic. Ask them to discuss what they know well, what they find challenging, how their understanding has evolved, and what they would want to explore further.",
    "Scenario/Case Study": "Please generate all the questions in the form of an extended response question that asks the student to analyze or respond to a scenario or case study that you provide.",
    "Short Answer": "Please generate all the questions in a short answer format. The question should require at most a paragraph of writing.",
    "Summarize": "Please generate all the questions in a in the form of a free response question that asks the student to summarize the content of a excerpt, writing, data, etc.",
    "True/False": "Please generate all the questions in a true/false format."
    }

    fixed_question_type = question_type.split(".")[1].strip()

    ai_instructions = instructions[fixed_question_type]

    return ai_instructions

def get_question_amount(question_category: str | None) -> tuple[int, int | None, str]:
    
    fail_count_question_amount = 0

    topic_amount = None

    while fail_count_question_amount < 3:
        if question_category == "Essay":
            try:
                question_amount = int(input("How many questions would you like? "))
                topic_amount = int(input("How many essay topics would you like to be able to choose from (per question)? "))
                if question_amount > 5:
                    print("Error: Too many questions. Please try an amount 5 or under.")
                    fail_count_question_amount += 1
                elif question_amount <= 0 or topic_amount <= 0:
                    print("Error: Please enter a positive integer.")
                    fail_count_question_amount += 1
                elif topic_amount > 5:
                    print("Error: Too many topics. Please try an amount 5 or under.")
                    fail_count_question_amount += 1
                else:                    
                    break
            except ValueError:
                print("Error: Please enter a valid integer.")
                fail_count_question_amount += 1   
        elif question_category == "Free Response":
            try:
                question_amount = int(input("How many questions would you like? "))
                if question_amount > 10:
                    print("Error: Too many questions. Please try an amount 10 or under.")
                    fail_count_question_amount += 1
                elif question_amount <= 0:
                    print("Error: Please enter a positive integer.")
                    fail_count_question_amount += 1
                else:                    
                    break
            except ValueError:
                print("Error: Please enter a valid integer.")
                fail_count_question_amount += 1   
        else:
            try:
                question_amount = int(input("How many questions would you like? "))
                if question_amount > 25:
                    print("Error: Too many questions. Please try an amount 25 or under.")
                    fail_count_question_amount += 1
                elif question_amount <= 0:
                    print("Error: Please enter a positive integer.")
                    fail_count_question_amount += 1
                else:                    
                    break
            except ValueError:
                print("Error: Please enter a valid integer.")
                fail_count_question_amount += 1   
    if fail_count_question_amount >= 3:
        print("Too many failed attempts. Exiting.")
        exit()

    return question_amount, topic_amount

def question_difficulty() -> tuple[str, int]:
    fail = 0
    while fail < 3:
        try:
            difficulty = int(input("Please choose a difficulty 1-10: ").strip())
            if difficulty > 10:
                print("Please enter a number 1-10")
                fail += 1
            elif difficulty < 1:
                print("Please enter a number 1-10")
                fail += 1
            else:
                fail_2 = 0
                while fail_2 < 3:
                    diff_confirm = input(f"Are you sure you want a difficulty of {difficulty}/10? (y/n): ").strip().lower()
                    if diff_confirm == "y":
                        return get_difficulty_prompt(difficulty), difficulty
                    if diff_confirm == "n":
                        break
                    else:
                        print("Please choose y/n.")
                        fail_2 += 1
                        continue
                if fail_2 >= 3:
                    print("Too many failed attempts. Exiting.")
                    exit()
        except (ValueError, IndexError):
            print("Error: Please enter a valid integer.")
            fail += 1
    if fail >= 3:
        print("Too many failed attempts. Exiting.")
        exit()
    
def get_difficulty_prompt(difficulty: int) -> str:
    difficulty_modifiers = {
    "1": """Pure surface-level recall. For objective formats (MCQ, T/F, Matching),
the correct choice must be blindingly obvious. For open-ended formats (Essays, Proofs, Code),
the prompt must only require stating a basic definition or flat fact with zero analytical effort.""",

    "2": """Simple recognition. For objective formats (MCQ, T/F, Matching), the
incorrect options/distractors should be easily ruled out. For open-ended formats (Essays, Proofs, Code),
the prompt must only require identifying basic concepts or restating a clearly defined
relationship directly from the notes or prompt.""",

    "3": """Basic comprehension. For objective formats (MCQ, T/F, Matching), it should require
straightforward information retrieval and easy-to-remove incorrect options/distractors. For open-ended
formats (Essays, Proofs, Code), the prompt should require a simple step of information retrieval or
minor connection-making (e.g., identifying a straightforward example of a concept or
writing a single line of basic code).""",

    "4": """Routine application. For objective formats (MCQ, T/F, Matching), distractors should
look plausible but remain easy to filter for a student who knows the basics. For open-ended formats
(Essays, Proofs, Code), the prompt should require applying a standard rule, a basic formula, or
summarizing a foundational concept without deep interpretation.""",

    "5": """Moderate analytical difficulty. For objective formats (MCQ, T/F, Matching), at least
two distractors should require close reading to differentiate from the correct answer. For open-ended
formats (Essays, Proofs, Code), the prompt should require explaining the logic behind a concept,
comparing two simple variables, or writing a basic multi-step paragraph or function.""",

    "6": """Deeper analysis. For objective formats (MCQ, T/F, Matching), distractors should include
common misconceptions or slight variations in data. For open-ended formats (Essays, Proofs, Code),
the prompt should require the student to analyze patterns, categorize items with overlapping traits,
or explain how multiple distinct components interact.""",

    "7": """High difficulty and synthesis. For objective formats (MCQ, T/F, Matching), options must
test for edge cases, requiring precise knowledge to eliminate wrong answers. For open-ended formats
(Essays, Proofs, Code), the prompt must require the student to justify an answer with strong evidence,
predict outcomes when variables change, or critique a specific viewpoint.""",

    "8": """Advanced critical thinking. For objective formats (MCQ, T/F, Matching), multiple choices
should seem correct at first glance, requiring multi-layered reasoning to solve. For open-ended formats
(Essays, Proofs, Code), the prompt must require handling complex hypothetical scenarios, debugging
intricate multi-line logic, or deriving connections not explicitly stated in the source text.""",

    "9": """High-level evaluation. For objective formats (MCQ, T/F, Matching), options must feature
highly nuanced, close-call terminology requiring exact conceptual precision. For open-ended formats
(Essays, Proofs, Code), the prompt must force the student to evaluate competing academic arguments,
defend highly complex positions, or construct multi-stage proofs.""",

    "10": """Maximum cognitive workload. For objective formats (MCQ, T/F, Matching), the questions
and options must be deeply nuanced, requiring the student to identify subtle exceptions or abstract rules.
For open-ended formats (Essays, Proofs, Code), the prompt must demand elite critical thinking, forcing
the student to reconcile apparent contradictions or solve highly complex, abstract problems from scratch."""
}
    difficulty_prompt = difficulty_modifiers[str(difficulty)]

    return difficulty_prompt

def get_notes_document(db: Database) -> tuple[str, str, str, list[str]]:

    topic_groups = {}
    topic_averages = []

    all_notes = []
    all_subjects = []

    file_names = os.listdir(".")

    note_check = {"notes", "note", "chapter", "unit", "lecture", "textbook", "review", "summary", "study", "guide", "handout", "slides"}
    notes_documents = []

    for file in file_names:
        name_without_suffix = os.path.splitext(file)[0]
        file_name_parts = set(part.lower().strip() for part in name_without_suffix.split(" "))
        if len(list(file_name_parts & note_check)) >= 1:
            notes_documents.append(file)

    for _ in range(MAX_DOCUMENTS):
        fail_count_notes_document = 0
        fail_count_read_document = 0
        fail_manual_entry = 0

        notes = None
        name_without_suffix = None
        extension = None
    
        while fail_count_notes_document < 3 and fail_count_read_document < 3:
            notes_index = 0
            print("Notes documents: ")
            for note in notes_documents:
                notes_index +=1
                print(f"{notes_index}. {note}")
            print(f"{notes_index + 1}. Manual entry")

            try:
                notes_document = int(input("Please choose one of the above notes documents by entering the corresponding number (e.g. 1, 2, 3). "))
                if notes_document == notes_index + 1:
                    while fail_manual_entry < 3:
                        manual_entry = input("Please enter the full name of the notes document (including the extension): ")
                        name_without_suffix = os.path.splitext(manual_entry)[0]
                        extension = os.path.splitext(manual_entry)[1]
                        if extension in {".txt", ".pdf", ".png", ".jpg", ".jpeg"}:
                            notes_documents.append(manual_entry)
                            break
                        else:
                            print("The file was not recognized. Please try again.")
                            fail_manual_entry += 1
                            continue
                    if fail_manual_entry >= 3:
                        print("Too many failed attempts. Please try another notes document.")
                        continue
                else:
                    name_without_suffix = os.path.splitext(notes_documents[notes_document - 1])[0]
                    extension = os.path.splitext(notes_documents[notes_document - 1])[1]
            except (ValueError, IndexError):
                print("The document chosen was not recognized. Please try again.")
                fail_count_notes_document +=1
                continue
            try:
                if extension == ".txt":
                    try:
                        with open(f"{notes_documents[notes_document - 1]}", "r") as f:
                            notes = f.read()
                        break
                    except (FileNotFoundError, OSError) as e:
                        logger.warning("Failed to open document: %s", e)
                        print("Notes extractions failed. Please try another notes document.")
                        fail_count_read_document += 1
                elif extension == ".pdf":
                    try:
                        with pdfplumber.open(notes_documents[notes_document - 1]) as pdf:
                            notes = ""
                            for page in pdf.pages:
                                notes += page.extract_text()
                        break
                    except (FileNotFoundError, OSError) as e:
                        logger.warning("Failed to open document: %s", e)
                        print("Notes extractions failed. Please try another notes document.")
                        fail_count_read_document += 1
                elif extension in {".png", ".jpg", ".jpeg"}:
                    while True:
                        try:
                            image = PIL.Image.open(notes_documents[notes_document - 1])
                            try:
                                response = client.models.generate_content(
                                    model = MODEL,
                                    contents = [image, "Extract all text from this image exactly as it appears. Return only the extracted text with no introduction, explanation, or commentary."]
                                )
                                notes = response
                                image_success = True
                                break
                            except Exception as e:
                                if "503" in str(e):
                                    logger.warning("Gemini is currently unavailable due to high demand. Please try again in a moment.")
                                else:
                                    logger.error("Generation failed.", exc_info=True)
                                retry = input("Would you like to try extracting the notes again? (y/n): ").strip().lower()
                                if retry == "n":
                                    break
                        except Exception:
                            print("Notes extractions failed. Please try another notes document.")
                            fail_count_read_document += 1
                            break
                    if image_success:
                        break
                    else:
                        continue
            except FileNotFoundError:
                print(f"Error: '{notes_document}.txt' not found. Please try again.")
                fail_count_read_document += 1   
        if fail_count_notes_document >= 3 or fail_count_read_document >= 3:
            print("Too many failed attempts. Exiting.")
            exit()
        if notes is None or name_without_suffix is None:
            print("Too many failed attempts. Exiting.")
            exit()

        all_notes.append(notes)

        file_name_parts = name_without_suffix.split(" ")
        filtered_parts = [part for part in file_name_parts if part.strip().lower() not in note_check]
        subject = " ".join(filtered_parts).strip()

        if subject in all_subjects:
            continue
        else:
            all_subjects.append(subject)

            fail_count_weak_focus = 0

            while fail_count_weak_focus < 3:
                question_weak_focus = input("Focus on weak topics? (y/n): ").strip().lower()
                if question_weak_focus == "y":
                    ai_weak_topic_text = "Weak Topics: "
                    
                    rows = db.fetch_weak_topics(subject)

                    if not rows:
                        print("Could not retrieve weak topics due to a local database issue.")
                        print("Proceeding.")
                        weak_topics = []
                        ai_weak_topic_text = ""
                        continue

                    for row in rows:
                        topic = row[0]
                        grade = row[1]

                        if grade == "Correct":
                            score = 1.0
                        elif grade == "Partially Correct":
                            score = .5
                        else:
                            score = 0.0
                            
                        if topic not in topic_groups:
                            topic_groups[topic] = []
                        topic_groups[topic].append({
                                "grade": grade,
                                "score": score
                        })
                    break
                elif question_weak_focus == "n":
                    weak_topics = []
                    ai_weak_topic_text = ""
                    break
                else:
                    print("Invalid response. Please input a valid response (y/n).")
                    fail_count_weak_focus += 1
            if fail_count_weak_focus >= 3:
                print("Too many failed attempts. Exiting.")
                exit()
        
        more_notes_fail = 0

        more_notes = input("Would you like to add another document? (y/n): ").strip().lower()
        while more_notes_fail < 3:
            if more_notes == "n":
                more_notes_final = False
                break
            elif more_notes == "y":
                more_notes_final = True
                break
            else:
                print("Invalid response. Please input a valid response (y/n).")
                more_notes_fail += 1
        
        if more_notes_final is False:
            break
        else: 
            continue
            
    for topic, records in topic_groups.items():
        avg = sum(r["score"] for r in records) / len(records)
        topic_averages.append((topic, avg))

    topic_averages.sort(key=lambda x: x[1])
    weak_topics_unformatted = [topic for topic, _ in topic_averages[:MAX_WEAK_TOPICS]]
    weak_topics = "\n".join(f"- {topic}" for topic in weak_topics_unformatted)

    notes = "\n\n".join(all_notes)

    return notes, weak_topics, ai_weak_topic_text, all_subjects

def run_generate(db: Database) -> None:

    today = datetime.now().strftime("%Y-%m-%d-%I-%M-%p")

    notes, weak_topics, ai_weak_topic_text, all_subjects = get_notes_document(db)

    ai_instructions, question_category, question_type = get_question_type() 

    question_amount, topic_amount = get_question_amount(question_category)
    question_difficulty_prompt, difficulty = question_difficulty()

    if topic_amount is None:
        essay_topic_instruction = None
    else:
        essay_topic_instruction = f"For each essay question give the choice of {topic_amount} different topic questions"

    questions: str = generate_questions(notes, weak_topics, ai_weak_topic_text, question_amount, ai_instructions, essay_topic_instruction, question_difficulty_prompt)
    
    if questions is None:
            print("Questions failed to generate. Please retry.")
            exit()

    session_id = db.insert_session(question_category, question_type, difficulty, today)
    db.insert_subjects(all_subjects, session_id)
    db.insert_questions(questions, session_id)

    header = f"Session ID: {session_id}\n\n"
    final_output = header + questions

    if len(all_subjects) > 1:
        subjects = " ".join(all_subjects) + " combined"
    else:
        subjects = all_subjects[0]

    with open(f"{subjects} questions {today}.txt", "w") as f:
        f.write(final_output)
    print(f"Questions saved to '{subjects} questions {today}.txt'")

if __name__ == "__main__":
    run_generate()