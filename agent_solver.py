from typing import Optional
import anthropic
from logging_config import get_logger

_log = get_logger("agent_solver")

_SOLVER_SYSTEM = """You are an expert number-guessing agent.
Use binary search to find the secret number as efficiently as possible.
After each result, recalculate your range and pick the exact midpoint.
Show your reasoning briefly before each call to check_guess."""

_SOLVER_TOOLS = [
    {
        "name": "check_guess",
        "description": (
            "Submit a guess to the number-guessing game. "
            "Returns 'Win' if correct, 'Too High' if the guess is above the secret, "
            "or 'Too Low' if the guess is below the secret."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "guess": {"type": "integer", "description": "The integer to guess."}
            },
            "required": ["guess"],
        },
    }
]


def solve_game(
    low: int,
    high: int,
    secret: int,
    max_attempts: int = 15,
    api_key: Optional[str] = None,
) -> dict:
    """
    Run the agentic solver.

    Returns:
        {
            "steps": [{"attempt": int, "guess": int, "result": str, "reasoning": str}, ...],
            "total_attempts": int,
            "solved": bool,
            "final_guess": int | None,
        }
    """
    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()

    messages = [
        {
            "role": "user",
            "content": (
                f"Find the secret number in the range [{low}, {high}] "
                f"using the check_guess tool. Use binary search."
            ),
        }
    ]

    _log.info("solver_start | range=[%d,%d] max_attempts=%d", low, high, max_attempts)
    steps: list = []
    attempts = 0
    solved = False
    final_guess = None

    while attempts < max_attempts:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=_SOLVER_SYSTEM,
            tools=_SOLVER_TOOLS,
            messages=messages,
        )

        tool_uses = [b for b in response.content if b.type == "tool_use"]
        reasoning = " ".join(
            b.text for b in response.content if b.type == "text"
        ).strip()

        # Agent finished with no tool call
        if response.stop_reason == "end_turn" or not tool_uses:
            break

        # Append assistant turn (must include all content blocks)
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for tu in tool_uses:
            guess_val = tu.input.get("guess")
            attempts += 1

            if guess_val == secret:
                result = "Win"
                solved = True
                final_guess = guess_val
            elif guess_val > secret:
                result = "Too High"
            else:
                result = "Too Low"

            _log.info("solver_step | attempt=%d guess=%d result=%s", attempts, guess_val, result)
            steps.append(
                {
                    "attempt": attempts,
                    "guess": guess_val,
                    "result": result,
                    "reasoning": reasoning,
                }
            )

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": result,
                }
            )

        messages.append({"role": "user", "content": tool_results})

        if solved:
            break

    _log.info(
        "solver_done | solved=%s attempts=%d final_guess=%s",
        solved, attempts, final_guess,
    )
    return {
        "steps": steps,
        "total_attempts": attempts,
        "solved": solved,
        "final_guess": final_guess,
    }
