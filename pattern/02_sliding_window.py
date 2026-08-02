"""
Sliding Window
--------------
Maintain a "window" (a contiguous subarray/substring) defined by two
pointers, expanding the right edge and shrinking the left edge as some
condition is violated. Avoids recomputing from scratch (O(n) instead
of O(n^2)).

When to use: "longest/shortest substring with property X," "max sum
subarray of size k," "contains all characters."

Signal: "contiguous," "substring," "subarray," "at most/exactly K."
"""


def longest_unique_substring(s):
    seen = {}
    left = max_len = 0
    for right, ch in enumerate(s):
        if ch in seen and seen[ch] >= left:
            left = seen[ch] + 1
        seen[ch] = right
        max_len = max(max_len, right - left + 1)
    return max_len


if __name__ == "__main__":
    assert longest_unique_substring("abcabcbb") == 3
    assert longest_unique_substring("bbbbb") == 1
    assert longest_unique_substring("pwwkew") == 3
    assert longest_unique_substring("") == 0
    print("All longest_unique_substring tests passed.")
