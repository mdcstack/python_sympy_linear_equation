import tkinter as tk
from tkinter import scrolledtext, messagebox
import sympy as sp
import matplotlib
import re
from math_engine import solve_linear_equation
from PIL import Image, ImageTk
import io
from solution_display import display_solution_trail

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# --- Global Trackers for Animation & Panning ---
animation_id = None
pan_start_x = None
initial_xlim = None


def on_canvas_press(event):
    """Records the starting X position when the user clicks the screen."""
    global pan_start_x, initial_xlim
    if event.button == 1:  # 1 is the Left Mouse Button
        pan_start_x = event.x
        initial_xlim = ax.get_xlim()

        # NEW: Change cursor to the 4-way move cross when clicked
        canvas.get_tk_widget().config(cursor="fleur")


def on_canvas_drag(event):
    """Pans the camera horizontally as the user drags the mouse."""
    global pan_start_x, initial_xlim
    if pan_start_x is not None and event.button == 1:
        # Calculate how far the mouse moved in pixels
        dx_pixels = pan_start_x - event.x
        # Convert pixels to Matplotlib data units (4.5 width * 100 dpi = 450 pixels)
        dx_data = dx_pixels / 450.0

        # Shift the camera limits and redraw
        ax.set_xlim(initial_xlim[0] + dx_data, initial_xlim[1] + dx_data)
        canvas.draw_idle()


def on_canvas_release(event):
    """Stops the panning when the user lets go of the mouse button."""
    global pan_start_x
    pan_start_x = None

    # NEW: Revert the cursor back to the hovering hand
    canvas.get_tk_widget().config(cursor="hand2")


# --- UI Action Functions ---
def block_keyboard_typing(event):
    """Allows letters, numbers, math operators, and navigation keys."""
    if event.keysym in ['Left', 'Right', 'BackSpace', 'Delete']:
        return None

    allowed_symbols = ['+', '-', '*', '/', '=', '(', ')', '.', '^']
    if event.char.isdigit() or event.char in allowed_symbols:
        return None

    if event.char.isalpha():
        cursor_pos = screen.index(tk.INSERT)
        current_text = raw_display_var.get()

        if cursor_pos > 0 and current_text[cursor_pos - 1].isalpha():
            return "break"
        if cursor_pos < len(current_text) and current_text[cursor_pos].isalpha():
            return "break"

        return None

    return "break"


def button_click(character):
    cursor_pos = screen.index(tk.INSERT)
    current_text = raw_display_var.get()
    char_str = str(character)

    if char_str.isalpha():
        if cursor_pos > 0 and current_text[cursor_pos - 1].isalpha():
            return
        if cursor_pos < len(current_text) and current_text[cursor_pos].isalpha():
            return

    new_text = current_text[:cursor_pos] + char_str + current_text[cursor_pos:]
    raw_display_var.set(new_text)
    screen.icursor(cursor_pos + len(char_str))
    screen.focus()


def clear_all():
    global animation_id
    if animation_id is not None:
        root.after_cancel(animation_id)
        animation_id = None

    raw_display_var.set("")
    final_answer_label.config(text="FINAL ANSWER: ")
    trail_display.delete(1.0, tk.END)


def delete_last():
    cursor_pos = screen.index(tk.INSERT)
    if cursor_pos > 0:
        current_text = raw_display_var.get()
        new_text = current_text[:cursor_pos - 1] + current_text[cursor_pos:]
        raw_display_var.set(new_text)
        screen.icursor(cursor_pos - 1)
        screen.focus()


def insert_fraction():
    cursor_pos = screen.index(tk.INSERT)
    current_text = raw_display_var.get()
    new_text = current_text[:cursor_pos] + "()/()" + current_text[cursor_pos:]
    raw_display_var.set(new_text)
    screen.icursor(cursor_pos + 1)
    screen.focus()


def sanitize_math_string(raw_str):
    text = raw_str.replace('÷', '/').replace('^', '**')
    text = re.sub(r'(\d)([A-Za-z\(])', r'\1*\2', text)
    text = re.sub(r'([A-Za-z])(\()', r'\1*\2', text)
    text = re.sub(r'(\))([A-Za-z0-9\(])', r'\1*\2', text)
    return text


def update_pretty_display():
    raw_text = raw_display_var.get()
    math_text = sanitize_math_string(raw_text)

    try:
        if "=" in math_text:
            lhs_str, rhs_str = math_text.split("=", 1)
            lhs_expr = sp.sympify(lhs_str, evaluate=False) if lhs_str else ""
            rhs_expr = sp.sympify(rhs_str, evaluate=False) if rhs_str else ""

            lhs_latex = sp.latex(lhs_expr, mul_symbol='dot', order='none') if lhs_expr else ""
            rhs_latex = sp.latex(rhs_expr, mul_symbol='dot', order='none') if rhs_expr else ""

            lhs_latex = re.sub(r'([0-9A-Za-z]+)\s*\\cdot\s*\\frac\{1\}\{([0-9A-Za-z]+)\}', r'\\frac{\1}{\2}', lhs_latex)
            rhs_latex = re.sub(r'([0-9A-Za-z]+)\s*\\cdot\s*\\frac\{1\}\{([0-9A-Za-z]+)\}', r'\\frac{\1}{\2}', rhs_latex)
            lhs_latex = re.sub(r'(\\left\(.*?\\right\))\s*\\cdot\s*\\frac\{1\}\{([0-9A-Za-z]+)\}', r'\\frac{\1}{\2}',
                               lhs_latex)
            rhs_latex = re.sub(r'(\\left\(.*?\\right\))\s*\\cdot\s*\\frac\{1\}\{([0-9A-Za-z]+)\}', r'\\frac{\1}{\2}',
                               rhs_latex)
            lhs_latex = re.sub(r'(\d)\s*\\cdot\s*([A-Za-z])', r'\1\2', lhs_latex)
            rhs_latex = re.sub(r'(\d)\s*\\cdot\s*([A-Za-z])', r'\1\2', rhs_latex)

            pretty_math = f"${lhs_latex} = {rhs_latex}$"
        else:
            expr = sp.sympify(math_text, evaluate=False)
            expr_latex = sp.latex(expr, mul_symbol='dot', order='none')

            expr_latex = re.sub(r'([0-9A-Za-z]+)\s*\\cdot\s*\\frac\{1\}\{([0-9A-Za-z]+)\}', r'\\frac{\1}{\2}',
                                expr_latex)
            expr_latex = re.sub(r'(\\left\(.*?\\right\))\s*\\cdot\s*\\frac\{1\}\{([0-9A-Za-z]+)\}', r'\\frac{\1}{\2}',
                                expr_latex)
            expr_latex = re.sub(r'(\d)\s*\\cdot\s*([A-Za-z])', r'\1\2', expr_latex)

            pretty_math = f"${expr_latex}$"

    except Exception:
        pretty_math = raw_text

    ax.clear()
    ax.axis("off")
    if raw_text == "":
        ax.text(1.0, 0.5, "0", size=20, ha="right", va="center")
    else:
        ax.text(1.0, 0.5, pretty_math, size=20, ha="right", va="center")
    canvas.draw()


def update_variable_options():
    current_text = raw_display_var.get()
    found_vars = sorted(list(set(re.findall(r'[A-Za-z]', current_text.lower()))))

    for widget in radio_buttons_inner_frame.winfo_children():
        widget.destroy()

    if not found_vars:
        tk.Label(radio_buttons_inner_frame, text="No variables detected", font=("Helvetica", 10, "italic")).pack(
            side=tk.LEFT)
        target_var.set("")
        return

    if target_var.get() not in found_vars:
        target_var.set(found_vars[0])

    for v in found_vars:
        tk.Radiobutton(radio_buttons_inner_frame, text=v, variable=target_var, value=v, font=("Helvetica", 10)).pack(
            side=tk.LEFT, padx=5)


def on_text_change(*args):
    update_pretty_display()
    update_variable_options()


def render_math_to_image(math_expr):
    """Creates a temporary canvas to draw the math, and converts it to a pasteable image."""
    fig_temp = Figure(figsize=(5, 0.6), dpi=100)
    fig_temp.patch.set_alpha(0.0)  # Transparent background
    ax_temp = fig_temp.add_subplot(111)
    ax_temp.axis("off")

    latex_str = sp.latex(math_expr, mul_symbol='dot', order='none')

    # Apply our custom fraction cleaners
    latex_str = re.sub(r'([0-9A-Za-z]+)\s*\\cdot\s*\\frac\{1\}\{([0-9A-Za-z]+)\}', r'\\frac{\1}{\2}', latex_str)
    latex_str = re.sub(r'(\\left\(.*?\\right\))\s*\\cdot\s*\\frac\{1\}\{([0-9A-Za-z]+)\}', r'\\frac{\1}{\2}', latex_str)
    latex_str = re.sub(r'(\d)\s*\\cdot\s*([A-Za-z])', r'\1\2', latex_str)

    ax_temp.text(0.0, 0.5, f"${latex_str}$", size=14, ha="left", va="center")

    # Save the drawing to computer memory
    buf = io.BytesIO()
    fig_temp.savefig(buf, format="png", bbox_inches='tight', transparent=True)
    buf.seek(0)

    img = Image.open(buf)
    return ImageTk.PhotoImage(img)


def compute_action():
    raw_equation = raw_display_var.get()
    solve_for = target_var.get()

    trail_display.delete(1.0, tk.END)

    if not raw_equation or "=" not in raw_equation:
        trail_display.insert(tk.END, "[VALIDATION STATUS: FAIL]\n")
        messagebox.showwarning("Input Error", "Please enter a complete equation with an '=' sign.")
        return

    if not solve_for:
        trail_display.insert(tk.END, "[VALIDATION STATUS: FAIL]\n")
        messagebox.showwarning("Input Error", "No variable detected to solve for.")
        return

    math_equation = sanitize_math_string(raw_equation)
    final_answer_label.config(text="FINAL ANSWER: Computing...")
    root.update()

    # 1. Ask the Math Engine for the answer and steps
    final_answer, trail_steps = solve_linear_equation(math_equation, solve_for)

    if final_answer in ["Error", "No Solution"]:
        trail_display.insert(tk.END, "[VALIDATION STATUS: FAIL]\n\n")
        display_solution_trail(trail_display, trail_steps)
        final_answer_label.config(text="FINAL ANSWER: Error")
        messagebox.showerror("Computation Error", trail_steps[0][1])
    else:
        trail_display.insert(tk.END, "[VALIDATION STATUS: PASS]\n\n")

        # 2. Hand the steps to the Solution Display renderer
        display_solution_trail(trail_display, trail_steps)

        final_answer_label.config(text=f"FINAL ANSWER: {final_answer}")

# --- Main Window Setup ---
root = tk.Tk()
root.title("Linear Equation Calculator")
root.geometry("950x620")
root.resizable(False, False)
root.configure(padx=20, pady=20)

# ==========================================
# LEFT FRAME: The Calculator Input & Keypad
# ==========================================
left_frame = tk.Frame(root)
left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))

fig = Figure(figsize=(4.5, 1.2), dpi=100)
fig.patch.set_facecolor('#e8f4f8')
ax = fig.add_subplot(111)
ax.axis("off")
ax.text(1.0, 0.5, "0", size=20, ha="right", va="center")

canvas = FigureCanvasTkAgg(fig, master=left_frame)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(fill=tk.X, pady=(0, 5))

# NEW: Set the default cursor to a hand when hovering over the display
canvas_widget.config(cursor="hand2")

# Bind the mouse events
canvas.mpl_connect('button_press_event', on_canvas_press)
canvas.mpl_connect('motion_notify_event', on_canvas_drag)
canvas.mpl_connect('button_release_event', on_canvas_release)

raw_display_var = tk.StringVar()
raw_display_var.trace_add("write", on_text_change)

screen = tk.Entry(left_frame, textvariable=raw_display_var, font=("Consolas", 14), justify="right", bd=5,
                  relief=tk.SUNKEN)
screen.pack(fill=tk.X, pady=(0, 15))
screen.bind("<Key>", block_keyboard_typing)

keypad_frame = tk.Frame(left_frame)
keypad_frame.pack()

buttons = [
    ('7', 0, 0), ('8', 0, 1), ('9', 0, 2), ('(', 0, 3), (')', 0, 4),
    ('4', 1, 0), ('5', 1, 1), ('6', 1, 2), ('*', 1, 3), ('/', 1, 4),  # Changed to forward slash
    ('1', 2, 0), ('2', 2, 1), ('3', 2, 2), ('+', 2, 3), ('-', 2, 4),
    ('0', 3, 0), ('.', 3, 1), ('x', 3, 2), ('y', 3, 3), ('^', 3, 4),
    ('C', 4, 0), ('Del', 4, 1), ('=', 4, 2), ('a/b', 4, 3)
]

for text, row, col in buttons:
    if text == 'C':
        action = clear_all
        bg_color = "#ff9999"
    elif text == 'Del':
        action = delete_last
        bg_color = "#ffcc99"
    elif text == 'a/b':
        action = insert_fraction
        bg_color = "#b3d9ff"
    else:
        action = lambda char=text: button_click(char)
        bg_color = "#f0f0f0"

    tk.Button(keypad_frame, text=text, width=4, height=2, font=("Helvetica", 12, "bold"),
              bg=bg_color, command=action).grid(row=row, column=col, padx=2, pady=2)

options_frame = tk.Frame(left_frame)
options_frame.pack(pady=(15, 0))

tk.Label(options_frame, text="Solve for:", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT, padx=5)

target_var = tk.StringVar()
radio_buttons_inner_frame = tk.Frame(options_frame)
radio_buttons_inner_frame.pack(side=tk.LEFT)

tk.Button(left_frame, text="COMPUTE", font=("Helvetica", 12, "bold"), bg="#99ff99", height=2,
          command=compute_action).pack(fill=tk.X, pady=(15, 0))

# ==========================================
# RIGHT FRAME: The Output & Solution Trail
# ==========================================
right_frame = tk.Frame(root)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

final_answer_label = tk.Label(right_frame, text="FINAL ANSWER: ", font=("Helvetica", 16, "bold"), fg="blue",
                              bg="#f0f8ff", relief=tk.RIDGE, bd=3, padx=10, pady=10)
final_answer_label.pack(fill=tk.X, pady=(0, 15))

tk.Label(right_frame, text="Solution Trail & Auditing:", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 5))

trail_display = scrolledtext.ScrolledText(right_frame, font=("Consolas", 11), bg="#f9f9f9", wrap=tk.WORD, bd=3,
                                          relief=tk.SUNKEN)
trail_display.pack(fill=tk.BOTH, expand=True)

update_variable_options()

if __name__ == "__main__":
    root.mainloop()