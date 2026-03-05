import sympy as sp
from functools import reduce


def get_expanded_terms(expr):
    """Helper function to expand parentheses without letting SymPy combine like terms."""
    terms = []
    if isinstance(expr, sp.Add):
        for arg in expr.args:
            expanded_arg = sp.expand(arg)
            if isinstance(expanded_arg, sp.Add):
                terms.extend(expanded_arg.args)
            else:
                terms.append(expanded_arg)
    else:
        expanded_arg = sp.expand(expr)
        if isinstance(expanded_arg, sp.Add):
            terms.extend(expanded_arg.args)
        else:
            terms.append(expanded_arg)
    return terms


def solve_linear_equation(equation_str, target_var_str):
    """Calculates the answer and dynamically verifies it using strict AST substitution."""
    steps = []
    try:
        if equation_str.count("=") != 1:
            return "Error", [("text", "Invalid formatting. Please use exactly one '=' sign.")]

        lhs_str, rhs_str = equation_str.split("=", 1)
        v = sp.Symbol(target_var_str)

        LHS_raw = sp.sympify(lhs_str, evaluate=False)
        RHS_raw = sp.sympify(rhs_str, evaluate=False)

        steps.append(("text", "GIVEN:"))
        steps.append(("math", sp.Eq(LHS_raw, RHS_raw, evaluate=False)))
        steps.append(("text", f"Solve for: {v}\n"))
        steps.append(("text", "METHOD: Deterministic Algorithmic Isolation\n"))

        LHS = sp.sympify(lhs_str)
        RHS = sp.sympify(rhs_str)

        step_count = 1

        collected_expr = sp.simplify(LHS - RHS)
        if not collected_expr.has(v) and collected_expr != 0:
            return "Error", [("text", f"The variable '{v}' is not in the equation!")]

        num, den = sp.fraction(sp.cancel(LHS - RHS))
        if den.has(v):
            return "Error", [("text", f"Not a linear equation. Variable '{v}' is in a denominator.")]
        if sp.degree(collected_expr, v) > 1:
            return "Error", [("text", f"Not a linear equation. Variable '{v}' has an exponent.")]

        # DYNAMIC STEP: Move to left
        if RHS_raw != sp.Integer(0):
            steps.append(("text",
                          f"{step_count}. Move all terms to the left side by subtracting the right side (LHS - RHS = 0):"))
            rhs_in_parens = sp.Mul(-1, RHS_raw, evaluate=False)
            step1_expr = sp.Add(LHS_raw, rhs_in_parens, evaluate=False)
            steps.append(("math", sp.Eq(step1_expr, 0, evaluate=False)))
            step_count += 1
        else:
            step1_expr = LHS_raw

        # DYNAMIC STEP: Clear Fractions
        dens = list(set([atom.q for atom in step1_expr.atoms(sp.Rational) if atom.q != 1]))
        if dens:
            lcm_val = reduce(sp.lcm, dens)
            if lcm_val > 1:
                steps.append(("text",
                              f"{step_count}. Clear the fractions by multiplying the entire equation by the Least Common Multiple ({lcm_val}):"))
                step1_expr = sp.expand(step1_expr * lcm_val)
                steps.append(("math", sp.Eq(step1_expr, 0, evaluate=False)))
                step_count += 1

        # DYNAMIC STEP: Expand
        expanded_terms = get_expanded_terms(step1_expr)
        expanded_uncombined_expr = sp.Add(*expanded_terms, evaluate=False)

        if str(step1_expr) != str(expanded_uncombined_expr):
            steps.append(
                ("text", f"{step_count}. Expand parentheses by distributing the multiplication and negative signs:"))
            steps.append(("math", sp.Eq(expanded_uncombined_expr, 0, evaluate=False)))
            step_count += 1

        # DYNAMIC STEP: Grouping & Combining
        v_terms = [t for t in expanded_terms if t.has(v)]
        c_terms = [t for t in expanded_terms if not t.has(v)]

        group_v = sp.Add(*v_terms, evaluate=False) if v_terms else sp.Integer(0)
        group_c = sp.Add(*c_terms, evaluate=False) if c_terms else sp.Integer(0)

        if len(v_terms) > 1 or len(c_terms) > 1:
            steps.append(
                ("text", f"{step_count}. Group the variable terms together, and the constant numbers together:"))
            latex_v = sp.latex(group_v)
            latex_c = sp.latex(group_c)
            steps.append(("math", f"$\\left({latex_v}\\right) + \\left({latex_c}\\right) = 0$"))

            if len(v_terms) > 1:
                simplified_v = sp.simplify(group_v)
                steps.append(("text", f"   {step_count}.1 Calculate the sum of the grouped variable terms:"))
                steps.append(("math", f"${latex_v} = {sp.latex(simplified_v)}$"))

            if len(c_terms) > 1:
                simplified_c = sp.simplify(group_c)
                steps.append(("text", f"   {step_count}.2 Calculate the sum of the grouped constant numbers:"))
                steps.append(("math", f"${latex_c} = {sp.latex(simplified_c)}$"))
            step_count += 1

            collected_expr = sp.simplify(step1_expr)
            steps.append(("text",
                          f"{step_count}. Substitute these calculated sums back into the equation to get the simplified standard form:"))
            steps.append(("math", sp.Eq(collected_expr, 0, evaluate=False)))
            step_count += 1
        else:
            collected_expr = sp.simplify(step1_expr)

        A = collected_expr.coeff(v)
        B = collected_expr - (A * v)

        if A == 0:
            return "No Solution", [("text", f"No Solution: The variable '{v}' cancels out.")]

        # DYNAMIC STEP: Identify A and B
        steps.append(
            ("text", f"{step_count}. Identify the coefficient (A) and the constant (B) for the format A*{v} + B = 0:"))
        steps.append(("text", f"   Coefficient A = {A}"))
        steps.append(("text", f"   Constant B = {B}\n"))
        step_count += 1

        # DYNAMIC STEP: Move the constant
        if B != 0:
            steps.append(
                ("text", f"{step_count}. Move the constant ({B}) to the right side by subtracting it from both sides:"))
            ax_expr = sp.Mul(A, v, evaluate=False)
            steps.append(("math", sp.Eq(ax_expr, -B, evaluate=False)))
            step_count += 1
        else:
            ax_expr = sp.Mul(A, v, evaluate=False)

        # DYNAMIC STEP: Explicit division fraction
        if A != 1:
            steps.append(("text", f"{step_count}. To isolate '{v}', divide both sides by the coefficient ({A}):"))
            latex_A = sp.latex(A)
            latex_negB = sp.latex(-B)
            latex_v = sp.latex(v)
            steps.append(("math", f"${latex_v} = \\frac{{{latex_negB}}}{{{latex_A}}}$"))

            answer = sp.simplify(-B / A)
            if sp.fraction(answer)[1] != 1 and A not in [1, -1, 0]:
                gcd_val = sp.gcd(-B, A)
                if gcd_val > 1:
                    steps.append(("text",
                                  f"   {step_count}.1 Find the Greatest Common Divisor (GCD) of the numerator and denominator to simplify. The GCD of {-B} and {A} is {gcd_val}:"))
                    steps.append(("math", f"${latex_v} = \\frac{{{-B} \\div {gcd_val}}}{{{A} \\div {gcd_val}}}$"))
            step_count += 1
        else:
            answer = sp.simplify(-B / A)

        # FINAL COMPUTATION STEP
        steps.append(("text", f"{step_count}. Write the final simplified answer:"))

        if answer.is_number and not answer.is_Integer:
            decimal_answer = round(float(answer.evalf()), 4)
            steps.append(("math", sp.Eq(v, answer, evaluate=False)))
            steps.append(("text", f"   (or approx {decimal_answer})"))
            final_answer = f"{v} = {answer} (or {decimal_answer})"
        else:
            steps.append(("math", sp.Eq(v, answer, evaluate=False)))
            final_answer = f"{v} = {answer}"

        step_count += 1

        # ==========================================
        # NEW: THE FRACTION-PROOF VERIFICATION STEP
        # ==========================================
        steps.append(("text",
                      f"\n{step_count}. Verify the answer by substituting ({answer}) back into the original equation for '{v}':"))

        # We use sp.UnevaluatedExpr to perfectly substitute the answer into the math structure
        # without allowing SymPy to automatically calculate the result yet!
        visual_ans = sp.UnevaluatedExpr(answer)
        visual_lhs = LHS_raw.subs(v, visual_ans)
        visual_rhs = RHS_raw.subs(v, visual_ans)

        steps.append(("math", sp.Eq(visual_lhs, visual_rhs, evaluate=False)))

        # Evaluate both sides completely to check the math
        lhs_eval = sp.simplify(LHS.subs(v, answer))
        rhs_eval = sp.simplify(RHS.subs(v, answer))

        steps.append(("text", f"   {step_count}.1 Evaluate the arithmetic on both sides to confirm they match:"))
        steps.append(("math", sp.Eq(lhs_eval, rhs_eval, evaluate=False)))

        if lhs_eval == rhs_eval:
            steps.append(("text", f"   ✅ Both sides equal {lhs_eval}. The answer is officially verified!"))
        else:
            steps.append(("text", "   ❌ Verification failed. (Check for rounding errors)."))

        return final_answer, steps

    except ZeroDivisionError:
        return "Error", [("text", "Division by zero detected. Please check your math.")]
    except Exception as e:
        return "Error", [("text", "Invalid math formatting. Please check your equation.")]