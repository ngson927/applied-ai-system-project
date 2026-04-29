# Number Guessing Game Strategy Guide

## Binary Search Strategy
The most mathematically optimal approach is binary search (also called bisection).
Always guess the midpoint of your current range. This guarantees finding any number
in a range of N in at most ceil(log2(N)) guesses. For a range of 1-100, that is 7 guesses.
Formula: next_guess = low + (high - low) // 2

## Range Narrowing
After each guess, update your mental range:
- If told "Too High": new high = last_guess - 1
- If told "Too Low": new low = last_guess + 1
Always track your current [low, high] range. Never guess outside it.

## Counting Remaining Possibilities
With range [low, high], there are (high - low + 1) possible values remaining.
When this count equals 1, you have found the answer on your next guess.
When it equals 2, you need at most 1 more guess after the midpoint.

## Attempt Budgeting
Calculate how many guesses binary search needs: ceil(log2(range_size)).
- Range 1-20: needs at most 5 guesses
- Range 1-50: needs at most 6 guesses
- Range 1-100: needs at most 7 guesses
If your remaining attempts are fewer than what binary search needs, take risks.

## Optimal Midpoint Calculation
Given a range [low, high], the optimal next guess is:
    next_guess = low + (high - low) // 2
This formula avoids overflow and works for any integer range.
Example: range [26, 49] → midpoint = 26 + (49-26)//2 = 26 + 11 = 37

## When to Deviate from Binary Search
Binary search is worst-case optimal. Deviations may help when:
- You have strong priors (humans often pick round numbers: 50, 25, 75)
- The range is very small (1-3 values) and linear scan is fast
- You are trying to maximize expected score, not worst-case guesses

## Psychological Patterns
Human number pickers often choose:
- Round numbers (multiples of 5 or 10)
- Numbers that "feel random" like 37, 73, 42
- Avoid very low (1-5) or very high (96-100) values
Adjust your strategy slightly toward these if you suspect a human-picked number.

## Scoring Strategy
Many guessing games award bonus points for guessing in fewer attempts.
If the score system rewards speed, favor binary search strictly.
If early correct guesses give large bonuses, consider starting at likely values.

## Handling Hard Difficulty
On hard difficulty with fewer attempts and a smaller range:
- Hard range (1-50) with 5 attempts: binary search fits exactly
- Prioritize binary search; no room for psychological guessing
- Each guess must eliminate at least half the remaining range
