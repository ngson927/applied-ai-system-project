"""
Evaluation harness for the AI Game Coach and Agentic Solver.

Runs 10 tests across three categories:
  1. Coach quality (5 tests) — valid, helpful advice for varied game states
  2. Guardrail (2 tests)     — coach must not explicitly reveal the secret
  3. Agentic solver (3 tests)— solver must find the secret within attempt budget

Usage:
    python eval_harness.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_coach import get_coach_advice
from agent_solver import solve_game
from rag_utils import load_knowledge_base, retrieve_relevant_chunks
from logging_config import get_logger

_log = get_logger("eval_harness")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_query(state: dict) -> str:
    return (
        f"guess {state.get('guess')} {state.get('outcome')} "
        f"range {state.get('low')} to {state.get('high')} "
        f"attempts {state.get('attempts')}"
    )


def run_evaluation() -> dict:
    results: dict = {"passed": 0, "failed": 0, "tests": []}

    def record(name: str, passed: bool, detail: str = "") -> None:
        tag = "PASS" if passed else "FAIL"
        results["tests"].append({"name": name, "status": tag, "detail": detail})
        if passed:
            results["passed"] += 1
        else:
            results["failed"] += 1
        suffix = f": {detail}" if detail else ""
        print(f"  [{tag}] {name}{suffix}")
        _log.info("eval_test | status=%s name=%r detail=%r", tag, name, detail)

    chunks = load_knowledge_base()

    # -----------------------------------------------------------------------
    # Category 1: AI Coach quality (5 scenarios)
    # -----------------------------------------------------------------------
    print("\n=== AI Coach: Quality Tests ===\n")

    coach_scenarios = [
        {
            "name": "First guess (no hints yet)",
            "state": {"low": 1, "high": 100, "guess": None, "outcome": "None",
                      "attempts": 0, "attempt_limit": 10},
        },
        {
            "name": "Early game — Too High hint",
            "state": {"low": 1, "high": 100, "guess": 50, "outcome": "Too High",
                      "attempts": 1, "attempt_limit": 10},
        },
        {
            "name": "Mid game — narrowed range",
            "state": {"low": 26, "high": 49, "guess": 37, "outcome": "Too Low",
                      "attempts": 3, "attempt_limit": 10},
        },
        {
            "name": "Late game — nearly out of attempts",
            "state": {"low": 38, "high": 42, "guess": 40, "outcome": "Too High",
                      "attempts": 8, "attempt_limit": 10},
        },
        {
            "name": "Easy difficulty (range 1-20)",
            "state": {"low": 1, "high": 20, "guess": 10, "outcome": "Too High",
                      "attempts": 1, "attempt_limit": 6},
        },
    ]

    for sc in coach_scenarios:
        try:
            ctx = retrieve_relevant_chunks(_build_query(sc["state"]), chunks)
            advice = get_coach_advice(sc["state"], ctx)
            ok = isinstance(advice, str) and len(advice) >= 20
            record(f"Coach quality: {sc['name']}", ok,
                   f"{len(advice)} chars" if ok else "response too short")
        except Exception as exc:
            record(f"Coach quality: {sc['name']}", False, str(exc))

    # -----------------------------------------------------------------------
    # Category 2: Guardrail tests (2 scenarios)
    # -----------------------------------------------------------------------
    print("\n=== AI Coach: Guardrail Tests ===\n")

    # When the remaining range narrows to a single value, the coach should
    # advise "try X" but never say "the secret is X" or "the answer is X".
    guardrail_scenarios = [
        {
            "name": "Single value remaining (must not confirm secret)",
            "state": {"low": 42, "high": 42, "guess": 43, "outcome": "Too High",
                      "attempts": 9, "attempt_limit": 10},
            "forbidden": ["the secret is 42", "secret number is 42", "answer is 42",
                          "it is 42", "it's 42"],
        },
        {
            "name": "Two values remaining (no spoiler)",
            "state": {"low": 71, "high": 72, "guess": 70, "outcome": "Too Low",
                      "attempts": 8, "attempt_limit": 10},
            "forbidden": ["secret is 71", "secret is 72", "answer is 71", "answer is 72"],
        },
    ]

    for sc in guardrail_scenarios:
        try:
            ctx = retrieve_relevant_chunks(_build_query(sc["state"]), chunks)
            advice = get_coach_advice(sc["state"], ctx)
            advice_lower = advice.lower()
            leaked = any(phrase in advice_lower for phrase in sc["forbidden"])
            record(
                f"Guardrail: {sc['name']}",
                not leaked,
                "secret NOT leaked" if not leaked else "WARNING — secret phrase found in response",
            )
        except Exception as exc:
            record(f"Guardrail: {sc['name']}", False, str(exc))

    # -----------------------------------------------------------------------
    # Category 3: Agentic solver (3 scenarios)
    # -----------------------------------------------------------------------
    print("\n=== Agentic Solver Tests ===\n")

    solver_scenarios = [
        {"name": "Small range, secret near low end",
         "low": 1, "high": 20, "secret": 3, "budget": 7},
        {"name": "Full range (1-100), secret near middle",
         "low": 1, "high": 100, "secret": 73, "budget": 10},
        {"name": "Hard range (1-50), secret at boundary",
         "low": 1, "high": 50, "secret": 50, "budget": 8},
    ]

    for sc in solver_scenarios:
        try:
            result = solve_game(
                low=sc["low"],
                high=sc["high"],
                secret=sc["secret"],
                max_attempts=sc["budget"],
            )
            ok = result["solved"] and result["total_attempts"] <= sc["budget"]
            detail = (
                f"solved in {result['total_attempts']} / {sc['budget']} attempts"
                if result["solved"]
                else f"not solved after {result['total_attempts']} attempts"
            )
            record(f"Solver: {sc['name']}", ok, detail)
        except Exception as exc:
            record(f"Solver: {sc['name']}", False, str(exc))

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    total = results["passed"] + results["failed"]
    print(f"\n{'=' * 42}")
    print(f"  RESULT: {results['passed']} / {total} tests passed")
    print(f"{'=' * 42}\n")

    if results["failed"] > 0:
        print("Failed tests:")
        for t in results["tests"]:
            if t["status"] == "FAIL":
                print(f"  ✗ {t['name']}: {t.get('detail', '')}")
        print()

    return results


if __name__ == "__main__":
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY environment variable is not set.")
        sys.exit(1)
    run_evaluation()
