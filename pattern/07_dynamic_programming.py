"""
Dynamic Programming (DP)
--------------------------
Break a problem into overlapping subproblems, solve each once, and
cache the result (memoization, top-down) or build up from the
smallest subproblem (tabulation, bottom-up). The key insight is
identifying the recurrence relation -- how the answer for size n
relates to smaller sizes.

When to use: optimization problems (min/max), counting problems ("how
many ways"), when brute force recomputes the same subproblem
repeatedly.

Signal: "minimum/maximum cost/ways," "can you reach," Fibonacci-like
recursive structure, knapsack-style "include or exclude this item."
"""


def climb_stairs(n):
    """Classic: climbing stairs (1 or 2 steps at a time)."""
    if n <= 2:
        return n
    prev2, prev1 = 1, 2
    for _ in range(3, n + 1):
        prev2, prev1 = prev1, prev1 + prev2
    return prev1


if __name__ == "__main__":
    assert climb_stairs(1) == 1
    assert climb_stairs(2) == 2
    assert climb_stairs(3) == 3
    assert climb_stairs(4) == 5
    assert climb_stairs(5) == 8
    print("All climb_stairs tests passed.")
