"""
Binary Search
-------------
Repeatedly halve the search space by comparing the midpoint to the
target -- only works on sorted (or monotonic) data.

When to use: sorted array search, "find the smallest/largest value
that satisfies condition X" (even on problems that don't look sorted
at first glance, if there's a monotonic property).

Signal: "sorted," O(log n) expected, "find the boundary where
behavior changes."
"""


def binary_search(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


if __name__ == "__main__":
    arr = [1, 3, 5, 7, 9, 11]
    assert binary_search(arr, 7) == 3
    assert binary_search(arr, 1) == 0
    assert binary_search(arr, 11) == 5
    assert binary_search(arr, 4) == -1
    assert binary_search([], 1) == -1
    print("All binary_search tests passed.")
