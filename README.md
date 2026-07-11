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

1. Install dependencies
	```
	pip install -r requirements.txt
	```
 2. Set your API key
  Creating a text document titled .env (keep the .txt extension) in the project root. Then, in the text document, add:
	```
	GEMINI_API_KEY=[your Gemini key]
	```
3. Run SFK
	```
	python menu.py
	```
You'll be prompted to generate questions, grade answers, view analytics, review session history, change favorites, or configure settings.

4. File naming

  Auto-detection matches on filename keywords (e.g. math notes.txt or chem_unit3_slides.txt). Keep note filenames to a subject plus a keyword like notes, unit, chapter, textbook, or slides. If a file isn't auto-detected, manual entry is always available.
  As well, don't rename generated question documents. Grading auto-detection depends on the filename staying intact. To grade, write your answers directly in the space provided on the questions document and save it.

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
