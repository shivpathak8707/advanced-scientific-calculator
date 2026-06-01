import unittest
import math
from engine import evaluate_expression, preprocess_percentage, insert_implicit_multiplication, clean_expression_for_eval, backspace_expression

class TestCalculatorEngine(unittest.TestCase):
    def test_basic_arithmetic(self):
        self.assertEqual(evaluate_expression("2 + 3"), 5)
        self.assertEqual(evaluate_expression("10 - 4"), 6)
        self.assertEqual(evaluate_expression("3 × 4"), 12)
        self.assertEqual(evaluate_expression("12 ÷ 3"), 4)
        self.assertEqual(evaluate_expression("5 + 3 × 2"), 11)
        self.assertEqual(evaluate_expression("(5 + 3) × 2"), 16)

    def test_division_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            evaluate_expression("1 / 0")
        with self.assertRaises(ZeroDivisionError):
            evaluate_expression("5 ÷ (2 - 2)")

    def test_percentage(self):
        self.assertEqual(evaluate_expression("50%"), 0.5)
        self.assertEqual(evaluate_expression("10 + 5%"), 10.05)
        self.assertEqual(evaluate_expression("10 × 5%"), 0.5)
        self.assertEqual(evaluate_expression("(10 + 10)%"), 0.2)

    def test_implicit_multiplication(self):
        self.assertEqual(evaluate_expression("2(3+4)"), 14)
        self.assertEqual(evaluate_expression("(2+3)(4+5)"), 45)
        self.assertAlmostEqual(evaluate_expression("2pi", angle_mode='rad'), 2 * math.pi)
        self.assertAlmostEqual(evaluate_expression("2sin(30)", angle_mode='deg'), 1.0)
        self.assertAlmostEqual(evaluate_expression("pi(2)", angle_mode='rad'), 2 * math.pi)

    def test_trigonometry(self):
        # Degrees
        self.assertAlmostEqual(evaluate_expression("sin(30)", angle_mode='deg'), 0.5)
        self.assertAlmostEqual(evaluate_expression("cos(60)", angle_mode='deg'), 0.5)
        self.assertAlmostEqual(evaluate_expression("tan(45)", angle_mode='deg'), 1.0)
        
        # Radians
        self.assertAlmostEqual(evaluate_expression("sin(pi/2)", angle_mode='rad'), 1.0)
        self.assertAlmostEqual(evaluate_expression("cos(pi)", angle_mode='rad'), -1.0)
        self.assertAlmostEqual(evaluate_expression("tan(0)", angle_mode='rad'), 0.0)

    def test_powers_and_roots(self):
        self.assertEqual(evaluate_expression("2^3"), 8)
        self.assertEqual(evaluate_expression("sqrt(9)"), 3)
        self.assertEqual(evaluate_expression("sqrt(2 + 7)"), 3)
        self.assertEqual(evaluate_expression("4^0.5"), 2)

    def test_logarithms(self):
        self.assertEqual(evaluate_expression("log(100)"), 2)
        self.assertAlmostEqual(evaluate_expression("ln(e)"), 1.0)

    def test_factorial(self):
        self.assertEqual(evaluate_expression("fact(5)"), 120)
        self.assertEqual(evaluate_expression("factorial(0)"), 1)
        with self.assertRaises(ValueError):
            evaluate_expression("fact(-1)")

    def test_overflow_protection(self):
        with self.assertRaises(OverflowError):
            evaluate_expression("9^9^9")
        with self.assertRaises(OverflowError):
            evaluate_expression("fact(1001)")

    def test_backspace(self):
        self.assertEqual(backspace_expression("sin("), "")
        self.assertEqual(backspace_expression("asin("), "")
        self.assertEqual(backspace_expression("2 + "), "2")
        self.assertEqual(backspace_expression("2 - "), "2")
        self.assertEqual(backspace_expression("2 × "), "2")
        self.assertEqual(backspace_expression("2 ÷ "), "2")
        self.assertEqual(backspace_expression("123"), "12")
        self.assertEqual(backspace_expression(""), "")
        self.assertEqual(backspace_expression("sqrt("), "")
        self.assertEqual(backspace_expression("cosec("), "")
        self.assertEqual(backspace_expression("acosec("), "")

    def test_advanced_trig(self):
        self.assertAlmostEqual(evaluate_expression("sec(60)", angle_mode='deg'), 2.0)
        self.assertAlmostEqual(evaluate_expression("cosec(30)", angle_mode='deg'), 2.0)
        self.assertAlmostEqual(evaluate_expression("cot(45)", angle_mode='deg'), 1.0)
        self.assertAlmostEqual(evaluate_expression("asec(2)", angle_mode='deg'), 60.0)
        self.assertAlmostEqual(evaluate_expression("acosec(2)", angle_mode='deg'), 30.0)
        self.assertAlmostEqual(evaluate_expression("acot(1)", angle_mode='deg'), 45.0)

    def test_polynomial_solver(self):
        from solver import solve_polynomial
        # Linear: 2x - 4 = 0 -> x = 2
        res = solve_polynomial([2, -4])
        self.assertEqual(res["roots"], [2.0])
        
        # Quadratic: x^2 - 5x + 6 = 0 -> x = 2, 3
        res = solve_polynomial([1, -5, 6])
        self.assertEqual(sorted(res["roots"]), [2.0, 3.0])
        
        # Cubic: x^3 - 6x^2 + 11x - 6 = 0 -> x = 1, 2, 3
        res = solve_polynomial([1, -6, 11, -6])
        roots = [round(r.real if isinstance(r, complex) else r, 4) for r in res["roots"]]
        self.assertEqual(sorted(roots), [1.0, 2.0, 3.0])

    def test_exact_representation(self):
        from ui import get_exact_representation, get_all_representations
        self.assertEqual(get_exact_representation(0.5), "1/2")
        self.assertEqual(get_exact_representation(math.sqrt(2)/2), "√2/2")
        self.assertEqual(get_exact_representation(-math.sqrt(3)), "-√3")
        
        # Test representations list cycling elements
        reprs = get_all_representations(0.70710678118)
        self.assertIn("√2/2", reprs)
        
        reprs_frac = get_all_representations(0.75)
        self.assertIn("3/4", reprs_frac)
        self.assertIn("0.75", reprs_frac)

    def test_domain_errors(self):
        # cosec(0) -> Domain error undefined
        with self.assertRaises(ValueError):
            evaluate_expression("cosec(0)")
            
        # cot(0) -> undefined
        with self.assertRaises(ValueError):
            evaluate_expression("cot(0)")
            
        # log(0) -> undefined
        with self.assertRaises(ValueError):
            evaluate_expression("log(0)")
            
        # sqrt(-1) -> undefined
        with self.assertRaises(ValueError):
            evaluate_expression("sqrt(-1)")

    def test_graph_expressions(self):
        # Test |x| -> abs(x)
        self.assertEqual(evaluate_expression("abs(-5)"), 5)
        self.assertEqual(evaluate_expression("|-5|"), 5)
        self.assertEqual(evaluate_expression("|2 + -5|"), 3)
        self.assertEqual(evaluate_expression("||-3| + -2|"), 1)  # Nested absolute values
        
        # Test asin, acos, atan evaluations (both standard and arc-prefix)
        self.assertAlmostEqual(evaluate_expression("asin(0.5)", angle_mode='deg'), 30.0)
        self.assertAlmostEqual(evaluate_expression("arcsin(0.5)", angle_mode='deg'), 30.0)
        self.assertAlmostEqual(evaluate_expression("acos(0.5)", angle_mode='deg'), 60.0)
        self.assertAlmostEqual(evaluate_expression("arccos(0.5)", angle_mode='deg'), 60.0)
        self.assertAlmostEqual(evaluate_expression("atan(1)", angle_mode='deg'), 45.0)
        self.assertAlmostEqual(evaluate_expression("arctan(1)", angle_mode='deg'), 45.0)
        
        # Test graphing domain exceptions for invalid values
        with self.assertRaises(ValueError):
            evaluate_expression("arcsin(2.0)")
        with self.assertRaises(ValueError):
            evaluate_expression("arccos(-1.5)")

if __name__ == '__main__':
    unittest.main()
