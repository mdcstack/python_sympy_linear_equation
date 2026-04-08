# Linear Equation Calculator v1.0
**Author/s:** Mellissa Ambeguia, 
              Endred Antoine Baido, 
              Matthew David Cartagena 

## Description
An interactive, Human-Computer Interaction (HCI) focused educational tool that solves linear equations using exact symbolic computation. It acts as a "glass box" tutor, showing complete step-by-step mathematical logic and deterministic stopping rules.

## Features
* **Two Solver Methods:** Choose between Standard Form Isolation ($Ax + B = 0$) and Two-Sided Balancing ($Ax = C$).
* **Dynamic Auto-Numbering:** The solution trail adapts to the input, skipping irrelevant steps (like fraction clearing if there are no fractions).
* **Interactive UI:** Features infinite-panning Matplotlib displays for rendering high-fidelity, textbook-style LaTeX fractions and long final answers.
* **Strict Syntax Validation:** Actively intercepts sloppy formatting (like `+-`) and forces mathematically sound inputs.

## How to Run
1. Ensure you have Python 3.8+ installed.
2. Install the required dependencies by running the following command in your terminal:
   `pip install sympy matplotlib pillow`
3. Run the main application file:
   `python main_ui.py`

## Sample Inputs v1
**Objective:** Verify symbolic math routing, stopping rules, and edge-case handling.

| Test ID | Objective | Input | Selected Method | Expected Stopping Rule | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-01** | Basic Algebraic Isolation | `3x - 5 = 10` | Standard Form | Exact analytical form reached. | [PASS] |
| **TC-02** | Identity (Infinite Solutions) | `2y + 4 = 2(y + 2)` | Standard Form | Identity reached. | [PASS] |
| **TC-03** | Two-Sided Scale Arithmetic | `3z + 5 = 20` | Balancing | Exact analytical form reached. | [PASS] |
| **TC-04** | Contradiction (No Solution) | `x + 5 = x + 10` | Balancing | Contradiction reached. | [PASS] |
| **TC-05** | Multi-variable Distribution | `5x + 2 = 3x + 10`| Balancing | Exact analytical form reached. | [PASS] |
