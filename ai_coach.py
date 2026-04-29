import os
from typing import Optional
import anthropic
from logging_config import get_logger

_log = get_logger("ai_coach")

COACH_SYSTEM = """You are a strategic game coach for a number guessing game.
Your job is to give the player concise, helpful advice about their next move.

GUARDRAIL: You must NEVER directly state, confirm, or strongly hint at the exact
secret number — even if you could mathematically deduce it. You may describe the
remaining range, optimal strategy, and what to try next, but the word "secret"
followed by an exact value is off-limits. Your role is to coach strategy, not
spoil the answer."""


def get_coach_advice(
    game_state: dict,
    retrieved_context: list,
    api_key: Optional[str] = None,
) -> str:
    """
    Return coaching advice for the current game state.

    game_state keys:
        low (int)          - current lower bound
        high (int)         - current upper bound
        guess (int|None)   - player's last guess
        outcome (str)      - "Too High", "Too Low", "Win", or "None"
        attempts (int)     - attempts used so far
        attempt_limit (int)- total attempts allowed
    """
    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()

    context_text = "\n\n".join(retrieved_context) if retrieved_context else "No tips available."
    remaining = game_state.get("attempt_limit", 10) - game_state.get("attempts", 0)

    user_message = (
        f"Game state:\n"
        f"- Current range: {game_state.get('low', 1)} to {game_state.get('high', 100)}\n"
        f"- Last guess: {game_state.get('guess', 'none yet')}\n"
        f"- Result: {game_state.get('outcome', 'none')}\n"
        f"- Attempts remaining: {remaining}\n\n"
        f"Strategy tips for context:\n{context_text}\n\n"
        f"Give me a brief coaching tip (2-3 sentences) for my next move."
    )

    _log.info(
        "coach_request | range=[%d,%d] guess=%s outcome=%s attempts=%d/%d ctx_chunks=%d",
        game_state.get("low", 1),
        game_state.get("high", 100),
        game_state.get("guess"),
        game_state.get("outcome"),
        game_state.get("attempts", 0),
        game_state.get("attempt_limit", 10),
        len(retrieved_context),
    )

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=256,
            system=COACH_SYSTEM,
            messages=[{"role": "user", "content": user_message}],
        )
        advice = response.content[0].text
        _log.info(
            "coach_response | input_tokens=%d output_tokens=%d advice_len=%d",
            response.usage.input_tokens,
            response.usage.output_tokens,
            len(advice),
        )
        return advice
    except anthropic.APIError as exc:
        _log.error("coach_api_error | %s", exc)
        raise
