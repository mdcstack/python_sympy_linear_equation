import sympy as sp


def solve_balancing_method(equation_str, target_var_str):
    """Calculates the answer using Two-Sided Equation Balancing (Ax = C) with explicit sub-steps."""
    steps = []
    try:
        if equation_str.count("=") != 1:
            return "Error", [("text", "[STOPPING RULE]: Invalid formatting. Process halted.")]

        lhs_str, rhs_str = equation_str.split("=", 1)
        v = sp.Symbol(target_var_str)

        LHS_raw = sp.sympify(lhs_str, evaluate=False)
        RHS_raw = sp.sympify(rhs_str, evaluate=False)

        steps.append(("text", "GIVEN:"))
        steps.append(("math", sp.Eq(LHS_raw, RHS_raw, evaluate=False)))
        steps.append(("text", f"Solve for: {v}\n"))
        steps.append(("text", "METHOD: Two-Sided Equation Balancing (Variables Left, Constants Right)\n"))

        LHS = sp.sympify(lhs_str)
        RHS = sp.sympify(rhs_str)

        # EARLY VALIDATION
        if not LHS_raw.has(v) and not RHS_raw.has(v):
            return "Error", [("text", f"[STOPPING RULE]: Variable '{v}' is entirely missing. Process halted.")]

        step_count = 1

        # 1. Expand both sides
        lhs_exp = sp.expand(LHS)
        rhs_exp = sp.expand(RHS)
        if lhs_exp != LHS or rhs_exp != RHS:
            steps.append(("text", f"{step_count}. Expand parentheses on both sides independently:"))
            steps.append(("math", sp.Eq(lhs_exp, rhs_exp, evaluate=False)))
            step_count += 1

        # 2. Extract coefficients for the scale
        A_left = sp.simplify(lhs_exp).coeff(v)
        B_left = sp.simplify(lhs_exp) - (A_left * v)
        A_right = sp.simplify(rhs_exp).coeff(v)
        B_right = sp.simplify(rhs_exp) - (A_right * v)

        steps.append(("text", f"{step_count}. Group variables and constants on each side of the equals sign:"))
        steps.append(("math",
                      sp.Eq(sp.Add(A_left * v, B_left, evaluate=False), sp.Add(A_right * v, B_right, evaluate=False),
                            evaluate=False)))
        step_count += 1

        # 3. Move Variables Left
        if A_right != 0:
            steps.append(("text",
                          f"{step_count}. Move the variable term ({A_right * v}) to the left side by subtracting it from both sides:"))

            # SUB-STEP: Show the literal subtraction on both sides
            lhs_sub = sp.Add(sp.Add(A_left * v, B_left, evaluate=False), sp.Mul(-1, A_right * v, evaluate=False),
                             evaluate=False)
            rhs_sub = sp.Add(sp.Add(A_right * v, B_right, evaluate=False), sp.Mul(-1, A_right * v, evaluate=False),
                             evaluate=False)
            steps.append(("math", sp.Eq(lhs_sub, rhs_sub, evaluate=False)))

            # SUB-STEP: Combine the math
            A_combined = sp.simplify(A_left - A_right)
            steps.append(("text", f"   {step_count}.1 Combine the variable terms on the left side:"))
            steps.append(("math", sp.Eq(sp.Add(A_combined * v, B_left, evaluate=False), B_right, evaluate=False)))

            step_count += 1
        else:
            A_combined = A_left

        # 4. Move Constants Right
        if B_left != 0:
            steps.append(("text",
                          f"{step_count}. Move the constant number ({B_left}) to the right side by subtracting it from both sides:"))

            # SUB-STEP: Show the literal subtraction on both sides
            lhs_sub2 = sp.Add(sp.Add(A_combined * v, B_left, evaluate=False), sp.Mul(-1, B_left, evaluate=False),
                              evaluate=False)
            rhs_sub2 = sp.Add(B_right, sp.Mul(-1, B_left, evaluate=False), evaluate=False)
            steps.append(("math", sp.Eq(lhs_sub2, rhs_sub2, evaluate=False)))

            # SUB-STEP: Combine the math
            C_combined = sp.simplify(B_right - B_left)
            steps.append(("text", f"   {step_count}.1 Combine the constant numbers on the right side:"))
            steps.append(("math", sp.Eq(A_combined * v, C_combined, evaluate=False)))

            step_count += 1
        else:
            C_combined = B_right

        # ==========================================
        # STOPPING RULES: IDENTITY & CONTRADICTION
        # ==========================================
        if A_combined == 0:
            if C_combined == 0:
                steps.append(("text",
                              "\n[STOPPING RULE MATCHED]: Variable canceled. Identity reached (0 = 0). Infinite solutions exist."))
                return "Infinite Solutions", steps
            else:
                steps.append(("text",
                              f"\n[STOPPING RULE MATCHED]: Variable canceled. Contradiction reached (0 = {C_combined}). No valid solution exists."))
                return "No Solution", steps

        # 5. Isolate
        if A_combined != 1:
            steps.append(
                ("text", f"{step_count}. To isolate '{v}', divide both sides by the coefficient ({A_combined}):"))
            latex_A = sp.latex(A_combined)
            latex_C = sp.latex(C_combined)
            steps.append(("math", f"${sp.latex(v)} = \\frac{{{latex_C}}}{{{latex_A}}}$"))

            answer = sp.simplify(C_combined / A_combined)

            # SUB-STEP: Fraction Simplification (GCD)
            if sp.fraction(answer)[1] != 1 and A_combined not in [1, -1, 0]:
                gcd_val = sp.gcd(C_combined, A_combined)
                if gcd_val > 1:
                    steps.append(("text",
                                  f"   {step_count}.1 Find the Greatest Common Divisor (GCD) of the numerator and denominator to simplify. The GCD of {C_combined} and {A_combined} is {gcd_val}:"))
                    steps.append(("math",
                                  f"${sp.latex(v)} = \\frac{{{C_combined} \\div {gcd_val}}}{{{A_combined} \\div {gcd_val}}}$"))

            step_count += 1
        else:
            answer = sp.simplify(C_combined / A_combined)

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

        # THE VERIFICATION STEP
        steps.append(("text",
                      f"\n{step_count}. Verify the answer by substituting ({answer}) back into the original equation for '{v}':"))
        visual_ans = sp.UnevaluatedExpr(answer)
        visual_lhs = LHS_raw.subs(v, visual_ans)
        visual_rhs = RHS_raw.subs(v, visual_ans)
        steps.append(("math", sp.Eq(visual_lhs, visual_rhs, evaluate=False)))

        lhs_eval = sp.simplify(LHS.subs(v, answer))
        rhs_eval = sp.simplify(RHS.subs(v, answer))
        steps.append(("text", f"   {step_count}.1 Evaluate the arithmetic on both sides to confirm they match:"))
        steps.append(("math", sp.Eq(lhs_eval, rhs_eval, evaluate=False)))

        if lhs_eval == rhs_eval:
            steps.append(("text", f"   ✅ Both sides equal {lhs_eval}. The answer is officially verified!"))
        else:
            steps.append(("text", "   ❌ Verification failed. (Check for rounding errors)."))

        steps.append(("text",
                      f"\n[STOPPING RULE MATCHED]: Exact analytical form reached. The variable '{v}' is completely isolated."))

        return final_answer, steps

    except ZeroDivisionError:
        return "Error", [("text", "[STOPPING RULE]: Division by zero detected. Process halted.")]
    except Exception as e:
        return "Error", [("text", "[STOPPING RULE]: Invalid math formatting. Process halted.")]