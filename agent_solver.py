import os
from typing import Optional
import google.generativeai as genai
from logging_config import get_logger

_log = get_logger("agent_solver")

_SOLVER_SYSTEM = """You are an expert number-guessing agent.
Use binary search to find the secret number as efficiently as possible.
After each result, recalculate your range and pick the exact midpoint.
Show your reasoning briefly before each call to check_guess."""

_SOLVER_TOOLS = [
    {
        "function_declarations": [
            {
                "name": "check_guess",
                "description": (
                    "Submit a guess to the number-guessing game. "
                    "Returns 'Win' if correct, 'Too High' if the guess is above the secret, "
                    "or 'Too Low' if the guess is below the secret."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guess": {"type": "integer", "description": "The integer to guess."}
                    },
                    "required": ["guess"],
                },
            }
        ]
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
    genai.configure(api_key=api_key or os.getenv("GEMINI_API_KEY"))

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=_SOLVER_SYSTEM,
        tools=_SOLVER_TOOLS,
    )

    chat = model.start_chat()

    _log.info("solver_start | range=[%d,%d] max_attempts=%d", low, high, max_attempts)
    steps: list = []
    attempts = 0
    solved = False
    final_guess = None

    response = chat.send_message(
        f"Find the secret number in the range [{low}, {high}] "
        f"using the check_guess tool. Use binary search."
    )

    while attempts < max_attempts:
        # Collect function-call parts and any reasoning text from this turn
        function_call_parts = [
            p for p in response.parts
            if hasattr(p, "function_call") and p.function_call and p.function_call.name
        ]
        reasoning = " ".join(
            p.text for p in response.parts if hasattr(p, "text") and p.text
        ).strip()

        # No tool calls — model has finished
        if not function_call_parts:
            break

        tool_result_parts = []
        for fc_part in function_call_parts:
            fc = fc_part.function_call
            guess_val = int(fc.args["guess"])
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

            tool_result_parts.append(
                genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=fc.name,
                        response={"result": result},
                    )
                )
            )

        if solved:
            break

        response = chat.send_message(tool_result_parts)

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
