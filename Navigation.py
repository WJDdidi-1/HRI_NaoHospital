# -*- coding: utf-8 -*-
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from Path_Calculation import dijkstra

def run_navigation(maze1, start, end, show=True):

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
        plt.close('all')
        visual = maze.copy()
        for (x, y) in path:
            visual[x, y] = 2

        plt.figure(figsize=(6,6))
        plt.imshow(visual, cmap='gray_r')
        plt.title("Shortest Path (Distance: %d)" % distance)
        plt.xticks(np.arange(8))
        plt.yticks(np.arange(8))
        plt.grid(True, color='lightgray')

        # Mark start and end
        plt.text(start[1], start[0]+0.2, 'Start', va='top', ha='center',
                 color='yellow', fontsize=12)
        plt.text(end[1],   end[0]+0.2,   'End',   va='top', ha='center',
                 color='red',    fontsize=12)

        # Department labels
        dept_labels = {
            'internal': (0,6,'internal'),
            'gastro':   (2,1,'gastro'),
            'restroom': (2,4,'restroom'),
            'surgery':  (4,4,'surgery'),
            'ent':      (6,4,'ent'),
            'emergency':(7,6,'emergency'),
            'lab':      (5,6,'lab'),
        }
        for _,(dx,dy,label) in dept_labels.items():
            plt.text(dy, dx+0.2, label, va='top', ha='center',
                     color='white', fontsize=11)

        plt.show()  # blocks until window closed

    print "Shortest Path Distance: %d" % distance
    print "Path:"
    for step in path:
        print step


if __name__ == "__main__":
    from GUI import get_updated_maze
    maze, start, end = get_updated_maze()
    run_navigation(maze, start, end)
