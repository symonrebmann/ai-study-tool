
from client import client
import config
import logging
logger = logging.getLogger(__name__)
from datetime import datetime
from database import Database

from document_loader import get_session_sources
from ui_generate import get_question_info
from prompts import get_difficulty_prompt, get_instructions

def _generate_questions(notes: str, weak_topics: str, ai_weak_topic_text: str, question_amount: int, ai_instructions: str, essay_topic_instruction: str, question_difficulty_prompt: str) -> str:
    """Send session info to the AI model for creating questions

    Handles API errors with retry logic.
    
    Args:
        notes: Note document(s) used as information to generate questions from
        weak_topics: Weak topics ranked best to worst used to focus on weak points or empty str when not applicable
        ai_weak_topic_text: Used to tell AI to use weak topics or empty str when not applicable
        question_amount: Amount of questions for AI to generate
        ai_instructions: Instructions for the AI to use to generate the question type
        essay_topic_instruction: Instructions for essay topic chosen or empty str when not applicable
        question_difficulty_prompt: Instructions for AI to use to generate the session difficulty
    Returns:
        Full generated question document as a str
    """

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
                model = config.MODEL,
                contents = prompt
            )
            logger.debug("Prompt length: %s chars", len(prompt))
            return response.text
        except Exception as e:
            if "503" in str(e):
                logger.warning("Gemini is currently unavailable due to high demand. Please try again in a moment.")
            else:
                logger.error("Generation failed.", exc_info=True)
            retry = input("Would you like to try generating again? (y/n): ").strip().lower()
            if retry != 'y':
                raise RuntimeError("Question generation failed.") from e

def _prepare_generation_prompts(question_type: str, question_subtype: str | None, topic_amount: int | None, difficulty: int) -> tuple[str, str, str]:
    """Get AI instructions based on session info

    Args:
        question_type: Used to get AI question instructions if no subtype
        question_subtype: Used to get AI question instructions if subtype
        topic_amount: Used to get AI essay topic instructions if not None
        difficulty: Used to get AI difficulty instructions
    Returns:
        Tuples (essay_topic_instruction, ai_instructions, difficulty_prompt)
        -essay_topic_instruction contains instructions for essay topic chosen or empty str when not applicable
        -ai_instructions contains instructions for the AI to use to generate the question type
        -question_difficulty_prompt contains instructions for AI to use to generate the session difficulty
    """

    if not question_subtype:
        ai_instructions = get_instructions(question_type)
    else:
        ai_instructions = get_instructions(question_subtype)

    if not topic_amount:
        essay_topic_instruction = ""
    else:
        essay_topic_instruction = f"For each essay question give the choice of {topic_amount} different topic questions"

    difficulty_prompt = get_difficulty_prompt(difficulty)

    return essay_topic_instruction, ai_instructions, difficulty_prompt

def _create_questions_file(session_id: int, questions: str, all_subjects: list[str], today: str) -> None:
    """Create and save a question file for a study session

    Args:
        session_id: Unique ID of the study session
        questions: Generated questions to write to the file
        all_subjects: Subject(s) used when generating the filename
        today: Generation datetime included in the filename
    """
    header = f"Session ID: {session_id}\n\n"
    final_output = header + questions

    if len(all_subjects) > 1:
        subjects = " ".join(all_subjects) + " combined"
    else:
        subjects = all_subjects[0]

    try:
        with open(f"{subjects} questions {today}.txt", "w", encoding="utf-8") as f:
            f.write(final_output)
    except Exception as e:
        logger.critical("Unable to create questions file due to error %s", e, exc_info = True)
        exit()

    print(f"Questions saved to '{subjects} questions {today}.txt'")

def run_generate(db: Database) -> None:
    """Orchestrate generation of a study session from user input
    
    Collects the information needed to generate questions, saves the resulting session and questions to the database, and writes the generated questions to a file

    Args:
        db: Database instance used to store session data
    """

    today = datetime.now().strftime("%Y-%m-%d-%I-%M-%p")

    notes, weak_topics, ai_weak_topic_text, all_subjects = get_session_sources(db)

    question_category, question_type, question_subtype, question_amount, topic_amount, difficulty = get_question_info()

    essay_topic_instruction, ai_instructions, difficulty_prompt = _prepare_generation_prompts(question_type, question_subtype, topic_amount, difficulty)

    try:
        questions = _generate_questions(notes, weak_topics, ai_weak_topic_text, question_amount, ai_instructions, essay_topic_instruction, difficulty_prompt)
    except RuntimeError as e:
        logger.critical(e)
        raise

    session_id = db.insert_session(question_category, question_type, question_subtype, difficulty, today)
    db.insert_subjects(all_subjects, session_id)
    db.insert_questions(questions, session_id)

    _create_questions_file(session_id, questions, all_subjects, today)

if __name__ == "__main__":
    run_generate()