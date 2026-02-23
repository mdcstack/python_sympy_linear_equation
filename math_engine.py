import sympy as sp
import time
from datetime import datetime
import re


def clean_trail_string(text):
    """Removes the implicit '*' from the final output text to look like human algebra."""
    # Remove '*' between a number and a letter (e.g., '2*x' -> '2x')
    text = re.sub(r'(\d)\*([A-Za-z])', r'\1\2', text)
    # Remove '*' between a number and a parenthesis (e.g., '2*(' -> '2(')
    text = re.sub(r'(\d)\*(\()', r'\1\2', text)
    return text


def solve_linear_equation(equation_string, target_var_str):
    """
    Solves a linear equation step-by-step strictly using algorithmic logic.
    Returns: (final_answer_string, full_solution_trail_string)
    """
    start_time = time.time()
    v = sp.Symbol(target_var_str)

    if '=' not in equation_string:
        return "Error", "Equation must contain an '=' sign."

    lhs_str, rhs_str = equation_string.split('=', 1)

    try:
        LHS = sp.sympify(lhs_str)
        RHS = sp.sympify(rhs_str)
    except Exception:
        # Instead of showing the raw computer error, we return a friendly human message!
        return "Error", "Invalid math formatting. Please check for incomplete equations or missing numbers."

    steps = []

    # --- STEP 1: Identify sides ---
    steps.append(f"1. Identify the Left and Right sides:\n   LHS = {LHS}\n   RHS = {RHS}")

    # --- STEP 2: Move to one side ---
    expr = LHS - RHS
    steps.append(f"2. Move all terms to the left side (LHS - RHS = 0):\n   {expr} = 0")

    # --- STEP 3: Expand ---
    expanded_expr = sp.expand(expr)
    if expanded_expr != expr:
        steps.append(f"3. Expand the expression:\n   {expanded_expr} = 0")
        expr = expanded_expr

    # --- STEP 4: Collect terms ---
    collected_expr = sp.collect(expr, v)
    steps.append(f"4. Group terms containing the target variable '{v}':\n   {collected_expr} = 0")

    # --- Ensure it is actually a Linear Equation ---
    try:
        if sp.degree(collected_expr, v) > 1:
            return "Error", f"Not a linear equation. The variable '{v}' has an exponent."
    except Exception:
        pass

        # --- STEP 5: Extract A and B (A*v + B = 0) ---
    A = collected_expr.coeff(v)
    B = collected_expr.subs(v, 0)

    if A == 0:
        return "No Solution", f"The variable '{v}' cancels out of the equation."

    steps.append(f"5. Identify the coefficient (A) and the constants (B):\n   A = {A}\n   B = {B}")

    # --- STEP 6: Move B to the right ---
    steps.append(f"6. Move the constants to the right side (A*{v} = -B):\n   {A * v} = {-B}")

    # --- STEP 7: Divide and Solve ---
    answer = sp.simplify(-B / A)

    # NEW: Calculate the decimal version if it's a fraction
    if answer.is_number and not answer.is_Integer:
        decimal_answer = round(float(answer.evalf()), 4)  # Round to 4 decimal places for clean UI
        steps.append(f"7. Divide by the coefficient A to isolate '{v}':\n   {v} = {answer}  (or {decimal_answer})")
        final_answer = f"{v} = {answer}  (or {decimal_answer})"
    else:
        steps.append(f"7. Divide by the coefficient A to isolate '{v}':\n   {v} = {answer}")
        final_answer = f"{v} = {answer}"

    # ==========================================
    # AUDITING: Symbolic Substitution Back-Check
    # ==========================================
    try:
        lhs_check = sp.simplify(LHS.subs(v, answer))
        rhs_check = sp.simplify(RHS.subs(v, answer))

        if sp.simplify(lhs_check - rhs_check) == 0:
            verification = f"Substitution check passed:\nLHS ({lhs_check}) == RHS ({rhs_check})"
        else:
            verification = f"Substitution check failed. \nLHS ({lhs_check}) != RHS ({rhs_check})"
    except Exception as e:
        verification = f"Could not verify automatically: {e}"

    # ==========================================
    # FORMATTING: Standard Trail Format
    # ==========================================
    runtime = round(time.time() - start_time, 4)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    summary = f"Runtime: {runtime}s | Iterations: 1 | Timestamp: {timestamp} | SymPy {sp.__version__}"

    # Stitch everything together
    trail = f"GIVEN: {equation_string} | Solve for: {target_var_str}\n\n"
    trail += f"METHOD: Deterministic Algorithmic Isolation\n\n"
    trail += "STEPS:\n" + "\n\n".join(steps) + "\n\n"
    trail += f"FINAL ANSWER: {final_answer}\n\n"
    trail += f"VERIFICATION:\n{verification}\n\n"
    trail += f"SUMMARY:\n{summary}"

    # NEW: Run our cleaner across all the generated text before returning it!
    final_answer = clean_trail_string(final_answer)
    trail = clean_trail_string(trail)

    return final_answer, trail