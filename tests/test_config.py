
import pytest
import config
import json
import os

config.run_config()

@pytest.fixture
def bad_json():
    original_content = None
    if os.path.exists(config.CONFIG_PATH):
        with open(config.CONFIG_PATH, "r") as f:
            original_content = f.read()
    yield
    if original_content is not None:
        with open(config.CONFIG_PATH, "w") as f:
            f.write(original_content)

@pytest.fixture
def no_json():
    original_content = None
    if os.path.exists(config.CONFIG_PATH):
        with open(config.CONFIG_PATH, "r") as f:
            original_content = f.read()
        os.remove(config.CONFIG_PATH)
    yield
    if original_content is not None:
        with open(config.CONFIG_PATH, "w") as f:
            f.write(original_content)

@pytest.fixture
def incorrect_json():
    original_content = None
    if os.path.exists(config.CONFIG_PATH):
        with open(config.CONFIG_PATH, "r") as f:
            original_content = f.read()
        outlandish_config = {
    "MAX_DOCUMENTS": "5000 bananas",
    "MAX_WEAK_TOPICS": 10000000000,
    "SESSIONS_PER_PAGE": -12,
    "FAVORITES_PER_PAGE": 25
    }
        with open(config.CONFIG_PATH, "w") as file:
                json.dump(outlandish_config, file)
    yield
    if original_content is not None:
        with open(config.CONFIG_PATH, "w") as f:
            f.write(original_content)

@pytest.fixture
def correct_json():
    if os.path.exists(config.CONFIG_PATH):
        with open(config.CONFIG_PATH, "r") as f:
            original_content = f.read()
    yield
    if original_content is not None:
        with open(config.CONFIG_PATH, "w") as f:
            f.write(original_content)

def test_config_types():
    assert isinstance(config.DEBUG_MODE, bool)
    assert isinstance(config.MAX_DOCUMENTS, int)
    assert isinstance(config.MAX_WEAK_TOPICS, int)
    assert isinstance(config.SESSIONS_PER_PAGE, int)
    assert isinstance(config.TEST_MODE, bool)
    assert isinstance(config.FAVORITES_PER_PAGE, int)

def test_config_values():
    assert config.LOG_FORMAT == "%(asctime)s %(levelname)s %(name)s — %(message)s"
    assert config.LOG_FILE == "./logs/sfk.log"
    assert config.MODEL == "gemini-3.5-flash"
    assert config.DB_PATH == "sfk.db"

def test_no_json(no_json):
    final_config = config.run_config() 
    assert final_config == {
    "MAX_DOCUMENTS": 5,
    "MAX_WEAK_TOPICS": 10,
    "SESSIONS_PER_PAGE": 10,
    "FAVORITES_PER_PAGE": 10
    }

def test_json_fallback(bad_json):
    with open(config.CONFIG_PATH, "w") as f:
        f.write("This is not json...")
    final_config = config.run_config() 
    assert final_config == {
    "MAX_DOCUMENTS": 5,
    "MAX_WEAK_TOPICS": 10,
    "SESSIONS_PER_PAGE": 10,
    "FAVORITES_PER_PAGE": 10
    }

def test_incorrect_json_values(incorrect_json):
    final_config = config.run_config() 
    assert final_config == {
    "MAX_DOCUMENTS": 5,
    "MAX_WEAK_TOPICS": 10,
    "SESSIONS_PER_PAGE": 10,
    "FAVORITES_PER_PAGE": 25
    }

def test_change_item(monkeypatch):
    setting = "Favorites Per Page"
    current_value = 10
    value_range = "1-50"
    monkeypatch.setattr("builtins.input", lambda _: "25")
    new_value = config._change_item(setting, current_value, value_range)
    assert new_value == 25
