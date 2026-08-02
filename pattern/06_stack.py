"""
Stack
-----
LIFO structure -- last thing pushed is the first thing popped.

When to use: matching/balancing (parentheses), "next greater
element," undo functionality, expression evaluation, anything with
nested structure.

Signal: brackets/parentheses, "nested," "next greater/smaller."
"""


def is_balanced(s):
    stack = []
    pairs = {')': '(', ']': '[', '}': '{'}
    for ch in s:
        if ch in '([{':
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
    return not stack


if __name__ == "__main__":
    assert is_balanced("([{}])") is True
    assert is_balanced("([)]") is False
    assert is_balanced("(") is False
    assert is_balanced("") is True
    print("All is_balanced tests passed.")
