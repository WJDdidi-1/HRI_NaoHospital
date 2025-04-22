import heapq

directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
rows = 8
cols = 8

dept_coords = {
    1: (0, 6),  # internal
    2: (2, 1),  # gastro
    3: (2, 4),  # restroom
    4: (4, 4),  # surgery
    5: (6, 4),  # ent
    6: (7, 6),  # emergency
    7: (5, 6),  # lab
}

def get_department_coord(dept_id):
    return dept_coords.get(dept_id)


def dijkstra(maze, start, end):
    heap = [(0, start)]
    distances = {start: 0}
    prev = {start: None}
    visited = set()

    while heap:
        dist, current = heapq.heappop(heap)
        if current in visited:
            continue
        visited.add(current)

        if current == end:
            break

        for dx, dy in directions:
            nx, ny = current[0] + dx, current[1] + dy
            neighbor = (nx, ny)
            if 0 <= nx < rows and 0 <= ny < cols and maze[nx][ny] != 0:
                new_dist = dist + maze[nx][ny]
                if neighbor not in distances or new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    prev[neighbor] = current
                    heapq.heappush(heap, (new_dist, neighbor))

    path = []
    node = end
    while node:
        path.append(node)
        node = prev.get(node)
    path.reverse()
    return distances.get(end, -1), path