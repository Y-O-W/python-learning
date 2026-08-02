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
