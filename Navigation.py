import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from Path_Calculation import dijkstra


def run_navigation(maze1, start, end, show=True):
    """
    Runs pathfinding from start to end and optionally displays the result.
    Returns (distance, path)
    """
    distance, path = dijkstra(maze1, start, end)

    maze = np.array([
        [0, 0, 1, 1, 1, 1, 1, 1],
        [0, 0, 1, 0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1, 1, 1, 0],
        [0, 0, 1, 0, 0, 0, 1, 0],
        [0, 0, 1, 1, 1, 1, 1, 0],
        [0, 0, 1, 0, 0, 0, 1, 0],
        [0, 0, 1, 1, 1, 1, 1, 0],
        [0, 0, 0, 0, 0, 0, 1, 0]
    ])

    if show:
        visual = np.copy(maze)
        for x, y in path:
            visual[x][y] = 2  # mark path

        plt.figure(figsize=(6, 6))
        plt.imshow(visual, cmap='gray_r')
        plt.title("Shortest Path (Distance: %d)" % distance)
        plt.xticks(np.arange(8))
        plt.yticks(np.arange(8))
        plt.grid(True, color='lightgray')
        plt.text(start[1], start[0]+0.2, 'Start', va='top', ha='center', color='yellow', fontsize=12)
        plt.text(end[1], end[0]+0.2, 'End', va='top', ha='center', color='red', fontsize=12)
        plt.text(6, 0, 'internal:'+str(maze1[0,6]), va='center', ha='center', color='white', fontsize=12)
        plt.text(1, 2, 'gastro:'+str(maze1[2,1]), va='center', ha='center', color='white', fontsize=12)
        plt.text(4, 2, 'restroom:'+str(maze1[2,4]), va='center', ha='center', color='white', fontsize=12)
        plt.text(4, 4, 'surgery:'+str(maze1[4,4]), va='center', ha='center', color='white', fontsize=12)
        plt.text(4, 6, 'ent:'+str(maze1[6,4]), va='center', ha='center', color='white', fontsize=12)
        plt.text(6, 7, 'emergency:'+str(maze1[7,6]), va='center', ha='center', color='grey', fontsize=12)
        plt.text(6, 5, 'lab:' + str(maze1[5, 6]), va='center', ha='center', color='white', fontsize=12)
        plt.show()

    print "Shortest Path Distance: %d" % distance
    print "Path:"
    for step in path:
        print step

    #return distance, path

if __name__ == "__main__":
    from GUI import get_updated_maze
    maze, start, end = get_updated_maze()
    run_navigation(maze, start, end)
    print(type(start), type(end))