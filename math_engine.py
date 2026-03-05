import sympy as sp


def solve_linear_equation(equation_str, target_var_str):
    """Calculates the answer and generates a highly educational, extremely detailed 7-step list."""
    steps = []
    try:
        if equation_str.count("=") != 1:
            return "Error", [("text", "Invalid formatting. Please use exactly one '=' sign.")]

        lhs_str, rhs_str = equation_str.split("=", 1)
        v = sp.Symbol(target_var_str)

        # Parse safely to preserve the exact GIVEN order
        LHS_raw = sp.sympify(lhs_str, evaluate=False)
        RHS_raw = sp.sympify(rhs_str, evaluate=False)

        steps.append(("text", "GIVEN:"))
        steps.append(("math", sp.Eq(LHS_raw, RHS_raw, evaluate=False)))
        steps.append(("text", f"Solve for: {v}\n"))
        steps.append(("text", "METHOD: Deterministic Algorithmic Isolation\n"))

        LHS = sp.sympify(lhs_str)
        RHS = sp.sympify(rhs_str)

        # STEP 1: The true "Move to left" visual (LHS - (RHS) = 0)
        steps.append(("text", "1. Move all terms to the left side by subtracting the right side (LHS - RHS = 0):"))
        step1_expr = sp.Add(LHS_raw, sp.Mul(-1, RHS_raw, evaluate=False), evaluate=False)
        steps.append(("math", sp.Eq(step1_expr, 0, evaluate=False)))

        # Validate the equation safely
        collected_expr = sp.simplify(LHS - RHS)
        if not collected_expr.has(v) and collected_expr != 0:
            return "Error", [("text", f"The variable '{v}' is not in the equation!")]

        num, den = sp.fraction(sp.cancel(LHS - RHS))
        if den.has(v):
            return "Error", [("text", f"Not a linear equation. Variable '{v}' is in a denominator.")]
        if sp.degree(collected_expr, v) > 1:
            return "Error", [("text", f"Not a linear equation. Variable '{v}' has an exponent.")]

        # STEP 2: Explicitly show parentheses expanding
        steps.append(("text", "2. Expand any parentheses and distribute multiplication:"))
        expanded_expr = sp.expand(LHS - RHS)
        steps.append(("math", sp.Eq(expanded_expr, 0, evaluate=False)))

        # STEP 3: Combine Like terms
        steps.append(("text", "3. Combine all like terms to create the simplified standard form:"))
        steps.append(("math", sp.Eq(collected_expr, 0, evaluate=False)))

        A = collected_expr.coeff(v)
        B = collected_expr - (A * v)

        if A == 0:
            return "No Solution", [("text", f"No Solution: The variable '{v}' cancels out.")]

        # STEP 4: Identify A and B explicitly for the student
        steps.append(("text", f"4. Identify the coefficient (A) and the constant (B) for the format A*{v} + B = 0:"))
        steps.append(("text", f"   Coefficient A = {A}"))
        steps.append(("text", f"   Constant B = {B}\n"))

        # STEP 5: Move the constant
        steps.append(("text", f"5. Move the constant ({B}) to the right side by subtracting it from both sides:"))
        ax_expr = sp.Mul(A, v, evaluate=False)
        steps.append(("math", sp.Eq(ax_expr, -B, evaluate=False)))

        # STEP 6: The explicit division fraction
        steps.append(("text", f"6. To isolate '{v}', divide both sides by the coefficient ({A}):"))
        latex_A = sp.latex(A)
        latex_negB = sp.latex(-B)
        latex_v = sp.latex(v)
        steps.append(("math", f"${latex_v} = \\frac{{{latex_negB}}}{{{latex_A}}}$"))

        # STEP 7: Final Answer
        answer = sp.simplify(-B / A)
        steps.append(("text", "7. Simplify the fraction to calculate the final exact answer:"))

        if answer.is_number and not answer.is_Integer:
            decimal_answer = round(float(answer.evalf()), 4)
            steps.append(("math", sp.Eq(v, answer, evaluate=False)))
            steps.append(("text", f"   (or approx {decimal_answer})"))
            final_answer = f"{v} = {answer} (or {decimal_answer})"
        else:
            steps.append(("math", sp.Eq(v, answer, evaluate=False)))
            final_answer = f"{v} = {answer}"

        return final_answer, steps

    except ZeroDivisionError:
        return "Error", [("text", "Division by zero detected. Please check your math.")]
    except Exception as e:
        return "Error", [("text", "Invalid math formatting. Please check your equation.")]