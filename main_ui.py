import tkinter as tk
from tkinter import scrolledtext, messagebox
import sympy as sp
import matplotlib
import re
from math_engine import solve_linear_equation

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


# --- UI Action Functions ---
def block_keyboard_typing(event):
    if event.keysym in ['Left', 'Right']:
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
    new_text = current_text[:cursor_pos] + "()÷()" + current_text[cursor_pos:]
    raw_display_var.set(new_text)
    screen.icursor(cursor_pos + 1)
    screen.focus()


def sanitize_math_string(raw_str):
    """Converts UI string into SymPy-friendly string with explicit multiplication."""
    # 1. Swap our custom UI symbols for Python math operators
    text = raw_str.replace('÷', '/').replace('^', '**')

    # 2. Insert '*' between a Number and a Letter/Parenthesis (e.g., "2x" -> "2*x", "2(" -> "2*(")
    text = re.sub(r'(\d)([A-Za-z\(])', r'\1*\2', text)

    # 3. Insert '*' between a Letter and a Parenthesis (e.g., "x(" -> "x*(")
    text = re.sub(r'([A-Za-z])(\()', r'\1*\2', text)

    # 4. Insert '*' between a closing Parenthesis and a Letter/Number/Parenthesis (e.g., ")x" -> ")*x")
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

            # NEW: Clean the LaTeX to remove the dot between numbers and letters!
            lhs_latex = re.sub(r'(\d)\s*\\cdot\s*([A-Za-z])', r'\1\2', lhs_latex)
            rhs_latex = re.sub(r'(\d)\s*\\cdot\s*([A-Za-z])', r'\1\2', rhs_latex)

            pretty_math = f"${lhs_latex} = {rhs_latex}$"
        else:
            expr = sp.sympify(math_text, evaluate=False)
            expr_latex = sp.latex(expr, mul_symbol='dot', order='none')

            # NEW: Clean the LaTeX here as well
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

    if not raw_equation or "=" not in raw_equation:
        messagebox.showwarning("Input Error", "Please enter a complete equation with an '=' sign.")
        return

    if not solve_for:
        messagebox.showwarning("Input Error", "No variable detected to solve for.")
        return

    # NEW: Use our sanitizer function before passing to the math engine!
    math_equation = sanitize_math_string(raw_equation)

    final_answer_label.config(text="FINAL ANSWER: Computing...")
    trail_display.delete(1.0, tk.END)

    # CALL OUR NEW MATH ENGINE
    final_answer, trail_text = solve_linear_equation(math_equation, solve_for)

    # DISPLAY THE RESULTS
    final_answer_label.config(text=f"FINAL ANSWER: {final_answer}")
    trail_display.insert(tk.END, trail_text)

# --- Main Window Setup ---
root = tk.Tk()
root.title("Linear Equation Calculator")
root.geometry("950x620")  # Changed to a wide desktop layout
root.resizable(False, False)
root.configure(padx=20, pady=20)

# ==========================================
# LEFT FRAME: The Calculator Input & Keypad
# ==========================================
left_frame = tk.Frame(root)
left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))

# 1. The Pretty Print Screen
fig = Figure(figsize=(4.5, 1.2), dpi=100)
fig.patch.set_facecolor('#e8f4f8')
ax = fig.add_subplot(111)
ax.axis("off")
ax.text(1.0, 0.5, "0", size=20, ha="right", va="center")

canvas = FigureCanvasTkAgg(fig, master=left_frame)
canvas.get_tk_widget().pack(fill=tk.X, pady=(0, 5))

# 2. The Raw Input Screen
raw_display_var = tk.StringVar()
raw_display_var.trace_add("write", on_text_change)

screen = tk.Entry(left_frame, textvariable=raw_display_var, font=("Consolas", 14), justify="right", bd=5,
                  relief=tk.SUNKEN)
screen.pack(fill=tk.X, pady=(0, 15))
screen.bind("<Key>", block_keyboard_typing)

# 3. The Keypad Area
keypad_frame = tk.Frame(left_frame)
keypad_frame.pack()

buttons = [
    ('7', 0, 0), ('8', 0, 1), ('9', 0, 2), ('(', 0, 3), (')', 0, 4),
    ('4', 1, 0), ('5', 1, 1), ('6', 1, 2), ('*', 1, 3), ('÷', 1, 4),
    ('1', 2, 0), ('2', 2, 1), ('3', 2, 2), ('+', 2, 3), ('-', 2, 4),
    ('0', 3, 0), ('.', 3, 1), ('x', 3, 2), ('y', 3, 3), ('^', 3, 4),
    ('C', 4, 0), ('Del', 4, 1), ('=', 4, 2), ('a/b', 4, 3)
]

for text, row, col in buttons:
    if text == 'C':
        action = clear_all;
        bg_color = "#ff9999"
    elif text == 'Del':
        action = delete_last;
        bg_color = "#ffcc99"
    elif text == 'a/b':
        action = insert_fraction;
        bg_color = "#b3d9ff"
    else:
        action = lambda char=text: button_click(char);
        bg_color = "#f0f0f0"

    tk.Button(keypad_frame, text=text, width=4, height=2, font=("Helvetica", 12, "bold"),
              bg=bg_color, command=action).grid(row=row, column=col, padx=2, pady=2)

# 4. The Action Buttons
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

# Made the text box much larger to utilize the new space
trail_display = scrolledtext.ScrolledText(right_frame, font=("Consolas", 11), bg="#f9f9f9", wrap=tk.WORD, bd=3,
                                          relief=tk.SUNKEN)
trail_display.pack(fill=tk.BOTH, expand=True)

update_variable_options()

if __name__ == "__main__":
    root.mainloop()