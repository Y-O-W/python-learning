"""
Two Pointers
------------
Use two index variables that move through a sequence (usually a sorted
array or string), either converging from both ends or moving at
different speeds.

When to use: sorted array problems, palindrome checks, pair-sum
problems, removing duplicates in place.

Signal: "sorted array," "find a pair that sums to X," "in-place."
"""


def two_sum_sorted(arr, target):
    left, right = 0, len(arr) - 1
    while left < right:
        s = arr[left] + arr[right]
        if s == target:
            return [left, right]
        elif s < target:
            left += 1
        else:
            right -= 1
    return None


if __name__ == "__main__":
    print(two_sum_sorted([1, 2, 3, 4, 6], 6))
    assert two_sum_sorted([1, 2, 3, 4, 6], 6) == [1, 3]
    print(two_sum_sorted([2, 7, 11, 15], 9))
    assert two_sum_sorted([2, 7, 11, 15], 9) == [0, 1]
    print(two_sum_sorted([1, 2, 3], 100))
    assert two_sum_sorted([1, 2, 3], 100) is None
    print("All two_sum_sorted tests passed.")
