
def get_instructions(question_type: str) -> str:
    """Retrieve generation instructions for a specific question type
    
    Args:
        question_type: Used to select the appropriate instructions
    Returns:    
        Prompt instructions for generating questions of the specified type
    """

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

    ai_instructions = instructions[question_type]

    return ai_instructions

def get_difficulty_prompt(difficulty: int) -> str:
    """Retrieve generation instructions for a specific difficulty
    
    Args:
        difficulty: Used to select the appropriate instructions
    Returns:    
        Prompt instructions for generating questions of the specified difficulty
    """

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