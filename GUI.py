# -*- coding: utf-8 -*-
from __future__ import print_function
import Tkinter as tk
import numpy as np

# Department names and coordinates
departments = {
    1: ("internal", (0, 6)),
    2: ("gastro", (2, 1)),
    3: ("restroom", (2, 4)),
    4: ("surgery", (4, 4)),
    5: ("ent", (6, 4)),
    6: ("emergency", (7, 6)),
    7: ("lab", (5, 6))
}

# Default map (0 = wall, 1 = path)
default_maze = np.array([
    [0, 0, 1, 1, 1, 1, 1, 1],
    [0, 0, 1, 0, 0, 0, 0, 0],
    [1, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 1, 0, 0, 0, 1, 0],
    [0, 0, 1, 1, 1, 1, 1, 0],
    [0, 0, 1, 0, 0, 0, 1, 0],
    [0, 0, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 0, 0, 0, 1, 0]
])

def get_updated_maze():
    root = tk.Tk()
    root.title("Hospital Path Weight Setting")

    entries = {}
    result = {'maze': None, 'start': None, 'end': None}

    # Department info
    info = tk.Label(root, text="Department Numbers:\n1. internal\n2. gastro\n3. restroom\n4. surgery\n5. ent\n6. emergency\n7. lab", justify='left')
    info.grid(row=0, column=2, rowspan=8, padx=20, pady=5, sticky='w')

    # Start and end input
    tk.Label(root, text="Start Department (1-7):").grid(row=7, column=0, padx=10, pady=5, sticky='e')
    start_entry = tk.Entry(root)
    start_entry.insert(0, "6")
    start_entry.grid(row=7, column=1, padx=10, pady=5)

    tk.Label(root, text="End Department (1-7):").grid(row=8, column=0, padx=10, pady=5, sticky='e')
    end_entry = tk.Entry(root)
    end_entry.insert(0, "1")
    end_entry.grid(row=8, column=1, padx=10, pady=5)

    def apply_weights_and_close():
        updated_maze = np.copy(default_maze)
        for num, (dept, coord) in departments.items():
            value = entries[dept].get()
            try:
                weight = int(value)
                updated_maze[coord] = weight
            except ValueError:
                print("%s has invalid input, skipping." % dept)

        try:
            start_index = int(start_entry.get())
            end_index = int(end_entry.get())
            start = departments[start_index][1]
            end = departments[end_index][1]
            result['maze'] = updated_maze
            result['start'] = start
            result['end'] = end
            root.destroy()
        except Exception as e:
            print("Invalid start or end department number:", e)

    # Weight entry for each department
    row = 0
    for num, (dept, coord) in departments.items():
        label = tk.Label(root, text=dept)
        label.grid(row=row, column=0, padx=10, pady=5, sticky='e')

        entry = tk.Entry(root)
        entry.insert(0, "1")
        entry.grid(row=row, column=1, padx=10, pady=5)
        entries[dept] = entry
        row += 1

    # Apply button
    submit_btn = tk.Button(root, text="Apply Settings", command=apply_weights_and_close)
    submit_btn.grid(row=9, columnspan=2, pady=10)

    root.mainloop()

    #return result['maze'], result['start'], result['end']
    return result['maze']
