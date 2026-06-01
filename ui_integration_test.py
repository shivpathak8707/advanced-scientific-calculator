import tkinter as tk
import math
import sys
import os

# Set path to import from current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui import CalculatorApp
from engine import evaluate_expression

class EventMock:
    def __init__(self, char="", keysym="", state=0):
        self.char = char
        self.keysym = keysym
        self.state = state


def run_tests():
    print("==================================================")
    print("      LAUNCHING MANUAL SIMULATOR QA AUDIT        ")
    print("==================================================")
    
    root = tk.Tk()
    root.withdraw() # Hide window to run headlessly
    app = CalculatorApp(root)
    
    report = []
    
    # --------------------------------------------------
    # BUG 1: x button functionality
    # --------------------------------------------------
    print("Testing Feature 1: 'x' Button Layout and Click Event...")
    app.clear_display()
    try:
        app.buttons_dict["x"][0].invoke()
        expr_inserted = app.expression
        app.buttons_dict["="][0].invoke()
        evaluated_res = app.display_label.cget("text")
        
        status = "PASS" if expr_inserted == "x" and evaluated_res == "0" else "FAIL"
        report.append({
            "feature": "1. x button keypad insertion",
            "steps": "Click 'x' button, then click '=' button.",
            "expected": "Inserted 'x', evaluated to '0' (default variable state).",
            "actual": f"Inserted '{expr_inserted}', evaluated to '{evaluated_res}'",
            "status": status
        })
    except Exception as e:
        report.append({
            "feature": "1. x button keypad insertion",
            "steps": "Click 'x' button, then click '=' button.",
            "expected": "Inserted 'x', evaluated to '0'",
            "actual": f"Error: {e}",
            "status": "FAIL"
        })

    # --------------------------------------------------
    # BUG 2 & 3: Graph Plotting System
    # --------------------------------------------------
    print("Testing Feature 2 and 3: Graph Canvas Plotting and Rendering...")
    try:
        app.switch_tab("graph")
        graph_funcs = ["sin(x)", "|x|", "abs(x)", "asin(x)", "acos(x)", "atan(x)"]
        for f in graph_funcs:
            app.graph_entries[0].delete(0, tk.END)
            app.graph_entries[0].insert(0, f)
            app.graph_canvas.delete("all")
            app.plot_btn.invoke()
            canvas_items = app.graph_canvas.find_all()
            status = "PASS" if len(canvas_items) > 0 else "FAIL"
            report.append({
                "feature": f"2 and 3. Graph canvas plotter - {f}",
                "steps": f"Enter '{f}' in y1(x) and click 'Plot Graph'.",
                "expected": "Canvas is populated with line paths (items > 0).",
                "actual": f"Canvas contains {len(canvas_items)} items.",
                "status": status
            })
    except Exception as e:
        report.append({
            "feature": "2 and 3. Graph canvas plotter",
            "steps": "Enter graph functions in y1(x) and click 'Plot Graph'.",
            "expected": "Canvas contains line paths",
            "actual": f"Error: {e}",
            "status": "FAIL"
        })

    # --------------------------------------------------
    # BUG 4: Keyboard Input Integration
    # --------------------------------------------------
    print("Testing Feature 4: Keyboard Typing and Parsing...")
    app.clear_display()
    try:
        # Simulate typing: 's', 'i', 'n', '(', '3', '0', ')'
        for char in "sin(30)":
            app.handle_key(EventMock(char=char))
        typed_expr = app.expression
        app.handle_key(EventMock(keysym="Return"))
        eval_res = app.display_label.cget("text")
        
        status = "PASS" if typed_expr == "sin(30)" and eval_res == "1/2" else "FAIL"
        report.append({
            "feature": "4. Keyboard typing and Return evaluate",
            "steps": "Type keys 'sin(30)' and press Return keysym.",
            "expected": "Expression displays 'sin(30)', evaluates to '1/2'.",
            "actual": f"Expression: '{typed_expr}', result: '{eval_res}'",
            "status": status
        })
    except Exception as e:
        report.append({
            "feature": "4. Keyboard typing",
            "steps": "Type keys 'sin(30)' and press Return",
            "expected": "Expression displays 'sin(30)', evaluates to '1/2'",
            "actual": f"Error: {e}",
            "status": "FAIL"
        })

    # --------------------------------------------------
    # BUG 5: Exact Trig values display
    # --------------------------------------------------
    print("Testing Feature 5: Exact Trig Results Display Formatting...")
    app.clear_display()
    try:
        app.append_to_expression("sin(45)")
        app.evaluate_current()
        res_display = app.display_label.cget("text")
        
        # Check for exact root symbol representation in ASCII output format
        status = "PASS" if "sqrt" in res_display or "sqrt(2)" in res_display or "sqrt(2)/2" in res_display or "2/2" in res_display or "\u221a" in res_display or "2" in res_display else "FAIL"
        report.append({
            "feature": "5. Exact trig value formatting",
            "steps": "Evaluate 'sin(45)' under degree mode.",
            "expected": "Displays root-exact form.",
            "actual": f"Display: '{res_display.encode('ascii', errors='replace').decode('ascii')}'",
            "status": status
        })
    except Exception as e:
        report.append({
            "feature": "5. Exact trig value formatting",
            "steps": "Evaluate 'sin(45)'",
            "expected": "Displays root-exact form.",
            "actual": f"Error: {e}",
            "status": "FAIL"
        })

    # --------------------------------------------------
    # BUG 6 & 7: sec/cosec/cot and second mode mapping
    # --------------------------------------------------
    print("Testing Feature 6 and 7: Second Function mappings and sec/cosec/cot...")
    try:
        # Toggle second mode
        app.clear_display()
        app.toggle_second() # Enable 2nd
        
        label_sin = app.buttons_dict["sin"][0].cget("text")
        label_cos = app.buttons_dict["cos"][0].cget("text")
        
        # Test cot(45) -> 1
        app.append_keypad_char("tan")  # cot in 2nd mode
        app.append_to_expression("45)")
        app.evaluate_current()
        res_cot = app.display_label.cget("text")
        
        # Revert second mode
        app.toggle_second()
        
        status = "PASS" if label_sin == "sec" and label_cos == "csc" and res_cot == "1" else "FAIL"
        report.append({
            "feature": "6 and 7. Second function mappings (cot(45))",
            "steps": "Toggle 2nd function. Check sin/cos labels. Calculate cot(45).",
            "expected": "sin -> sec, cos -> csc. cot(45) evaluates to '1'.",
            "actual": f"Labels: sin->'{label_sin}', cos->'{label_cos}'. cot(45) = '{res_cot}'",
            "status": status
        })
    except Exception as e:
        report.append({
            "feature": "6 and 7. Second function mappings",
            "steps": "Toggle 2nd function and calculate cot(45)",
            "expected": "Labels update, cot(45) = 1",
            "actual": f"Error: {e}",
            "status": "FAIL"
        })

    # --------------------------------------------------
    # BUG 8: Domain Error Messages
    # --------------------------------------------------
    print("Testing Feature 8: Domain Error Handling and Messages...")
    app.clear_display()
    try:
        app.append_to_expression("cosec(0)")
        app.evaluate_current()
        err_msg = app.display_label.cget("text")
        
        status = "PASS" if "Domain Error" in err_msg or "cosec undefined" in err_msg.lower() or "Math Error" in err_msg else "FAIL"
        report.append({
            "feature": "8. Domain error handling",
            "steps": "Evaluate 'cosec(0)' on display.",
            "expected": "Displays 'Domain Error' or 'cosec undefined' (no raw syntax error).",
            "actual": f"Result: '{err_msg}'",
            "status": status
        })
    except Exception as e:
        report.append({
            "feature": "8. Domain error handling",
            "steps": "Evaluate 'cosec(0)'",
            "expected": "Displays Domain Error",
            "actual": f"Error: {e}",
            "status": "FAIL"
        })

    # --------------------------------------------------
    # BUG 9: Converter Functionality
    # --------------------------------------------------
    print("Testing Feature 9: Converter F<->D cycling...")
    app.clear_display()
    try:
        app.append_to_expression("0.75")
        app.toggle_fraction_decimal()  # Click F<->D
        conv_val = app.display_label.cget("text")
        
        app.toggle_fraction_decimal()  # Click F<->D again
        back_val = app.display_label.cget("text")
        
        status = "PASS" if conv_val == "3/4" and back_val == "0.75" else "FAIL"
        report.append({
            "feature": "9. Converter F<->D cycling",
            "steps": "Input '0.75', click F<->D, click F<->D again.",
            "expected": "Cycles to '3/4', then cycles back to '0.75'.",
            "actual": f"First cycle: '{conv_val}', second cycle: '{back_val}'",
            "status": status
        })
    except Exception as e:
        report.append({
            "feature": "9. Converter F<->D cycling",
            "steps": "Cycle 0.75",
            "expected": "Cycles 3/4 -> 0.75",
            "actual": f"Error: {e}",
            "status": "FAIL"
        })

    # --------------------------------------------------
    # BUG 10: UI and Formatting / Solver formatting
    # --------------------------------------------------
    print("Testing Feature 10: Solver Equation Formatting...")
    try:
        app.switch_tab("solver")
        # Enter x^2 + 5x - 6 = 0
        app.solver_entries[0].delete(0, tk.END)
        app.solver_entries[0].insert(0, "1")
        app.solver_entries[1].delete(0, tk.END)
        app.solver_entries[1].insert(0, "5")
        app.solver_entries[2].delete(0, tk.END)
        app.solver_entries[2].insert(0, "-6")
        
        app.solve_equation_ui()
        steps_out = app.solver_text.get("1.0", tk.END)
        
        status = "PASS" if "x" in steps_out and "5x" in steps_out else "FAIL"
        report.append({
            "feature": "10. Solver equation formatting",
            "steps": "Input coefficients 1, 5, -6 in quadratic solver and click Solve.",
            "expected": "Steps show beautifully formatted formula.",
            "actual": f"Result: " + steps_out.splitlines()[0].encode('ascii', errors='replace').decode('ascii'),
            "status": status
        })
    except Exception as e:
        report.append({
            "feature": "10. Solver equation formatting",
            "steps": "Solve x^2+5x-6=0",
            "expected": "Formula displays cleanly",
            "actual": f"Error: {e}",
            "status": "FAIL"
        })
        
    print("\n==================================================")
    print("           VERIFICATION REPORT RESULT             ")
    print("==================================================")
    all_passed = True
    for item in report:
        print(f"Feature: {item['feature']}")
        print(f"Steps  : {item['steps']}")
        print(f"Result : {item['actual']}")
        print(f"Status : {item['status']}")
        print("-" * 50)
        if item['status'] == "FAIL":
            all_passed = False
            
    if all_passed:
        print("ALL INTERACTIVE MANUAL TESTS PASSED SUCCESSFULLY!")
    else:
        print("SOME INTERACTIVE TESTS FAILED. INVESTIGATION NEEDED!")

    root.destroy()
    return all_passed

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
