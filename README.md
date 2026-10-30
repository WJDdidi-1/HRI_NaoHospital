# NAO Hospital Assistant (HRI)

A Pepper/NAO-sized social robot that greets patients in a hospital lobby, asks
which department they need, plans a route across the floorplan, walks them there
while avoiding obstacles, and answers in speech with a face that shows the
emotion it recognised in the visitor.

Built for the NAOqi 2.5 runtime (`naoqi`, `qi`); the trajectory and interaction
modules talk to the robot directly, so they do not run on a laptop. The planner
is plain Python and **is** covered by tests — that is the part CI checks.

## What the robot does

1. **Detect a visitor** — `FacialExpressionDetection.py` runs the bundled Keras
   model (`expression_model.h5`) over camera frames and labels the expression.
2. **Ask where they are going** — `HRI_Speech_EmoRec_Interaction.py` holds the
   dialogue session: speech recognition, the department vocabulary, and the
   assistant's replies.
3. **Plan the walk** — `Path_Calculation.py` is a Dijkstra search over an 8×8
   weighted floorplan; each cell carries a traversal cost, so a crowded corridor
   can be made more expensive than a longer quiet one.
4. **Walk it** — `Navigation.py` draws the route, `Motion.py` turns grid moves
   into walk commands, `Obstacle.py` holds the obstacle list that inflates the
   cost of cells near people and furniture.
5. **Set the map** — `GUI.py` is a Tkinter grid editor: enter the cell weights,
   pick start and destination, and the maze is handed to the planner.

`Main.py` is the entry point that wires these together; `camera_client.py` is a
small socket client used to pull frames from a phone camera in the demo setup.

## Departments (default floorplan)

| # | Department | Cell (row, column) |
| --- | --- | --- |
| 1 | internal | (0, 6) |
| 2 | gastro | (2, 1) |
| 3 | restroom | (2, 4) |
| 4 | surgery | (4, 4) |
| 5 | ent | (6, 4) |
| 6 | emergency | (7, 6) |
| 7 | lab | (5, 6) |

## Running the parts that do not need the robot

```console
$ python -m pytest        # 7 tests over the planner
```

The tests pin down the behaviour that matters at a reception desk: a route
exists to every department, the route is contiguous and never crosses a wall,
the reported cost equals the sum of the cells it crosses, heavier cells are
avoided when a cheaper detour exists, and an unreachable target reports `-1`
with an **empty** path — a bug this suite caught: the planner used to return
`[-1, [target]]`, which made an isolated department look walkable.

On the robot, with NAOqi installed and `PYTHONPATH` pointing at the SDK:

```console
$ python Main.py            # GUI map editor, then speak or type a department
```

## Notes and limits

- The floorplan is 8×8 and the grid is hard-coded in `Path_Calculation.py`
  (`rows`, `cols`); a larger floor needs those constants widened.
- `expression_model.h5` is committed so the demo is reproducible; retraining
  needs the FER-style dataset the report describes, which is not in the repo.
- `emotion_log.csv` and `interaction_log.csv` are captures from demo runs, kept
  as evidence rather than as fixtures.
- Python 2-era idioms (`raw_input`, `print_function`) remain where NAOqi's
  interpreter required them.

## License

No license file, so the default applies: all rights reserved.
