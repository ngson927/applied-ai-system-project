# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

- What did the game look like the first time you ran it?
- List at least two concrete bugs you noticed at the start  
  (for example: "the hints were backwards").
Bug 1 — Impossible hint at the lowest value
Expected: Guessing 1 should result in either a correct answer or a hint to go higher.
Actual: The game told me to “Go LOWER!” after I guessed 1, which is impossible.

Bug 2 — Same hint for very different guesses
Expected: Different guesses (like 1, 50, and 100) should produce different hints.
Actual: The game kept giving “Go LOWER!” regardless of the number I entered.

Bug 3 — Game felt unwinnable
Expected: Accurate hints should help narrow down the correct number.
Actual: Because the hints were inconsistent, I could not logically find the answer, making the game feel broken.
---

## 2. How did you use AI as a teammate?

- Which AI tools did you use on this project (for example: ChatGPT, Gemini, Copilot)?
- Give one example of an AI suggestion that was correct (including what the AI suggested and how you verified the result).
- Give one example of an AI suggestion that was incorrect or misleading (including what the AI suggested and how you verified the result).
I used Claude as AI tools on this project.
One correct AI suggestion was that the hint logic was comparing strings instead of integers, which caused incorrect HIGHER/LOWER messages; I verified this by fixing the code, running pytest, and manually testing the game.
One incorrect suggestion focused on possible UI problems rather than the core logic bug; after trying it, the hints were still wrong, which I confirmed by running the game again.
---

## 3. Debugging and testing your fixes

- How did you decide whether a bug was really fixed?
- Describe at least one test you ran (manual or using pytest)  
  and what it showed you about your code.
- Did AI help you design or understand any tests? How?
I decided the bug was fixed when the game consistently produced logical hints for different guesses and all automated tests passed.
I ran pytest tests using guesses below, above, and equal to the secret number, which confirmed that the function returned the correct HIGHER, LOWER, or correct messages.
AI helped suggest simple edge-case tests such as using very low and very high guesses, which made it easier to verify that the comparison logic worked correctly.
---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?
Streamlit reruns the entire script every time the user interacts with the app, so session state is needed to store data like the secret number and attempts so they are not reset on each rerun.
---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
- This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.
One habit I want to reuse is testing edge cases, such as minimum and maximum inputs, because they quickly reveal hidden logic errors.
Next time I work with AI on a coding task, I would verify each suggestion step by step with tests instead of assuming the first solution is correct.
This project showed me that AI-generated code can look correct but still contain subtle bugs, so it should be treated as a helpful assistant rather than a final authority.