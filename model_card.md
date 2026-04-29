# Model Card: Game Glitch Investigator — AI Coach & Agentic Solver

## Model Overview

| Field | Value |
|---|---|
| **Project** | Game Glitch Investigator (Module 1 → Module 5 Extension) |
| **AI Model** | Claude Sonnet 4.6 (`claude-sonnet-4-6`) via Anthropic Python SDK |
| **Components** | AI Coach (RAG + guardrail), Agentic Solver (tool-use loop) |
| **Primary Use** | Strategic coaching for a number-guessing game; autonomous solving via binary search |
| **Developer** | ngson927 |

---

## AI Collaboration

This project was built with Claude (via Claude Code CLI) as a primary collaborator throughout design, implementation, and evaluation.

### One Helpful Suggestion

**Guardrail in the system prompt rather than output filtering.**

My initial plan was to scan the coach's response after generation and regenerate it if it contained forbidden phrases. Claude suggested instead that placing the constraint as a role instruction in the system prompt — "you are a coach who never spoils the answer" — would be more robust. A post-generation filter requires predicting every possible phrasing of a spoiler in advance; a role instruction lets the model's own reasoning enforce the constraint. The eval harness confirmed this approach holds even under adversarial conditions (range collapsed to a single value), and no additional filtering code was needed.

### One Flawed or Incorrect Suggestion

**Using the SDK beta `tool_runner` for the agentic solver.**

Claude initially recommended the beta `@tool` decorator and `tool_runner` pattern, which auto-generates tool schemas from Python function signatures and manages the agentic loop internally. The code was cleaner, but the beta runner abstracts away each iteration — I could not access the `text` block (Claude's reasoning) alongside each guess, nor could I build the `steps` list that the eval harness and UI display depend on. I switched to a manual loop where I control each `messages.create` call, append `response.content` as the assistant turn, and collect results explicitly. The abstraction was hiding data that was essential to the feature. This was the right call and is documented in the Design Decisions section of the README.

---

## Intended Use

- **In scope:** Providing strategic hints to a human player of a number-guessing game without revealing the secret number; autonomously solving the game to demonstrate binary search reasoning.
- **Out of scope:** Any application outside this game context. The model is not fine-tuned and inherits all general capabilities and limitations of Claude Sonnet 4.6.

---

## Limitations and Biases

**RAG retrieval quality:** The retriever uses keyword overlap, not semantic similarity. Queries that don't share vocabulary with the knowledge base section titles (e.g., "I have no idea what to do") receive poorly matched context. The coach still responds, but with less relevant guidance. Semantic retrieval (e.g., embedding-based cosine similarity) would fix this at the cost of a vector-store dependency.

**Guardrail robustness:** The guardrail is enforced only through the system prompt. A sufficiently adversarial prompt — asking "what number should I definitely NOT guess?" or using indirect framing — could elicit a response that implies the secret without triggering the forbidden-phrase check in the eval harness. A production system would layer the prompt instruction with a post-generation classifier.

**Coach quality proxy:** The eval harness measures coach quality by response length (≥ 20 characters). A 25-character response like "Guess lower, you fool." would pass. The actual advice quality depends on Claude's general reasoning ability and the relevance of the retrieved context, neither of which is directly measured.

**No demographic bias surface:** The game and coaching context involve no personal data, demographics, or identity-sensitive information. Bias risk in this application is minimal and isolated to coaching style variation across game states.

---

## Testing Results

### Unit Tests (offline, `pytest tests/ -v`)

| Test | Result |
|---|---|
| `test_guess_below_minimum_is_too_low` | ✅ Pass |
| `test_guess_above_maximum_is_too_high` | ✅ Pass |
| `test_exact_guess_is_win` | ✅ Pass |
| `test_knowledge_base_loads` | ✅ Pass |
| `test_chunks_have_required_keys` | ✅ Pass |
| `test_retrieve_returns_top_k` | ✅ Pass |
| `test_retrieve_relevant_content` | ✅ Pass |
| `test_retrieve_empty_chunks` | ✅ Pass |

**8 / 8 pass.** No API key required. Runs in under 0.1 seconds.

### Evaluation Harness (live API, `python eval_harness.py`)

| Category | Tests | Result |
|---|---|---|
| Coach quality | 5 | ✅ 5 / 5 pass — substantive responses across all game states |
| Guardrail | 2 | ✅ 2 / 2 pass — forbidden phrases absent when range is 1–2 values |
| Solver accuracy | 3 | ✅ 3 / 3 pass — secret found within budget on all difficulty scenarios |

**10 / 10 pass.** Every AI call is logged to `app.log` with model, token counts, and error details.

### What Failed During Development

An earlier version of the agent solver system prompt did not include the phrase "use binary search." The instruction only said "find the secret efficiently." Claude sometimes chose linear search from the low end, which was correct but slow — it could exhaust the attempt budget on a full 1–100 range. Adding the explicit binary search instruction resolved this reliably across all three solver test scenarios.

---

## Ethical Considerations

**Misuse potential:** The most plausible misuse is guardrail bypass — a player attempting to extract the secret by asking indirect questions. The current mitigations are the system-prompt role instruction and the adversarial eval tests. A stronger mitigation would add a post-generation classifier that detects boundary-value disclosure and regenerates the response.

**Transparency:** The application includes a developer debug panel (visible in the Streamlit UI) that displays the secret number in plaintext. This was left in intentionally for demo and grading purposes. It would be removed in a production deployment.

**Dependency on external API:** All AI features require a live Anthropic API key. The game degrades gracefully without one — the core guessing loop remains fully functional — but the coaching and solver features are unavailable. This is documented in the README setup instructions.
