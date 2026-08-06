"""
Hash Map / Hash Set for Lookups
--------------------------------
Trade space for time -- store things you've seen in a dict/set for
O(1) lookup instead of scanning repeatedly.

When to use: anything with "have I seen this before," counting
frequencies, finding complements (classic two-sum unsorted), detecting
duplicates.

Signal: unsorted data + you keep thinking "I'd need to search the
array again."
"""


def two_sum_unsorted(arr, target):
    seen = {}
    for i, num in enumerate(arr):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return None


if __name__ == "__main__":
    assert two_sum_unsorted([2, 7, 11, 15], 9) == [0, 1]
    assert two_sum_unsorted([3, 2, 4], 6) == [1, 2]
    assert two_sum_unsorted([1, 2, 3], 100) is None
    print("All two_sum_unsorted tests passed.")

"""
This is the classic Two Sum problem solved with a hash map in one pass, O(n) time instead of the O(n²) brute-force nested loop.

Walking through it:

- seen = {} — a dict mapping value → index for numbers already visited.
- for i, num in enumerate(arr): — walk the array once, tracking both index and value.
- complement = target - num — the number that, added to num, would hit target.
- if complement in seen: — check whether that complement was already seen earlier in the array.
  - If yes: seen[complement] is its index, i is the current index → return [earlier_index, current_index].
  - If no: record seen[num] = i so later elements can find this number as their complement.
- If no pair is found by the end, the function implicitly returns None.

Example: two_sum_unsorted([2, 7, 11, 15], 9)
1. i=0, num=2 → complement 7, not in seen → seen = {2: 0}
2. i=1, num=7 → complement 2, is in seen → return [0, 1]

Unlike two_sum_sorted (the two-pointer version), this doesn't require the array to be sorted, and it returns the original indices rather than needing a sorted-position mapping — that's the key tradeoff: O(n) time and O(n) extra space here, vs. O(1) space but requires sorted input for the two-pointer version.

seen[complement] gives the index where the complement was first recorded (0, for the value 2), and i is the current index (1, for the value 7), so it returns [0, 1] — the two indices whose values (2 + 7) sum to target (9).
"""