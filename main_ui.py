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

# --- Global Trackers for Top Screen Panning ---
animation_id = None
pan_start_x = None
initial_xlim = None

# --- Global Trackers for Final Answer Panning ---
fa_pan_start_x = None
fa_initial_xlim = None


def on_canvas_press(event):
    """Records the starting X position for the TOP screen."""
    global pan_start_x, initial_xlim
    if event.button == 1:
        pan_start_x = event.x
        initial_xlim = ax.get_xlim()
        canvas.get_tk_widget().config(cursor="fleur")


def on_canvas_drag(event):
    """Pans the camera horizontally for the TOP screen, with boundary limits."""
    global pan_start_x, initial_xlim
    if pan_start_x is not None and event.button == 1:
        dx_pixels = pan_start_x - event.x
        dx_data = dx_pixels / 450.0

        new_left = initial_xlim[0] + dx_data
        new_right = initial_xlim[1] + dx_data

        # NEW: Bounding Box Collision Detection
        if ax.texts:
            renderer = canvas.get_renderer()
            bbox = ax.texts[0].get_window_extent(renderer=renderer).transformed(ax.transData.inverted())

            # Find the true edges of the math equation (with a tiny 0.05 padding)
            min_left = min(bbox.x0, 0.0) - 0.05
            max_right = max(bbox.x1, 1.0) + 0.05
            view_width = initial_xlim[1] - initial_xlim[0]

            # If the camera hits the left wall, stop it
            if new_left < min_left:
                new_left = min_left
                new_right = new_left + view_width
            # If the camera hits the right wall, stop it
            elif new_right > max_right:
                new_right = max_right
                new_left = new_right - view_width

        ax.set_xlim(new_left, new_right)
        canvas.draw_idle()


def on_fa_canvas_drag(event):
    """Pans the camera horizontally for the BOTTOM screen, with boundary limits."""
    global fa_pan_start_x, fa_initial_xlim
    if fa_pan_start_x is not None and event.button == 1:
        dx_pixels = fa_pan_start_x - event.x
        dx_data = dx_pixels / 500.0

        new_left = fa_initial_xlim[0] + dx_data
        new_right = fa_initial_xlim[1] + dx_data

        # NEW: Bounding Box Collision Detection
        if fa_ax.texts:
            renderer = fa_canvas.get_renderer()
            bbox = fa_ax.texts[0].get_window_extent(renderer=renderer).transformed(fa_ax.transData.inverted())

            min_left = min(bbox.x0, 0.0) - 0.05
            max_right = max(bbox.x1, 1.0) + 0.05
            view_width = fa_initial_xlim[1] - fa_initial_xlim[0]

            if new_left < min_left:
                new_left = min_left
                new_right = new_left + view_width
            elif new_right > max_right:
                new_right = max_right
                new_left = new_right - view_width

        fa_ax.set_xlim(new_left, new_right)
        fa_canvas.draw_idle()


def on_canvas_release(event):
    """Stops the panning for the TOP screen."""
    global pan_start_x
    pan_start_x = None
    canvas.get_tk_widget().config(cursor="hand2")


# --- NEW: Final Answer Panning Functions ---
def on_fa_canvas_press(event):
    """Records the starting X position for the BOTTOM screen."""
    global fa_pan_start_x, fa_initial_xlim
    if event.button == 1:
        fa_pan_start_x = event.x
        fa_initial_xlim = fa_ax.get_xlim()
        fa_canvas.get_tk_widget().config(cursor="fleur")


def on_fa_canvas_release(event):
    """Stops the panning for the BOTTOM screen."""
    global fa_pan_start_x
    fa_pan_start_x = None
    fa_canvas.get_tk_widget().config(cursor="hand2")


# --- UI Action Functions ---
def set_final_answer(text_content):
    """Translates the text to LaTeX and draws it on the Matplotlib Canvas."""
    fa_ax.clear()
    fa_ax.axis("off")

    # Reset the camera view back to the left edge
    fa_ax.set_xlim(0, 1)
    fa_ax.set_ylim(0, 1)

    display_text = text_content

    # If the answer contains math (has an '=' sign and isn't an Error)
    if "FINAL ANSWER:" in text_content and "=" in text_content and "Error" not in text_content:
        raw_math = text_content.replace("FINAL ANSWER:", "").strip()
        decimal_part = ""

        # Split off the "(or approx...)" part if it exists
        if "(or" in raw_math:
            parts = raw_math.split("(or")
            raw_math = parts[0].strip()
            decimal_part = " (or " + parts[1].strip()

        try:
            lhs, rhs = raw_math.split("=")
            lhs_expr = sp.sympify(lhs, evaluate=False)
            rhs_expr = sp.sympify(rhs, evaluate=False)

            lhs_latex = sp.latex(lhs_expr)
            rhs_latex = sp.latex(rhs_expr)

            # Clean up SymPy's fraction formatting to make it look beautiful
            rhs_latex = re.sub(r'([0-9A-Za-z]+)\s*\\cdot\s*\\frac\{1\}\{([0-9A-Za-z]+)\}', r'\\frac{\1}{\2}', rhs_latex)
            rhs_latex = re.sub(r'(\d)\s*\\cdot\s*([A-Za-z])', r'\1\2', rhs_latex)

            # Combine the Bold text, the LaTeX math, and the decimal string
            display_text = f"$\\mathbf{{FINAL\\ ANSWER:}}$ ${lhs_latex} = {rhs_latex}$" + decimal_part
        except Exception:
            pass  # If the math parser fails, safely fall back to plain text

    # Draw the final result onto the canvas
    fa_ax.text(0.02, 0.5, display_text, size=16, ha="left", va="center", color="blue")
    fa_canvas.draw()


def block_keyboard_typing(event):
    """Allows letters, numbers, math operators, and handles operator replacement."""
    if event.keysym in ['Left', 'Right', 'BackSpace', 'Delete']:
        return None

    allowed_symbols = ['+', '-', '*', '/', '=', '(', ')', '.', '^']
    if event.char.isdigit() or event.char in allowed_symbols:

        # Intercept physical keyboard stacking operators
        operators = ['+', '-', '*', '/', '^']
        if event.char in operators:
            cursor_pos = screen.index(tk.INSERT)
            current_text = raw_display_var.get()

            if cursor_pos > 0 and current_text[cursor_pos - 1] in operators:
                # Replace the old operator with the typed one
                new_text = current_text[:cursor_pos - 1] + event.char + current_text[cursor_pos:]
                raw_display_var.set(new_text)
                screen.icursor(cursor_pos)
                return "break"

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

    # Prevent stacking operators by replacing the last one
    operators = ['+', '-', '*', '/', '^']
    if char_str in operators and cursor_pos > 0:
        if current_text[cursor_pos - 1] in operators:
            new_text = current_text[:cursor_pos - 1] + char_str + current_text[cursor_pos:]
            raw_display_var.set(new_text)
            screen.icursor(cursor_pos)
            screen.focus()
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
    set_final_answer("$\\mathbf{FINAL\\ ANSWER:}$ ")
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

    invalid_combos = ['+-', '-+', '++', '--', '*/', '/*', '+*', '+/', '-*', '-/', '..']

    for combo in invalid_combos:
        if combo in raw_equation:
            trail_display.insert(tk.END, "[VALIDATION STATUS: FAIL]\n")
            messagebox.showwarning("Syntax Error",
                                   f"Invalid math formatting: '{combo}' is not allowed. Please clean up your operators.")
            return

    math_equation = sanitize_math_string(raw_equation)
    set_final_answer("$\\mathbf{FINAL\\ ANSWER:}$ Computing...")
    root.update()

    # Ask the Math Engine for the answer and steps
    chosen_method = solver_method.get()
    final_answer, trail_steps = solve_linear_equation(math_equation, solve_for, chosen_method)

    if final_answer == "Error":
        trail_display.insert(tk.END, "[VALIDATION STATUS: FAIL]\n\n")
        display_solution_trail(trail_display, trail_steps)
        set_final_answer("$\\mathbf{FINAL\\ ANSWER:}$ Error")
        messagebox.showerror("Computation Error", trail_steps[0][1])
    else:
        # This now correctly handles numbers, "No Solution", and "Infinite Solutions" as PASS!
        trail_display.insert(tk.END, "[VALIDATION STATUS: PASS]\n\n")
        display_solution_trail(trail_display, trail_steps)

        # If it's a special text answer, format it nicely without the equals sign
        if final_answer in ["No Solution", "Infinite Solutions"]:
            set_final_answer(f"$\\mathbf{{FINAL\\ ANSWER:}}$ {final_answer}")
        else:
            set_final_answer(f"FINAL ANSWER: {final_answer}")

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

# TOP MATPLOTLIB CANVAS
fig = Figure(figsize=(4.5, 1.2), dpi=100)
fig.patch.set_facecolor('#e8f4f8')
ax = fig.add_subplot(111)
ax.axis("off")
ax.text(1.0, 0.5, "0", size=20, ha="right", va="center")

canvas = FigureCanvasTkAgg(fig, master=left_frame)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(fill=tk.X, pady=(0, 5))
canvas_widget.config(cursor="hand2")

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
    ('4', 1, 0), ('5', 1, 1), ('6', 1, 2), ('*', 1, 3), ('/', 1, 4),
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
options_frame.pack(pady=(15, 0), fill=tk.X)

var_frame = tk.Frame(options_frame)
var_frame.pack(anchor="w")
tk.Label(var_frame, text="Solve for:", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT, padx=5)

target_var = tk.StringVar()
radio_buttons_inner_frame = tk.Frame(var_frame)
radio_buttons_inner_frame.pack(side=tk.LEFT)

# --- NEW: Symbolic Method Selection Row ---
method_frame = tk.Frame(options_frame)
method_frame.pack(anchor="w", pady=(10, 0))
tk.Label(method_frame, text="Method:", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT, padx=5)

solver_method = tk.StringVar(value="standard")
tk.Radiobutton(method_frame, text="Standard Form (Ax + B = 0)", variable=solver_method, value="standard", font=("Helvetica", 10)).pack(side=tk.LEFT)
tk.Radiobutton(method_frame, text="Two-Sided Balancing (Ax = C)", variable=solver_method, value="balancing", font=("Helvetica", 10)).pack(side=tk.LEFT)

tk.Button(left_frame, text="COMPUTE", font=("Helvetica", 12, "bold"), bg="#99ff99", height=2,
          command=compute_action).pack(fill=tk.X, pady=(15, 0))

# ==========================================
# RIGHT FRAME: The Output & Solution Trail
# ==========================================
right_frame = tk.Frame(root)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# NEW: BOTTOM MATPLOTLIB CANVAS (The Final Answer Display)
fa_fig = Figure(figsize=(5.0, 0.6), dpi=100)
fa_fig.patch.set_facecolor('#f0f8ff')
fa_ax = fa_fig.add_subplot(111)
fa_ax.axis("off")
fa_ax.set_xlim(0, 1)
fa_ax.set_ylim(0, 1)
fa_ax.text(0.02, 0.5, "$\\mathbf{FINAL\\ ANSWER:}$ ", size=16, ha="left", va="center", color="blue")

fa_canvas = FigureCanvasTkAgg(fa_fig, master=right_frame)
fa_canvas_widget = fa_canvas.get_tk_widget()
fa_canvas_widget.config(cursor="hand2", relief=tk.RIDGE, bd=3)
fa_canvas_widget.pack(fill=tk.X, pady=(0, 15))

# Bind the panning mouse events for the bottom screen!
fa_canvas.mpl_connect('button_press_event', on_fa_canvas_press)
fa_canvas.mpl_connect('motion_notify_event', on_fa_canvas_drag)
fa_canvas.mpl_connect('button_release_event', on_fa_canvas_release)

tk.Label(right_frame, text="Solution Trail & Auditing:", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 5))

trail_display = scrolledtext.ScrolledText(right_frame, font=("Consolas", 11), bg="#f9f9f9", wrap=tk.WORD, bd=3,
                                          relief=tk.SUNKEN)
trail_display.pack(fill=tk.BOTH, expand=True)

update_variable_options()

if __name__ == "__main__":
    root.mainloop()