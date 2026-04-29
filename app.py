import os
import random
import streamlit as st
from logic_utils import get_range_for_difficulty, parse_guess, check_guess, update_score
from rag_utils import load_knowledge_base, retrieve_relevant_chunks
from ai_coach import get_coach_advice
from logging_config import get_logger

_log = get_logger("app")

st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game. Something is off.")

st.sidebar.header("Settings")

_api_key_set = bool(os.getenv("ANTHROPIC_API_KEY"))
ai_coach_on = st.sidebar.checkbox(
    "Enable AI Coach 🤖",
    value=_api_key_set,
    disabled=not _api_key_set,
    help="Requires ANTHROPIC_API_KEY environment variable.",
)
if not _api_key_set:
    st.sidebar.caption("⚠️ Set ANTHROPIC_API_KEY to enable the AI coach.")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

attempt_limit_map = {
    "Easy": 6,
    "Normal": 8,
    "Hard": 5,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")

if "secret" not in st.session_state:
    st.session_state.secret = random.randint(low, high)

if "attempts" not in st.session_state:
    st.session_state.attempts = 1

if "score" not in st.session_state:
    st.session_state.score = 0

if "status" not in st.session_state:
    st.session_state.status = "playing"

if "history" not in st.session_state:
    st.session_state.history = []

if "coach_advice" not in st.session_state:
    st.session_state.coach_advice = None

# Load knowledge base once per session
if "kb_chunks" not in st.session_state:
    st.session_state.kb_chunks = load_knowledge_base()

st.subheader("Make a guess")

st.info(
    f"Guess a number between 1 and 100. "
    f"Attempts left: {attempt_limit - st.session_state.attempts}"
)

with st.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)

raw_guess = st.text_input(
    "Enter your guess:",
    key=f"guess_input_{difficulty}"
)

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess 🚀")
with col2:
    new_game = st.button("New Game 🔁")
with col3:
    show_hint = st.checkbox("Show hint", value=True)

if new_game:
    st.session_state.attempts = 0
    st.session_state.secret = random.randint(1, 100)
    st.success("New game started.")
    st.rerun()

if st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
    st.stop()

if submit:
    st.session_state.attempts += 1

    ok, guess_int, err = parse_guess(raw_guess)

    if not ok:
        st.session_state.history.append(raw_guess)
        st.error(err)
    else:
        st.session_state.history.append(guess_int)

        outcome, message = check_guess(guess_int, st.session_state.secret)

        if show_hint:
            st.warning(message)

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
            )
        else:
            if st.session_state.attempts >= attempt_limit:
                st.session_state.status = "lost"
                st.error(
                    f"Out of attempts! "
                    f"The secret was {st.session_state.secret}. "
                    f"Score: {st.session_state.score}"
                )

        # Fetch AI coaching advice after every guess
        if ai_coach_on and outcome != "Win" and st.session_state.status == "playing":
            try:
                game_state = {
                    "low": low,
                    "high": high,
                    "guess": guess_int,
                    "outcome": outcome,
                    "attempts": st.session_state.attempts,
                    "attempt_limit": attempt_limit,
                }
                query = f"guess {guess_int} {outcome} range {low} to {high}"
                ctx = retrieve_relevant_chunks(query, st.session_state.kb_chunks)
                st.session_state.coach_advice = get_coach_advice(game_state, ctx)
                _log.info("coach_triggered | guess=%d outcome=%s", guess_int, outcome)
            except Exception as exc:
                _log.error("coach_error | %s", exc)
                st.session_state.coach_advice = None

if ai_coach_on and st.session_state.coach_advice:
    with st.expander("🤖 AI Coach Tip", expanded=True):
        st.info(st.session_state.coach_advice)

st.divider()

with st.expander("🤖 AI Solver Demo", expanded=False):
    st.write(
        "Watch the AI agent solve the game using binary search reasoning. "
        "This runs live API calls and may take a few seconds."
    )
    if not _api_key_set:
        st.warning("Set ANTHROPIC_API_KEY to use the AI Solver.")
    else:
        if st.button("Solve Current Game ▶"):
            from agent_solver import solve_game
            with st.spinner("AI agent is solving…"):
                sol = solve_game(
                    low=low,
                    high=high,
                    secret=st.session_state.secret,
                    max_attempts=15,
                )
            if sol["solved"]:
                st.success(
                    f"Solved in {sol['total_attempts']} attempt(s)! "
                    f"Secret = {sol['final_guess']}"
                )
            else:
                st.error(f"Agent did not find the secret in {sol['total_attempts']} attempts.")
            for step in sol["steps"]:
                col_a, col_b = st.columns([1, 3])
                col_a.metric(f"Attempt {step['attempt']}", step["guess"], step["result"])
                if step["reasoning"]:
                    col_b.caption(step["reasoning"][:200])

st.caption("Built by an AI that claims this code is production-ready.")
