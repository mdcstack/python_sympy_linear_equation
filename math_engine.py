import sympy as sp


def solve_linear_equation(equation_str, target_var_str):
    """Calculates the answer and generates a detailed step-by-step list."""
    steps = []
    try:
        if equation_str.count("=") != 1:
            return "Error", [("text", "Invalid formatting. Please use exactly one '=' sign.")]

        lhs_str, rhs_str = equation_str.split("=", 1)
        v = sp.Symbol(target_var_str)

        # THE FIX: Parse with evaluate=False to preserve the exact GIVEN order
        LHS_raw = sp.sympify(lhs_str, evaluate=False)
        RHS_raw = sp.sympify(rhs_str, evaluate=False)

        steps.append(("text", "GIVEN:"))
        steps.append(("math", sp.Eq(LHS_raw, RHS_raw, evaluate=False)))
        steps.append(("text", f"Solve for: {v}\n"))
        steps.append(("text", "METHOD: Deterministic Algorithmic Isolation\n"))

        # Now parse them normally so the computer can actually do math
        LHS = sp.sympify(lhs_str)
        RHS = sp.sympify(rhs_str)

        # STEP 1
        steps.append(("text", "1. Move everything to the left side to equal zero (LHS - RHS = 0):"))
        collected_expr = LHS - RHS
        steps.append(("math", sp.Eq(collected_expr, 0, evaluate=False)))

        if not collected_expr.has(v):
            return "Error", [("text", f"The variable '{v}' is not in the equation!")]

        # Error Checks
        num, den = sp.fraction(sp.cancel(collected_expr))
        if den.has(v):
            return "Error", [("text", f"Not a linear equation. Variable '{v}' is in a denominator.")]
        if sp.degree(collected_expr, v) > 1:
            return "Error", [("text", f"Not a linear equation. Variable '{v}' has an exponent.")]

        # STEP 2
        steps.append(("text", "2. Expand all parentheses and distribute terms:"))
        expanded_expr = sp.expand(collected_expr)
        steps.append(("math", sp.Eq(expanded_expr, 0, evaluate=False)))

        # STEP 3
        steps.append(("text", f"3. Factor out the target variable '{v}':"))
        factored_expr = sp.collect(expanded_expr, v)
        steps.append(("math", sp.Eq(factored_expr, 0, evaluate=False)))

        # STEP 4
        A = factored_expr.coeff(v)
        B = factored_expr.subs(v, 0)

        steps.append(("text", f"4. Identify the coefficients (A*{v} + B = 0):"))
        steps.append(("text", f"   A = {A}"))
        steps.append(("text", f"   B = {B}\n"))

        if A == 0:
            return "No Solution", [("text", f"No Solution: The variable '{v}' cancels out.")]

        # STEP 5
        steps.append(("text", f"5. Move the remainder to the right side (A*{v} = -B):"))
        steps.append(("math", sp.Eq(A * v, -B, evaluate=False)))

        # STEP 6
        steps.append(("text", f"6. Isolate '{v}' by dividing both sides by A (-B / A):"))
        answer = sp.simplify(-B / A)

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