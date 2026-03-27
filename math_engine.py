from standard_computation import solve_standard_form
from balancing_computation import solve_balancing_method

def solve_linear_equation(equation_str, target_var_str, method="standard"):
    """
    Acts as a router to send the equation to the correct algorithm 
    based on the user's selected method in the UI.
    """
    if method == "balancing":
        return solve_balancing_method(equation_str, target_var_str)
    else:
        # Default to the Standard Form method
        return solve_standard_form(equation_str, target_var_str)