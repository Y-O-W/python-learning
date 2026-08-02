"""
BFS (Breadth-First Search)
---------------------------
Explore a graph/tree/grid level by level using a queue (FIFO).
Guarantees the shortest path in unweighted graphs because it explores
all nodes at distance 1 before distance 2, etc.

When to use: shortest path, "minimum number of steps," level-order
tree traversal, grid problems ("minimum moves to reach the exit").

Signal: "shortest," "minimum steps/moves," "fewest."
"""

from collections import deque


def bfs_shortest_path(graph, start, target):
    queue = deque([(start, 0)])  # (node, distance)
    visited = {start}
    while queue:
        node, dist = queue.popleft()
        if node == target:
            return dist
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, dist + 1))
    return -1


if __name__ == "__main__":
    graph = {
        "A": ["B", "C"],
        "B": ["A", "D"],
        "C": ["A", "D"],
        "D": ["B", "C", "E"],
        "E": ["D"],
    }
    assert bfs_shortest_path(graph, "A", "E") == 3
    assert bfs_shortest_path(graph, "A", "A") == 0
    assert bfs_shortest_path(graph, "A", "Z" if "Z" in graph else "E") == 3
    graph["Z"] = []
    assert bfs_shortest_path(graph, "A", "Z") == -1
    print("All bfs_shortest_path tests passed.")
