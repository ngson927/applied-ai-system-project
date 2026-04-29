# 💭 Reflection: Game Glitch Investigator → Applied AI System

## Original Project Reflection (Module 1)

### 1. What was broken when you started?

Bug 1 — Impossible hint at the lowest value
Expected: Guessing 1 should result in either a correct answer or a hint to go higher.
Actual: The game told me to "Go LOWER!" after I guessed 1, which is impossible.

Bug 2 — Same hint for very different guesses
Expected: Different guesses (like 1, 50, and 100) should produce different hints.
Actual: The game kept giving "Go LOWER!" regardless of the number I entered.

Bug 3 — Game felt unwinnable
Expected: Accurate hints should help narrow down the correct number.
Actual: Because the hints were inconsistent, I could not logically find the answer.

---

### 2. How did you use AI as a teammate?

I used Claude as AI tools on this project.
One correct AI suggestion was that the hint logic was comparing strings instead of integers, which caused incorrect HIGHER/LOWER messages; I verified this by fixing the code, running pytest, and manually testing the game.
One incorrect suggestion focused on possible UI problems rather than the core logic bug; after trying it, the hints were still wrong, which I confirmed by running the game again.

---

### 3. Debugging and testing your fixes

I decided the bug was fixed when the game consistently produced logical hints for different guesses and all automated tests passed.
I ran pytest tests using guesses below, above, and equal to the secret number, which confirmed that the function returned the correct HIGHER, LOWER, or correct messages.
AI helped suggest simple edge-case tests such as using very low and very high guesses, which made it easier to verify that the comparison logic worked correctly.

---

### 4. What did you learn about Streamlit and state?

Streamlit reruns the entire script every time the user interacts with the app, so session state is needed to store data like the secret number and attempts so they are not reset on each rerun.

---

## Final Project Reflection (Module 5 Extension)

### 5. How I Used AI During Development of the Extension

I used Claude (via the Claude Code CLI) as a primary collaborator throughout the extension work.

**Design phase:** I described my goal — "add a coaching AI that gives strategic hints without spoiling the answer" — and Claude suggested breaking it into three components: a RAG retriever, a coach with a system-level guardrail, and an agentic solver using tool use. This modular design made testing each piece independently much easier.

**Implementation phase:** For the agentic solver, Claude correctly explained the messages-array structure for tool-use loops: the assistant response must be appended as-is (with all content blocks, not just text), and the tool result must come back as a user message with `type: "tool_result"` and a matching `tool_use_id`. Getting this structure right on the first try saved significant debugging time.

**Evaluation design:** Claude helped design the eval harness structure — running multiple independent test categories (coach quality, guardrail, solver accuracy) and printing a clear pass/fail summary. The idea to test the guardrail by creating a "one value remaining" scenario was a specific suggestion that improved the test suite.

---

### 6. One Helpful AI Suggestion

The most helpful suggestion was the guardrail design: putting the constraint in the **system prompt** rather than trying to filter the output after the fact. A post-generation filter would have been fragile (brittle string matching). Expressing the constraint as a persona instruction — "you are a coach who never spoils the answer" — is more robust because the model's own reasoning enforces it rather than brittle downstream logic.

---

### 7. One Flawed AI Suggestion

Claude initially suggested using the beta `tool_runner` decorator pattern for the agent solver, which generates schemas automatically from function signatures. This looked clean, but the beta runner handles the loop internally and makes it harder to capture intermediate steps (each guess result + reasoning) for display. The manual agentic loop — where I control each iteration — turned out to be the right choice because I could record every step for the eval harness and for the UI display. I switched after realizing the abstraction was hiding the data I needed.

---

### 8. System Limitations and Future Improvements

**Limitations:**
- The RAG retrieval uses simple keyword overlap scoring, not semantic similarity. A query like "I'm stuck with few guesses" would miss the "Attempt Budgeting" section because the words don't overlap well.
- The AI Coach makes a fresh API call on every guess, which adds latency. For a real product, caching identical game states or batching requests would reduce cost.
- The agent solver always uses binary search because the system prompt instructs it to. A more interesting extension would let the agent choose its own strategy based on game context.
- The guardrail is prompt-level only. A determined adversarial prompt injected through a malicious game setup could potentially bypass it.

**Future Improvements:**
- Replace keyword RAG with a small embedding model for semantic retrieval.
- Add a leaderboard that tracks whether players improved after using the AI coach.
- Extend the agent solver to support multi-round sessions where it learns from past games.
- Add confidence scoring: the coach could report how certain it is about its advice.
- Use streaming to display coach advice word-by-word as it is generated.
