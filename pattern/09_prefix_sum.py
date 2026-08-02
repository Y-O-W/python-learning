"""
Prefix Sum
----------
Preprocess an array into a running-sum array where index i holds the
sum of all elements from the start up to i. Once built, any subarray
sum can be computed in O(1) via subtraction, instead of re-summing the
range each time.

When to use: repeated range-sum queries, "subarray sums to X,"
cumulative totals, problems where you'd otherwise re-sum overlapping
ranges.

Signal: "sum of subarray from i to j," multiple queries over the same
array, "count subarrays with sum equal to K."
"""


def subarray_sum_equals_k(arr, k):
    prefix_sums = {0: 1}  # sum -> count of times seen
    total = count = 0
    for num in arr:
        total += num
        count += prefix_sums.get(total - k, 0)
        prefix_sums[total] = prefix_sums.get(total, 0) + 1
    return count


if __name__ == "__main__":
    assert subarray_sum_equals_k([1, 1, 1], 2) == 2
    assert subarray_sum_equals_k([1, 2, 3], 3) == 2
    assert subarray_sum_equals_k([1, -1, 0], 0) == 3
    print("All subarray_sum_equals_k tests passed.")
