
import logging
logger = logging.getLogger(__name__)

def extract_question_blocks(text: str) -> list[dict]:
    """Extract response data from a questions document

    Parses a questions document to retrieve each question and its topic

    Args:
        text: Question document text to parse
    Returns:
        A list of dicts containing question and its topic data for each question
    """

    current_field = None
    blocks = []
    current_block = {}
    lines = text.split("\n")

    for line in lines[1:]:
        stripped = line.strip()
        if stripped.startswith("Topic Title:"):
            current_field = None
            if current_block:
                blocks.append(current_block)
                current_block = {}
            topic = stripped.replace("Topic Title:", "").strip()
            current_block["topic"] = topic
        elif stripped.startswith("Question Difficulty:"):
            current_field = None
        elif stripped.startswith("Q:"):
            current_field = "question"
            question = stripped.replace("Q:", "").strip()
            current_block["question"] = question
        elif stripped.startswith("A:"):
            current_field = None
        elif current_field and stripped:
            current_block[current_field] += " " + stripped

    if current_block:
        blocks.append(current_block)

    if not blocks:
        logger.warning("extract_question_blocks returned no blocks; check input format")
    logger.debug(f"extract_question_blocks returned %s blocks", len(blocks))

    return blocks

def extract_response_blocks(text: str) -> list[dict]:
    """Extract response data from a graded document

    Parses a graded document to retrieve each question's response, grade, and explanation

    Args:
        text: Graded document text to parse
    Returns:
        A list of dicts containing response, grade, and explanation data for each question
    """

    current_field = None
    blocks = []
    current_block = {}
    lines = text.split("\n")

    for line in lines[3:]:
        stripped = line.strip()
        if stripped.startswith("Grading:"):
            current_field = None
        elif stripped.startswith("Topic Title:"):
            current_field = None
            if current_block:
                blocks.append(current_block)
                current_block = {}
        elif stripped.startswith("Question Difficulty:"):
            current_field = None
        elif stripped.startswith("A:"):
            current_field = "answer"
            answer = stripped.replace("A:", "").strip()
            if answer:
                current_block["answer"] = answer
        elif stripped.startswith("G:"):
            current_field = None
            grade = stripped.replace("G:", "").strip()
            current_block["grade"] = grade
        elif stripped.startswith("E:"):
            current_field = "explanation"
            explanation = stripped.replace("E:", "").strip()
            current_block["explanation"] = explanation  
        elif current_field and stripped:
            current_block[current_field] += " " + stripped

    if current_block:
        blocks.append(current_block)

    if not blocks:
        logger.warning("extract_response_blocks returned no blocks; check input format")
    logger.debug("extract_response_blocks returned %s blocks", len(blocks))

    return blocks