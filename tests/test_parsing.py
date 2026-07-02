
import pytest
from parsing import extract_question_blocks, extract_response_blocks

def test_extract_question_blocks(sample_questions_text):
    blocks = extract_question_blocks(sample_questions_text)
    assert len(blocks) == 5
    for block in blocks:
        assert len(block) == 2
    assert blocks[0]["topic"] == "Slope-Intercept Form Equation" #topic
    assert blocks[0]["question"] == "What is the standard slope-intercept form of a linear equation? A) y = mx + b B) y = x^2 C) a^2 + b^2 = c^2 D) E = mc^2" #question

def test_extract_response_blocks(sample_responses_text):
    blocks = extract_response_blocks(sample_responses_text)
    assert len(blocks) == 5
    for block in blocks:
        assert len(block) == 3
    assert blocks[0]["answer"] == "Im going to say the correct answer is.......... A" #answer
    assert blocks[0]["grade"] == "Correct" #grade
    assert blocks[0]["explanation"] == "The student chose option A. The standard slope-intercept form of a linear equation is indeed y = mx + b, where 'm' represents the slope and 'b' represents the y-intercept." #explanation