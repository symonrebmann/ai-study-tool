# SFK — Strive For Knowledge

SFK (Strive For Knowledge) is an AI-powered study assistant built in Python that turns personal notes into targeted practice sessions. It generates questions, evaluates responses, tracks performance over time, and identifies weak areas for focused review.

Built with the Gemini API and a SQLite-backed analytics pipeline, and backed by a tested, CI-verified pipeline, SFK is designed as an end-to-end learning system with persistent, long-term performance tracking.

## Tech Stack

- Language: Python
- AI: Google Gemini API
- Database: SQLite
- Testing: 42+ test pytest suite
- CI: GitHub Actions (test suite runs on every push to main)
- Config: JSON-based, with type/range validation and fallback defaults

## Features:

- Multi-source ingestion — Notes can be text files, PDFs, and images; with the ability to combine multiple documents for richer context
- Auto-detection — Auto-detects notes and generated files, with manual entry always available
- 37 question formats — Analytical, written response, selected response, and STEM-focused formats, with difficulty scaling from 1–10
- Weak topic targeting — Optionally pull your 10 weakest topics from past performance to focus generation where you need it most
- AI-powered grading — Detailed feedback and explanations on every answer
- Performance analytics — Topic weakness ranking, trend detection, and weighted averages
- Session history — Review of past sessions; option to review full question, answer, and grade detail
- Persistent session database — Stores every question, answer, grade, and explanation across all sessions for long-term tracking and review
- Favorites — Save, edit, review, and remove favorited questions, with paginated browsing
- Configurable settings — JSON-backed configuration with runtime editing through the menu

## Engineering

- Dependency-injected `Database` class, tested in-memory via SQLite
- 42+ tests across database, parsing, analytics, config, and integration
- GitHub Actions CI running the full suite on every push to main
- Centralized error handling in the database layer via `critical_handler` / `error_handler` decorators
- Named per-module logging

## Setup & Usage:

  You first need to install the required libraries. You can do this by running the following in your terminal:
	```
	pip install -r requirements.txt
	```
  You will then need to create an environmental variable. You can do this by creating a text document titled .env (you can have the .txt extension) in the folder. Then, in the text document, type "GEMINI_API_KEY=[your Gemini key]."

  Finally, in your terminal, run: "python menu.py". From there, you will be asked if you'd like to generate questions, grade your answers, generate analytics, or view session history.

  For note files, please keep the format somewhat simple using the format including just the subject and keywords like "notes, unit, chapter, textbook, slides" and similar keywords. As well, do not change the name of the generated questions documents; grading auto-detection relies on it (or else you'd have to use manual entry). Finally, to upload the questions for grading, write your answers in the space provided on the questions document and save it.

## Roadmap:

### Phase 1: Foundation - Complete
- Multi-source ingestion (text, PDF, images) ✓
- Multiple document combining ✓
- Auto-detection for notes and generated files ✓
- SQLite migration ✓
  
### Phase 2: Memory — Complete
- Session history, with full question/answer/grade review ✓
- Favorites — add, edit, remove, with paginated browsing ✓
- Configurable settings — JSON-backed, editable at runtime ✓
- Infrastructure — Database class with dependency injection, module-based logging, automated pytest suite, GitHub Actions CI ✓

### Phase 3: Terminal Experience — In Progress

- Draft mode (ungraded, exploratory) vs. Active Recall mode (strict, graded) — distinct psychological framing, not just a difficulty toggle
- Tutor tone setting — adjusts system prompt per session
- Attempt-based streaks — counts sessions started, not correctness, to reduce grade anxiety
- Effort-focused end-of-session summary instead of a grade-first report

### Phase 4: Adaptation

- Adaptive session calibration — single probe question at session start adjusts difficulty in real time, rather than a fixed easy block
- Topic mastery levels (Novice → Familiar → Proficient → Mastered), feeding a recommendation engine weighted by mastery, recency, and confidence gap
- Spaced repetition scheduling built on top of mastery tracking

### Phase 5: Platform

- API layer (REST endpoints for generate/grade/analytics/history) to decouple backend from the terminal interface
- Multi-provider abstraction — Gemini, Claude, GPT-4 swappable behind a common interface
- Web frontend (React + FastAPI), migrating SQLite to PostgreSQL if scale demands it

### Phase 6: Beyond

- Peer teaching mode — user explains a concept to the AI, which grades the explanation
- Multi-model consensus grading — same answer graded by two models, disagreement flagged as a confidence signal
- Async study with friends — shared question sets, results compared after the fact
