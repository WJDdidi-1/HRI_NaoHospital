# Re-import necessary libraries after kernel reset
import matplotlib.pyplot as plt

def draw_corrected_motion_logic():
    fig, ax = plt.subplots(figsize=(10, 8))

    def add_box(text, xy, color="lightblue"):
        ax.text(xy[0], xy[1], text, ha="center", va="center", size=10,
                bbox=dict(boxstyle="round", facecolor=color, edgecolor="black"))

    steps = [
        ("Loop: i in range(2, len(path))", (5, 10)),
        ("Compute dx, dy, dx_prev, dy_prev", (5, 9)),
        ("Check direction change\n(dy!=0 and dx_prev!=0)\nor (dx!=0 and dy_prev!=0)", (5, 8), "lightgreen"),
        ("turn_flag == 0?", (5, 7), "lightgreen"),
        ("Direction changed along x?", (3, 6), "lightgreen"),
        ("Turn based on dx & dy_prev, turn_flag == 1", (3, 5)),
        ("Direction changed along y?", (7, 6), "lightgreen"),
        ("Turn based on dy & dx_prev, turn_flag == 1", (7, 5)),
        ("Move forward 0.15m", (5, 4)),
        ("Set turn_flag = 0", (5, 3)),
        ("Next iteration", (5, 2)),
    ]

    # Draw boxes
    for step in steps:
        if len(step) == 3:
            text, pos, color = step
        else:
            text, pos = step
            color = "lightblue"
        add_box(text, pos, color=color)

    # Arrows
    arrows = [
        ((5, 10), (5, 9)),
        ((5, 9), (5, 8)),
        ((5, 8), (5, 7)),
        ((5, 7), (3, 6)),
        ((5, 7), (7, 6)),
        ((3, 6), (3, 5)),
        ((7, 6), (7, 5)),
        ((3, 5), (5, 4)),
        ((7, 5), (5, 4)),
        ((5, 4), (5, 3)),
        ((5, 3), (5, 2)),
        ((5, 2), (5, 10)),  # Loop back
    ]

    for start, end in arrows:
        ax.annotate("", xy=end, xytext=start,
                    arrowprops=dict(arrowstyle="->", lw=1.5))

    ax.set_xlim(0, 10)
    ax.set_ylim(1, 11)
    ax.axis('off')
    plt.tight_layout()
    plt.show()

draw_corrected_motion_logic()
