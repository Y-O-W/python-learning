"""
DFS (Depth-First Search)
--------------------------
Explore as far as possible down one path before backtracking, using
recursion or an explicit stack (LIFO).

When to use: exploring all paths/combinations, tree traversals,
connected components, "does a path exist," backtracking problems
(permutations, subsets, N-Queens style).

Signal: "all possible," "does there exist a path," tree/graph
structure without a shortest-path requirement.
"""


def dfs(graph, node, visited=None):
    if visited is None:
        visited = set()
    visited.add(node)
    for neighbor in graph[node]:
        if neighbor not in visited:
            dfs(graph, neighbor, visited)
    return visited


if __name__ == "__main__":
    graph = {
        "A": ["B", "C"],
        "B": ["A", "D"],
        "C": ["A", "D"],
        "D": ["B", "C", "E"],
        "E": ["D"],
        "Z": [],
    }
    assert dfs(graph, "A") == {"A", "B", "C", "D", "E"}
    assert dfs(graph, "Z") == {"Z"}
    print("All dfs tests passed.")
