
import re
import os
import logging
logger = logging.getLogger(__name__)
import pdfplumber
from PIL import Image, UnidentifiedImageError
from client import client
import config
from database import Database

_JUNK_TITLE_WORDS = {
    # General note types
    "note",
    "lecture",
    "lesson",
    "class",
    "course",
    "unit",
    "chapter",
    "section",
    "topic",
    "module",

    # Educational material
    "slide",
    "slideshow",
    "presentation",
    "ppt",
    "pptx",
    "pdf",
    "worksheet",
    "handout",
    "packet",
    "reading",
    "review",
    "study",
    "guide",
    "summary",
    "outline",
    "example",
    "practice",
    "exercise",
    "assignment",
    "homework",
    "lab",

    # Assessment
    "quiz",
    "exam",
    "test",
    "midterm",
    "final",

    # Generic descriptors
    "intro",
    "introduction",
    "overview",
    "basic",
    "fundamental",
    "advanced",
    "supplement",
    "appendix",
    "reference",

    # Organization
    "part",
    "week",
    "day",
    "session",
    "meeting",

    # Common numbering prefixes
    "ch",
    "chap",
    "sec",
    "lec",
    "wk",
    "pt",

    # Versions
    "draft",
    "copy",
    "update",
    "new",
    "old",
    "latest",
    "finalized",
    "edited",
    "complete",

    # File organization
    "school",
    "college",
    "university",
    "semester",
    "spring",
    "summer",
    "fall",
    "winter",

    # Common extras
    "and",
    "&",
    "the",
    "of",
    "for",
    "to",
    "in",
    "on",
}

_JUNK_TITLE_WORDS_EXPANDED = _JUNK_TITLE_WORDS | {_pluralize(w) for w in _JUNK_TITLE_WORDS}

def _pluralize(word: str) -> str:
    """Generate a naive plural form for junk-word matching"""
    if word.endswith(("s", "x", "ch", "sh")):
        return word + "es"
    elif word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
        return word[:-1] + "ies"
    else:
        return word + "s"

def _discover_documents() -> list[str]:
    """Discover notes documents from os
    
    Returns:
        List containing all found note document names
    """

    file_names = os.listdir(".")

    note_check = {"notes", "note", "chapter", "unit", "lecture", "textbook", "review", "summary", "study", "guide", "handout", "slides"}
    notes_documents = []

    for file in file_names:
        name_without_suffix = os.path.splitext(file)[0]
        file_name_parts = set(part.lower().strip() for part in re.split(r"[\s_.\-]+", name_without_suffix))
        if file_name_parts & note_check:
            notes_documents.append(file)
        
    return notes_documents

def _validate_manual_entry(filename: str) -> tuple[bool, str]:
    """Validate manual entry as an applicable file
    
    Args:
        filename: Manually entered file to validate
    Returns:
        Tuple of (is_valid, error_message) where is_valid is True if the file passes validation and error_message describes the failure or is empty on success
    """

    extension = os.path.splitext(filename)[1]
    if not extension in {".txt", ".pdf", ".png", ".jpg", ".jpeg"}:
        return False, f"Unsupported file type: {extension}"

    if os.path.dirname(filename) not in {"", "."}:
        return False, "Please enter only the filename, not a path"
    
    if not os.path.exists(filename):
        return False, f"File '{filename}' not found in current directory"

    if not os.access(filename, os.R_OK):
        return False, f"Cannot read '{filename}' — check permissions"

    return True, ""

def _input_document_choice(notes_documents: list[str]) -> tuple[str | None, str | None]:
    """Choose and validate a notes document
    
    Args:
        notes_documents: List containing all note documents
    Returns:
        Tuple of (filepath, name_without_suffix) where filepath directs to the file and name_without_suffix is the files name or returns (None, None) on failure
    """

    fail_manual_entry = 0

    notes_count = len(notes_documents)
    print("Notes documents: ")
    for i, note in enumerate(notes_documents, start = 1):
        print(f"{i}. {note}")
    print(f"{notes_count + 1}. Manual entry")

    try:
        notes_document = int(input("Please choose one of the above notes documents by entering the corresponding number (e.g. 1, 2, 3). "))
        if notes_document == notes_count + 1:
            while fail_manual_entry < 3:
                manual_entry = input("Please enter the full name of the notes document (including the extension): ")

                is_valid, error = _validate_manual_entry(manual_entry)
                
                if is_valid:
                    notes_documents.append(manual_entry)
                    name_without_suffix = os.path.splitext(manual_entry)[0]
                    return manual_entry, name_without_suffix
                else:
                    print(f"{error}. Please try again")
                    fail_manual_entry += 1
                    continue
            if fail_manual_entry >= 3:
                print("Too many failed attempts. Please try another notes document.")
                return None, None
        else:
            filepath = notes_documents[notes_document - 1]
            name_without_suffix = os.path.splitext(filepath)[0]
            return filepath, name_without_suffix
    except (ValueError, IndexError):
        print("The document chosen was not recognized. Please try again.")
        return None, None

def _read_document(filepath: str) -> tuple[str | None, str]:
    """Read the chosen notes document
    
    Args:
        filepath: Path to the file being read
    Returns:
        Tuple of (notes, error_message) where notes contains the file text and error_message is empty on success, or (None, error_message) on failure
    """

    extension = os.path.splitext(filepath)[1]

    if extension == ".txt":
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                notes = f.read()
            return notes, ""
        except (FileNotFoundError, OSError) as e:
            logger.warning("Failed to open document: %s", e)
            return None, "Notes extractions failed."
    elif extension == ".pdf":
        try:
            with pdfplumber.open(filepath) as pdf:
                notes = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        notes += text
            if not notes.strip():
                return None, "No text could be extracted from the PDF."
            else:
                return notes, ""
        except (FileNotFoundError, OSError) as e:
            logger.warning("Failed to open document: %s", e)
            return None, "Failed to extract notes from pdf."
    elif extension in {".png", ".jpg", ".jpeg"}:
        image_success = False
        while True:
            try:
                with Image.open(filepath) as image:
                    try:
                        response = client.models.generate_content(
                            model = config.MODEL,
                            contents = [image, "Extract all text from this image exactly as it appears. Return only the extracted text with no introduction, explanation, or commentary."]
                        )
                        notes = response.text
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
            except (FileNotFoundError, PermissionError, UnidentifiedImageError, OSError) as e:
                logger.warning("Failed to open document: %s", e)
                return None, "Couldn't extract notes."
        if image_success:
            return notes, ""
        else:
            return None, "Image extraction abandoned."
    else:
        return None, f"Unsupported file type: {extension}"

def _get_subject(name: str) -> str:
    """Extract the subject of the notes document
    
    Args:
        name: Name of the chosen notes document
    Returns:
        Filtered subject or "Unknown" when it fails
    """

    parts = re.split(r"[\s_.\-()]+", name)

    filtered = []

    for part in parts:

        if not part:
            continue

        part = part.lower()

        if part in _JUNK_TITLE_WORDS_EXPANDED:
            continue

        if part.isdigit():
            continue

        if re.fullmatch(r"(ch|chap|sec|lec|wk|pt|v)\d+", part):
            continue

        if re.fullmatch(r"[ivxlcdm]+", part):
            continue

        if re.fullmatch(r"\d{4}", part):
            continue

        filtered.append(part)

    return " ".join(filtered).strip() or "Unknown"

def _get_weak_topics(db: Database, subject: str, topic_groups: dict[str, list[dict[str, str | float]]] | None) -> dict[str, list[dict[str, str | float]]]:
    """Fetch the weak topics and format into a dict
    
    Args:
        db: Database instance used to fetch weak topics
        subject: Subject of the notes used to find weak topics
        topic_groups: Dict containing the topics in a subject and a list of the scores and grades for those topics or none if it hasn't been created yet
    Returns:
        Dict containing the topics in a subject and a list of the scores and grades for those topics
    """

    rows = db.fetch_weak_topics(subject)

    if not rows:
        print("Could not retrieve weak topics due to a local database issue.")
        print("Proceeding.")
        return topic_groups

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
    
    return topic_groups

def _more_documents() -> bool:
    """Prompt user and handle more note documents
    
    Returns:
        Bool containing True for yes and False for no
    """

    more_notes_fail = 0

    while more_notes_fail < 3:
        more = input("Would you like to add another document? (y/n): ").strip().lower()
        if more == "n":
            return False
        elif more == "y":
            return True
        else:
            print("Invalid response. Please input a valid response (y/n).")
            more_notes_fail += 1
    if more_notes_fail >= 3:
        print("Too many failed attempts. Proceeding with current documents. ")
        return False

def _aggregate_weak_topics(topic_groups: dict[str, list[dict[str, str | float]]]) -> str:
    """Calculate weak topic averages and sort by weakest
    
    Args:
        topic_groups: Dict containing the topics in a subject and a list of the scores and grades for those topics
    Returns:
        String containing up to MAX_WEAK_TOPICS topics sorted weakest to strongest
    """

    topic_averages = []

    if not topic_groups:
        return ""

    for topic, records in topic_groups.items():
        avg = sum(r["score"] for r in records) / len(records)
        topic_averages.append((topic, avg))

    topic_averages.sort(key=lambda x: x[1])
    weak_topics_unformatted = [topic for topic, _ in topic_averages[:config.MAX_WEAK_TOPICS]]
    weak_topics = "\n".join(f"- {topic}" for topic in weak_topics_unformatted)

    return weak_topics

def get_session_sources(db: Database) -> tuple[str, str, str, list[str]]:
    """Orchestrate the calling of required functions to get note(s) and weak topics
    
    Args:
        db: Database instance used to pass into required functions
    Returns:
        Tuple of (notes, weak_topics, ai_weak_topic_text, all_subjects) where:
        -notes contains the combined text of all note documents
        -weak_topics is a str of topics sorted weakest to strongest
        -ai_weak_topic_text is the formatted prompt addition for weak topics
        -all_subjects is a list of subject names for the session
    """

    notes_documents = _discover_documents()

    topic_groups = {}

    all_notes = []
    all_subjects = []

    for _ in range(config.MAX_DOCUMENTS):
        fail_count_notes_document = 0
        fail_count_read_document = 0

        notes = None
        name_without_suffix = None
    
        while fail_count_notes_document < 3 and fail_count_read_document < 3:

            result = _input_document_choice(notes_documents)

            if result == (None, None):
                fail_count_notes_document +=1
                continue
            
            filepath, name_without_suffix = result

            notes, error = _read_document(filepath)

            if notes is None:
                fail_count_read_document += 1
                print(f"{error} Please try another document.")
                continue
            break
        if fail_count_notes_document >= 3 or fail_count_read_document >= 3:
            print("Too many failed attempts. Exiting.")
            exit()

        all_notes.append(notes)

        subject = _get_subject(name_without_suffix)

        if subject == "Unknown":
            print("Subject could not be found from title.")
            while True:
                subject = input("Please input a subject for your session: ").lower().strip()
                if not subject:
                    print("Please enter a subject. Not doing so can only hurt your progress.")
                    continue
                else:
                    break
        if subject not in all_subjects:
            all_subjects.append(subject)

            fail_count_weak_focus = 0

            while fail_count_weak_focus < 3:
                question_weak_focus = input("Focus on weak topics for this document? (y/n): ").strip().lower()
                if question_weak_focus == "y":
                    topic_groups = _get_weak_topics(db, subject, topic_groups)
                    break
                elif question_weak_focus == "n":
                    break
                else:
                    print("Invalid response. Please input a valid response (y/n).")
                    fail_count_weak_focus += 1
            if fail_count_weak_focus >= 3:
                print("Too many failed attempts. Proceeding.")

        more_notes = _more_documents()

        if not more_notes:
            break
        else: 
            continue
    
    if topic_groups:
        weak_topics = _aggregate_weak_topics(topic_groups)
        ai_weak_topic_text = "Weak Topics: "
    else:
        weak_topics = ""
        ai_weak_topic_text = ""

    notes = "\n\n".join(all_notes)

    return notes, weak_topics, ai_weak_topic_text, all_subjects