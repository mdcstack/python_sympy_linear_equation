import tkinter as tk
import sympy as sp
import re
import io
from matplotlib.figure import Figure
from PIL import Image, ImageTk


def render_math_to_image(math_data):
    """Creates a temporary canvas to draw the math, supporting both SymPy objects and raw LaTeX."""
    fig_temp = Figure(figsize=(5, 0.6), dpi=100)
    fig_temp.patch.set_alpha(0.0)  # Transparent background
    ax_temp = fig_temp.add_subplot(111)
    ax_temp.axis("off")

    # NEW: The "Bridge" Check
    if isinstance(math_data, str) and math_data.startswith("$"):
        # If it's a raw LaTeX string from the engine, use it exactly as is!
        latex_str = math_data.strip("$")
    else:
        # If it's a SymPy object, format it normally
        latex_str = sp.latex(math_data, mul_symbol='dot', order='none')

        # Apply our custom fraction cleaners
        latex_str = re.sub(r'([0-9A-Za-z]+)\s*\\cdot\s*\\frac\{1\}\{([0-9A-Za-z]+)\}', r'\\frac{\1}{\2}', latex_str)
        latex_str = re.sub(r'(\\left\(.*?\\right\))\s*\\cdot\s*\\frac\{1\}\{([0-9A-Za-z]+)\}', r'\\frac{\1}{\2}',
                           latex_str)
        latex_str = re.sub(r'(\d)\s*\\cdot\s*([A-Za-z])', r'\1\2', latex_str)

    ax_temp.text(0.0, 0.5, f"${latex_str}$", size=14, ha="left", va="center")

    buf = io.BytesIO()
    fig_temp.savefig(buf, format="png", bbox_inches='tight', transparent=True)
    buf.seek(0)

    img = Image.open(buf)
    return ImageTk.PhotoImage(img)


def display_solution_trail(trail_display, trail_steps):
    """Takes the list of steps and safely injects them into the Tkinter Text widget."""
    trail_display.image_list = []

    for step_type, content in trail_steps:
        if step_type == "text":
            trail_display.insert(tk.END, content + "\n")
        elif step_type == "math":
            img = render_math_to_image(content)
            trail_display.image_list.append(img)
            trail_display.image_create(tk.END, image=img)
            trail_display.insert(tk.END, "\n\n")

    trail_display.see(tk.END)