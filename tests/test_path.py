"""Hardware-free tests for the part that does not need a robot.

`Path_Calculation.dijkstra` is plain Python, so the cost model and the route it
returns can be checked on any machine. The rest of the project talks to NAOqi,
which only exists on the robot.
"""
import math

import pytest

from Path_Calculation import dijkstra

# The default hospital floorplan from GUI.py, repeated here so the test does not
# need Tkinter (GUI.py opens a window on import).
FLOOR = [
    [0, 0, 1, 1, 1, 1, 1, 1],
    [0, 0, 1, 0, 0, 0, 0, 0],
    [1, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 1, 0, 0, 0, 1, 0],
    [0, 0, 1, 1, 1, 1, 1, 0],
    [0, 0, 1, 0, 0, 0, 1, 0],
    [0, 0, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 0, 0, 0, 1, 0],
]

# (row, column) of the departments in GUI.py
DEPARTMENTS = {
    "internal": (0, 6),
    "gastro": (2, 1),
    "restroom": (2, 4),
    "surgery": (4, 4),
    "ent": (6, 4),
    "emergency": (7, 6),
    "lab": (5, 6),
}


def test_a_route_exists_to_every_department():
    for name, (row, column) in DEPARTMENTS.items():
        distance, path = dijkstra(FLOOR, (2, 2), (row, column))
        assert distance > 0, name
        assert path[0] == (2, 2), name
        assert path[-1] == (row, column), name


def test_the_route_is_contiguous_and_walks_on_free_cells():
    _, path = dijkstra(FLOOR, (2, 2), (5, 6))
    for (ax, ay), (bx, by) in zip(path, path[1:]):
        assert abs(ax - bx) + abs(ay - by) == 1, (ax, ay, bx, by)
    for row, column in path:
        assert FLOOR[row][column] != 0, (row, column)


def test_the_cost_is_the_sum_of_the_cells_it_crosses():
    distance, path = dijkstra(FLOOR, (2, 2), (5, 6))
    assert distance == sum(FLOOR[row][column] for row, column in path[1:])


def test_walls_are_not_crossed_even_when_the_detour_is_long():
    distance, path = dijkstra(FLOOR, (0, 2), (2, 0))
    assert distance > 0
    assert all(FLOOR[row][column] != 0 for row, column in path)


def test_start_equal_to_end_is_zero_distance():
    distance, path = dijkstra(FLOOR, (4, 4), (4, 4))
    assert distance == 0
    assert path == [(4, 4)]


def test_an_unreachable_target_reports_minus_one():
    isolated = [[1] * 8 for _ in range(8)]
    isolated[3][3] = 0
    distance, path = dijkstra(isolated, (0, 0), (3, 3))
    assert distance == -1
    assert path == []


def test_heavier_cells_are_avoided_when_a_cheaper_route_exists():
    # One expensive cell on the direct line; a detour of cost-1 cells exists.
    grid = [[1, 1, 1, 1, 1, 1, 1, 1] for _ in range(8)]
    grid[0][4] = 5
    distance, path = dijkstra(grid, (0, 2), (0, 6))
    assert distance > 0
    assert all(grid[row][column] == 1 for row, column in path)
