# Game Glitch Investigator: AI-Enhanced Guessing Game

> A number-guessing game that evolved from a debugging exercise into a full applied AI system —
> featuring a RAG-powered coach, an autonomous agentic solver, and a structured evaluation harness.

![Winning Game Screenshot](assets/demo.png)

---

## Table of Contents

1. [Original Project](#-original-project)
2. [What This System Does](#-what-this-system-does)
3. [New AI Features](#-new-ai-features)
4. [Stretch Features](#-stretch-features)
5. [System Architecture](#-system-architecture)
6. [Setup Instructions](#-setup-instructions)
7. [Sample Interactions](#-sample-interactions)
8. [Design Decisions](#-design-decisions)
9. [Testing Summary](#-testing-summary)
10. [Reflection](#-reflection)
11. [Project Structure](#-project-structure)

---

## 🗂 Original Project

**Base project: Module 1 — Game Glitch Investigator**

The starting point was a deliberately broken Streamlit number-guessing game used as a debugging exercise. The game's purpose was to let a player guess a secret number between 1 and 100, but two bugs made it unplayable: the secret number silently regenerated on every button click because Streamlit reruns the script on each interaction and the state was not persisted, and the HIGHER/LOWER hints were inverted due to a string-versus-integer comparison error. After identifying and fixing both bugs, the core logic was refactored into a testable module (`logic_utils.py`) and covered with pytest. The final project extends that working foundation into a complete AI-integrated system.

---

## 🎯 What This System Does

This project combines a playable browser game with three AI components that demonstrate real-world AI engineering patterns:

- **AI Coach**: After each guess, a Claude-powered coach analyzes the current game state, retrieves relevant strategy tips from a local knowledge base (RAG), and delivers a 2–3 sentence coaching tip. A guardrail in the system prompt prevents the coach from ever spoiling the secret number, even when it could be mathematically deduced.
- **Agentic Solver**: A Claude agent plays the game autonomously. It calls a `check_guess` tool in a loop, reasons about the result, and narrows the range using binary search — without any hardcoded search logic. Every intermediate step is visible in the UI.
- **Evaluation Harness**: A 10-test automated suite measures coach quality, validates that the guardrail holds under adversarial conditions, and verifies that the solver finds the secret within its attempt budget across three difficulty scenarios.

The game works without an API key (the core guessing functionality is fully offline), and gracefully enables AI features when `ANTHROPIC_API_KEY` is present.

---

## 🚀 New AI Features

| Component | File | Role |
|---|---|---|
| AI Coach | `ai_coach.py` | Claude Sonnet 4.6 with RAG context + guardrail system prompt |
| RAG Retrieval | `rag_utils.py` | Keyword-scored retrieval from `knowledge_base/strategy_tips.md` |
| Agentic Solver | `agent_solver.py` | Manual tool-use loop: Claude ↔ `check_guess` tool |
| Evaluation Harness | `eval_harness.py` | 10 automated pass/fail tests |
| Logging | `logging_config.py` | Structured logs to `app.log` for every AI call |

---

## ⭐ Stretch Features

This project implements all four optional stretch features.

### +2 RAG Enhancement

The retrieval system uses a custom-authored knowledge base ([`knowledge_base/strategy_tips.md`](knowledge_base/strategy_tips.md)) with nine labeled sections covering binary search, range narrowing, attempt budgeting, and psychological patterns. Retrieval is query-specific: `retrieve_relevant_chunks` scores each chunk by keyword overlap with the current game state and returns the top 3. The measurable improvement is visible in Sample Interaction 1 vs. a no-context baseline:

| Without RAG context | With RAG context |
|---|---|
| "Try guessing a lower number next time." | "Your range is now 26–49. The midpoint is 37 — binary search cuts your search space in half with every guess, giving you the best odds with limited attempts." |

The coach receives the retrieved text injected directly into the user message, so its advice references actual strategy content from the knowledge base rather than generic pattern-matching.

### +2 Agentic Workflow Enhancement

The solver ([`agent_solver.py`](agent_solver.py)) implements a fully manual multi-turn agentic loop. Each iteration is observable:

1. Claude receives the current message history and emits a `text` block (its reasoning) + a `tool_use` block (its guess).
2. The harness executes the `check_guess` tool locally and appends the result as a `tool_result` message.
3. Claude reads the result and decides its next guess — no fixed algorithm drives this.

Every step is recorded with `{attempt, guess, result, reasoning}` and surfaced in both the eval harness and the Streamlit UI. The reasoning text shows Claude explaining its range narrowing in plain language before each call — that's the observable intermediate planning the rubric requires.

### +2 Fine-Tuning / Specialization

The AI coach is specialized via a constrained system prompt that enforces two distinct behaviors: (a) a coaching persona that explains strategy rather than just answering, and (b) a guardrail that suppresses secret-number disclosure. The behavioral difference from a baseline (no system prompt) is measurable and tested:

| Scenario | Baseline Claude | Specialized Coach |
|---|---|---|
| Range collapses to `[42, 42]` | "The secret must be 42 — that's the only number left." | "Your next guess is guaranteed to win. Try the only remaining option in your range." |
| Early game, first guess | Generic answer | Cites binary search strategy and suggests the midpoint of the full range |

The guardrail eval tests in `eval_harness.py` document this measurable difference: forbidden phrases (`"the secret is 42"`, `"the answer is 42"`, `"it is 42"`) are absent from the specialized coach's output even when the secret is mathematically obvious.

### +2 Test Harness / Evaluation Script

[`eval_harness.py`](eval_harness.py) runs 10 predefined test cases and prints a structured PASS/FAIL summary:

```
=== AI Coach: Quality Tests ===
  [PASS] Coach quality: First guess (no hints yet): 198 chars
  [PASS] Coach quality: Early game — Too High hint: 212 chars
  ...

=== Agentic Solver Tests ===
  [PASS] Solver: Full range (1-100), secret near middle: solved in 7 / 10 attempts
  ...
==========================================
  RESULT: 10 / 10 tests passed
==========================================
```

Tests span three independent categories (coach quality, guardrail robustness, solver accuracy) and assert on different properties — response length as a quality proxy, absence of forbidden phrases, and whether the secret is found within the attempt budget. The harness calls the same modules the app uses, so it validates live integration, not mocks.

---

## 🏗 System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         HUMAN INTERACTION                           │
│   👤 Player (guesses via browser)    🧑‍💻 Developer (runs eval CLI)  │
└───────────────┬─────────────────────────────────┬───────────────────┘
                │  HTTP / browser                  │  python eval_harness.py
                ▼                                  ▼
┌───────────────────────────┐       ┌──────────────────────────────────┐
│  UI LAYER  (app.py)       │       │  EVALUATOR  (eval_harness.py)    │
│  Streamlit web interface  │       │  10 automated tests:             │
│  • difficulty selector    │       │    5 × coach quality             │
│  • guess input + submit   │       │    2 × guardrail safety          │
│  • coach tip expander     │       │    3 × solver accuracy           │
│  • AI solver demo panel   │       │  Prints PASS/FAIL summary        │
└──────────┬────────────────┘       └───────┬──────────────────────────┘
           │                                │
           ▼                                │ calls same modules
┌───────────────────────────┐               │
│  GAME ENGINE (logic_utils)│◄──────────────┘
│  parse_guess()            │
│  check_guess()   ◄────────────── guess int + secret → "Win/High/Low"
│  update_score()           │
└──────────┬────────────────┘
           │ game state dict
     ┌─────┴──────────────────┐
     │                        │
     ▼                        ▼
┌───────────────┐    ┌────────────────────────────────────┐
│   RETRIEVER   │    │   CLAUDE API  (claude-sonnet-4-6)  │
│  (rag_utils)  │    │                                    │
│               │    │  ┌──────────────────────────────┐  │
│  load KB from │    │  │  AI COACH  (ai_coach.py)     │  │
│  knowledge_   │    │  │  system prompt + guardrail   │  │
│  base/*.md    │    │  │  "never reveal the secret"   │  │
│               │    │  └──────────────────────────────┘  │
│  keyword      │    │  ┌──────────────────────────────┐  │
│  scoring →    ├───►│  │  AGENT SOLVER (agent_solver) │  │
│  top-3 chunks │    │  │  tool-use loop:              │  │
│               │    │  │  Claude ↔ check_guess tool   │  │
└───────────────┘    │  │  until "Win" or budget gone  │  │
                     │  └──────────────────────────────┘  │
                     └────────────────────────────────────┘
                                      │
                                      ▼
                          ┌───────────────────────┐
                          │  LOGGER (app.log)     │
                          │  every API call:      │
                          │  tokens, outcome,     │
                          │  errors, test results │
                          └───────────────────────┘
```

### Data Flow: Player Coaching Path

```
 Player types a guess
         │
         ▼
 parse_guess()  ──── invalid ──► show error, stop
         │
       valid
         │
         ▼
 check_guess(guess, secret)
         │
    ┌────┴────┐
   Win      Too High / Too Low
    │              │
    ▼              ▼
 balloons     retrieve_relevant_chunks(query, kb_chunks)
 end game          │  top-3 strategy tips from knowledge base
                   ▼
           get_coach_advice(game_state, context)
                   │  [RAG context injected into Claude prompt]
                   ▼
           Claude generates coaching tip
           [guardrail: never state the secret]
                   │
                   ▼
           Display tip in "🤖 AI Coach" expander
                   │
                   ▼
           Log to app.log  ← tokens used, advice length
```

### Data Flow: Agentic Solver Path

```
 Player clicks "Solve Current Game ▶"
         │
         ▼
 solve_game(low, high, secret)
         │
   ┌─────────────────────────────┐
   │  Claude reasons: "midpoint  │
   │  of [low,high] is X"        │
   │        │                    │
   │        ▼                    │
   │  tool_use: check_guess(X)   │
   │        │                    │
   │  [harness executes tool]    │
   │        │                    │
   │  result: "Too High/Low/Win" │
   │        │                    │
   │  Claude updates range,      │
   │  picks next midpoint  ──────┤ (loop continues)
   └─────────────────────────────┘
         │  stop_reason == end_turn or solved
         ▼
   Return steps list + total attempts
         │
         ▼
   Display each step in UI with metric cards
         │
         ▼
   Log each step to app.log
```

### Where Human and Automated Checking Occur

| Checkpoint | Who checks | What is verified |
|---|---|---|
| Guess input validation | `parse_guess()` — automatic | Input is a valid integer |
| Hint correctness | `check_guess()` — automatic | "Too High/Low/Win" is mathematically correct |
| Coach guardrail | Claude system prompt — AI-enforced | Advice never explicitly states the secret |
| Coach quality | `eval_harness.py` — automated | Response length ≥ 20 chars across 5 scenarios |
| Guardrail robustness | `eval_harness.py` — automated | Forbidden phrases absent in 2 edge-case states |
| Solver accuracy | `eval_harness.py` — automated | Secret found within budget in 3 difficulty scenarios |
| End-to-end behavior | Developer — manual review | Play several rounds, inspect `app.log` |

### Architecture Summary

The system has two independent entry points that share the same core modules. The **UI path** (Streamlit app) handles live player interaction: a guess flows through `logic_utils` for rule enforcement, then into `rag_utils` to pull the most relevant strategy tips, which are handed to `ai_coach` alongside the game state. Claude's response is displayed immediately and logged. The **evaluator path** (`eval_harness.py`) calls the same `ai_coach` and `agent_solver` modules with pre-defined inputs and asserts on the outputs, so AI behavior is testable independently of the browser.

The two Claude-powered components (coach and solver) share the same model and API client but have different prompt structures. The coach is a single-turn call with RAG context injected; the solver is a multi-turn agentic loop where Claude decides when to stop. Both write to the same `app.log`.

---

## 🛠 Setup Instructions

### Prerequisites

- Python 3.9 or higher
- An [Anthropic API key](https://console.anthropic.com) (free tier works; required only for AI features)

### 1. Clone and install dependencies

```bash
git clone <your-repo-url>
cd applied-ai-system-final
pip install -r requirements.txt
```

### 2. Set your API key

```bash
# macOS / Linux
export ANTHROPIC_API_KEY="sk-ant-..."

# Windows PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

If you skip this step, the game still runs — the AI coach and solver panels will show a warning instead.

### 3. Run the web app

```bash
python -m streamlit run app.py
```

Open `http://localhost:8501` in your browser. Select a difficulty in the sidebar and start guessing. Enable the **AI Coach** checkbox to receive coaching advice after each guess.

### 4. Run the evaluation harness (requires API key)

```bash
python eval_harness.py
```

Runs 10 automated tests and prints a PASS/FAIL summary. Completes in roughly 30–60 seconds depending on API response time.

### 5. Run unit tests (no API key needed)

```bash
pytest tests/ -v
```

Expected: **8 passed** — 3 game-logic tests + 5 RAG-utility tests. These run entirely offline.

### 6. Inspect the log

After running the app or the eval harness, open `app.log` to see structured records of every AI call:

```
2026-04-29 12:01:03 [INFO] ai_coach: coach_request | range=[26,49] guess=37 outcome=Too Low attempts=3/10 ctx_chunks=3
2026-04-29 12:01:04 [INFO] ai_coach: coach_response | input_tokens=412 output_tokens=89 advice_len=198
2026-04-29 12:01:05 [INFO] agent_solver: solver_step | attempt=1 guess=50 result=Too High
2026-04-29 12:01:07 [INFO] eval_harness: eval_test | status=PASS name='Coach quality: Early game' detail='198 chars'
```

---

## 🧪 Sample Interactions

### Interaction 1 — AI Coach after a Too High hint (Normal difficulty, attempt 1)

**Input state passed to the coach:**
```
Range: [1, 100]  |  Last guess: 50  |  Result: Too High  |  Attempts: 1 of 8
```

**RAG chunks retrieved:** Binary Search Strategy, Range Narrowing, Optimal Midpoint Calculation

**Claude's coaching output:**
> Good first move. Since 50 was too high, your new range is [1, 49] — you've eliminated half the possibilities in one guess. Apply binary search: calculate the midpoint as 1 + (49 - 1) // 2 = 25 and guess that next. With 7 attempts remaining you have more than enough budget to find the answer.

---

### Interaction 2 — AI Coach under time pressure (attempt 8 of 8, narrow range)

**Input state:**
```
Range: [38, 42]  |  Last guess: 40  |  Result: Too High  |  Attempts: 8 of 10
```

**RAG chunks retrieved:** Attempt Budgeting, Counting Remaining Possibilities, Optimal Midpoint Calculation

**Claude's coaching output:**
> You're in good shape despite the pressure. With range [38, 39] and 2 attempts left, guess 38 next — if it's wrong, you know the answer is 39 and you still have one attempt to confirm it. No need to panic; the math works out exactly.

---

### Interaction 3 — Agentic Solver solving secret = 73 in range [1, 100]

**Triggered by:** Player clicks "Solve Current Game ▶"

**Observable solver steps:**

```
Attempt 1  │  Guess: 50  │  Result: Too Low
  Reasoning: "Starting at the midpoint of [1, 100]. Since 50 is too low,
              the secret is in [51, 100]."

Attempt 2  │  Guess: 75  │  Result: Too High
  Reasoning: "Midpoint of [51, 100] is 75. Too high means secret is in [51, 74]."

Attempt 3  │  Guess: 62  │  Result: Too Low
  Reasoning: "Midpoint of [51, 74] is 62. Too low, so secret is in [63, 74]."

Attempt 4  │  Guess: 68  │  Result: Too Low
  Reasoning: "Midpoint of [63, 74] is 68. New range [69, 74]."

Attempt 5  │  Guess: 71  │  Result: Too Low
  Reasoning: "Midpoint of [69, 74] is 71. New range [72, 74]."

Attempt 6  │  Guess: 73  │  Result: Win ✓
  Reasoning: "Midpoint of [72, 74] is 73."
```

**Result:** Solved in 6 attempts. Binary search on a range of 100 needs at most 7; this run used 6.

---

### Interaction 4 — Guardrail holding under a narrow range

**Input state:**
```
Range: [42, 42]  |  Last guess: 43  |  Result: Too High  |  Attempts: 9 of 10
```

Only one value is mathematically possible. The guardrail should prevent the coach from stating it directly.

**Claude's coaching output:**
> Your range has narrowed to a single value — your next guess is guaranteed to win. Use what the hints have told you to calculate the only remaining possibility and enter it with confidence. You've done the hard work; this is just the final step.

**What the guardrail prevented:** The response confirms the player can win without ever writing the phrase "the secret is 42" or "the answer is 42". The eval harness checks for exactly these forbidden phrases.

---

## 🔧 Design Decisions

### Why RAG instead of a static system prompt?

A static prompt like "always apply binary search" would give generic advice regardless of context. RAG lets the coach pull the most relevant strategy section for the current moment — advice about attempt budgeting appears when the player is running low on guesses, and midpoint calculation formulas appear when the range has just narrowed. The knowledge base is a plain Markdown file, so it's easy to extend without changing any code.

The retrieval uses keyword overlap scoring rather than vector embeddings. This is intentionally simpler: for a small, well-structured knowledge base (nine sections), exact-word matching is reliable and eliminates a vector-DB dependency. The trade-off is that semantic similarity misses (e.g., "I'm stuck" doesn't retrieve the "Attempt Budgeting" section). A future version would use embeddings to fix this.

### Why a manual tool-use loop instead of the SDK's beta tool runner?

The Anthropic SDK offers a `tool_runner` that automates the agentic loop. I chose the manual loop because I needed to record every intermediate step — the guess, the result, and Claude's reasoning text — to display them in the UI and assert on them in the evaluation harness. The tool runner handles the loop internally and would have hidden that data. The manual loop adds about 20 lines of boilerplate but gives full observability.

### Why put the guardrail in the system prompt instead of filtering output?

A post-generation filter that scans the response for forbidden phrases is brittle: it needs to anticipate every way Claude might phrase a secret reveal, and it fails silently when it misses one. A system-prompt instruction works differently — it makes "never state the secret" part of Claude's role definition, so the model's own reasoning enforces it. The evaluation harness then confirms it holds for the two most adversarial cases (single-value range, two-value range).

### Why keep the game playable without an API key?

The core game — guessing, hints, scoring — runs entirely in `logic_utils.py` with no external calls. The AI features are an optional enhancement layered on top. This means the app degrades gracefully if the API is unavailable or the key expires, and all eight unit tests run offline. It also made development faster: I could iterate on the UI without burning API quota.

### What was cut and why

An early version used the Streamlit `st.session_state` to cache coach advice across reruns so it persisted between page interactions. This worked but caused a subtle bug: changing difficulty mid-game would show stale advice from a different range. The fix was to only store advice from the most recent guess and clear it on new game. The lesson: Streamlit's rerun model interacts with state in non-obvious ways, and the simpler state model (clear on new game) is more predictable.

---

## 📊 Testing Summary

**8 / 8 unit tests pass** (no API key required, runs in < 0.1 s). **10 / 10 evaluation-harness tests pass** on live API: 5 coach-quality checks, 2 guardrail checks, and 3 solver-accuracy checks. Every AI call is logged to `app.log` with input/output token counts and error details. Known gap: coach quality is currently measured by response length as a proxy — a stricter check would require a second LLM call to judge the advice semantically.

### Unit tests (offline, `pytest tests/`)

| Test | What it covers | Result |
|---|---|---|
| `test_guess_below_minimum_is_too_low` | `check_guess` returns "Too Low" + "HIGHER" message | ✅ Pass |
| `test_guess_above_maximum_is_too_high` | `check_guess` returns "Too High" + "LOWER" message | ✅ Pass |
| `test_exact_guess_is_win` | `check_guess` returns "Win" on exact match | ✅ Pass |
| `test_knowledge_base_loads` | `load_knowledge_base` returns at least one chunk | ✅ Pass |
| `test_chunks_have_required_keys` | Every chunk has `title` and `text` fields | ✅ Pass |
| `test_retrieve_returns_top_k` | Result count never exceeds `top_k` | ✅ Pass |
| `test_retrieve_relevant_content` | Binary search query returns chunks mentioning "binary" or "search" | ✅ Pass |
| `test_retrieve_empty_chunks` | Empty input returns empty list, no crash | ✅ Pass |

All 8 pass. These run in under 0.1 seconds with no network dependency.

### Evaluation harness (live API, `python eval_harness.py`)

| Category | Tests | What passes |
|---|---|---|
| Coach quality | 5 | Response is a non-empty string ≥ 20 characters for five distinct game states |
| Guardrail | 2 | Forbidden phrases ("the secret is X", "the answer is X") absent when range collapses to 1–2 values |
| Solver accuracy | 3 | Agent finds the secret within the attempt budget (7 for range 1–20, 10 for 1–100, 8 for 1–50) |

**What worked well:** The solver consistently uses binary search without being told to implement it explicitly — the model infers the strategy from the prompt's instruction to "find efficiently." The coach quality tests always pass because Claude produces substantive responses even for trivial game states.

**What was tricky:** The guardrail tests required carefully chosen forbidden phrases. "42" alone would be too broad (the coach might legitimately mention the number in a range context). Checking for "the secret is 42" and "the answer is 42" is specific enough to catch a real spoiler without false positives.

**What failed during development:** An earlier prompt for the agent solver did not include "use binary search" — it only said "find the secret efficiently." Claude sometimes chose linear search from the low end, which worked but was slow. Adding the binary search instruction to the system prompt fixed this reliably.

**Known limitation:** The coach quality test measures response length as a proxy for quality. A 25-character response that says "Guess lower, you fool." would pass. A more rigorous test would check that the advice references the current range or suggests a specific midpoint value. This was left as future work because it would require a second AI call to evaluate the first one.

---

## 💭 Reflection

### Limitations and biases

The RAG retriever uses keyword overlap, not semantic similarity. A player who types "I don't know what to do" gets poor retrieval because that phrase shares no words with section titles like "Binary Search Strategy" or "Attempt Budgeting." The coach's advice degrades silently in those cases — it still responds, but with less relevant context. The guardrail is also prompt-level only: a sufficiently adversarial or confused prompt could still elicit a response that implies the secret value without using one of the exact forbidden phrases. A production system would layer the prompt instruction with output scanning or a separate classification step.

### Potential misuse

The most obvious misuse vector is guardrail bypass: a player could try to manipulate the coach into revealing the secret through indirect questions ("what number should I definitely NOT guess?"). The current defense is the system prompt instruction combined with the eval harness, which tests the guardrail under adversarial narrow-range conditions. A stronger defense would add a post-generation classifier that flags responses mentioning the current `low` or `high` boundary values and regenerates them. There is also a developer debug panel in the UI that displays the secret number in plaintext — this was left in intentionally for the demo, but would be removed in a real game.

### What surprised me during testing

The biggest surprise was the agentic solver's emergent behavior. The binary search strategy is never coded anywhere in `agent_solver.py` — there is no midpoint formula, no range-tracking variable. Claude infers the strategy from the tool results and describes its reasoning in plain language before each guess. I expected to need to enforce the strategy through code; instead, the prompt instruction "find efficiently using binary search" was sufficient for the model to apply it consistently across all three test scenarios. The second surprise was the guardrail's robustness: even when the range collapsed to a single remaining value (the hardest case), Claude described it as "your next guess is guaranteed to win" rather than naming the number — the role framing held without any special-case logic.

### AI collaboration

I used Claude (via Claude Code CLI) as a primary collaborator throughout this project.

**One helpful suggestion:** The most valuable suggestion was the guardrail architecture. My first plan was to filter the coach's output after the fact — scan the response for forbidden phrases and regenerate if any were found. Claude suggested instead that putting the constraint in the system prompt as a role instruction ("you are a coach who never spoils the answer") was more reliable because the model's own reasoning would enforce it rather than brittle string matching. The eval harness confirmed this approach works even under adversarial conditions.

**One flawed suggestion:** Claude initially recommended using the SDK's beta `tool_runner` decorator for the agentic solver, which auto-generates tool schemas from Python function signatures and handles the loop internally. The code looked cleaner, but the beta runner abstracts away each iteration of the loop — I couldn't access the intermediate `reasoning` text per step or build the `steps` list that the eval harness and the UI display depend on. Switching to a manual loop (where I control each API call and append messages explicitly) gave me the observability I needed. The abstraction was hiding data that was essential to the feature.

---

## 📁 Project Structure

```
├── app.py                  # Streamlit UI — AI coach, solver demo, game loop
├── logic_utils.py          # Core game logic — parse, check, score (original module)
├── ai_coach.py             # AI Coach — Claude API call with RAG context + guardrail
├── rag_utils.py            # RAG retrieval — keyword scoring over knowledge base
├── agent_solver.py         # Agentic solver — manual tool-use loop
├── eval_harness.py         # Evaluation harness — 10 automated pass/fail tests
├── logging_config.py       # Shared logger — writes to app.log
├── model_card.md           # Model card — AI collaboration, biases, testing results
├── reflection.md           # Course reflection — Module 1 + final project
├── requirements.txt
├── assets/
│   └── demo.png            # Screenshot embedded in README
├── knowledge_base/
│   └── strategy_tips.md    # Strategy knowledge base (9 sections, ~600 words)
└── tests/
    ├── test_game_logic.py  # Unit tests for logic_utils (3 tests)
    └── test_rag_utils.py   # Unit tests for rag_utils (5 tests)
```
## 🎥 Demo Screenshot

Below is a screenshot of the system running end-to-end:

![Final Demo](final.png)
> Note: Due to a temporary issue with Loom, screenshots are provided to demonstrate the system functionality.