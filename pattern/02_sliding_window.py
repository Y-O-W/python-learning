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


def MinWindowSubstring(strArr):
    n, k = strArr[0], strArr[1]

    need = {}
    for ch in k:
        need[ch] = need.get(ch, 0) + 1
    missing = len(k)

    left = 0
    best_left, best_right = 0, len(n) + 1  # invalid/sentinel range

    for right, ch in enumerate(n, start=1):
        if need.get(ch, 0) > 0:
            missing -= 1
        need[ch] = need.get(ch, 0) - 1

        while missing == 0:
            if right - left < best_right - best_left:
                best_left, best_right = left, right
            left_ch = n[left]
            need[left_ch] = need.get(left_ch, 0) + 1
            if need[left_ch] > 0:
                missing += 1
            left += 1

    return n[best_left:best_right] if best_right <= len(n) else ""


if __name__ == "__main__":
    assert longest_unique_substring("abcabcbb") == 3
    assert longest_unique_substring("bbbbb") == 1
    assert longest_unique_substring("pwwkew") == 3
    assert longest_unique_substring("") == 0
    print("All longest_unique_substring tests passed.")

    print(MinWindowSubstring(["aaabaaddae", "aed"]))
    assert MinWindowSubstring(["aaabaaddae", "aed"]) == "dae"
    print("All MinWindowSubstring tests passed.")
