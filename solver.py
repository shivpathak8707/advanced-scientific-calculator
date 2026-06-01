import cmath
import math

def format_complex(val):
    """Formats a real or complex number into a neat string representation."""
    if isinstance(val, complex):
        real = round(val.real, 6)
        imag = round(val.imag, 6)
        if abs(imag) < 1e-9:
            return f"{real}"
        if abs(real) < 1e-9:
            return f"{imag}i"
        sign = "+" if imag >= 0 else "-"
        return f"{real} {sign} {abs(imag)}i"
    else:
        real = round(val, 6)
        if real.is_integer():
            return str(int(real))
        return str(real)


def format_poly_equation(coeffs):
    """Formats polynomial coefficients into beautiful textbook-style equations (e.g. x² + 5x - 6 = 0)."""
    degree = len(coeffs) - 1
    terms = []
    
    for i, c in enumerate(coeffs):
        deg = degree - i
        if abs(c) < 1e-15:
            continue
            
        is_negative = False
        if isinstance(c, complex):
            val_str = f"({format_complex(c)})"
            sign = " + " if i > 0 else ""
        else:
            if c < 0:
                is_negative = True
                c = -c
            sign = " - " if is_negative else (" + " if i > 0 else "")
            
            if abs(c - 1.0) < 1e-15 and deg > 0:
                val_str = ""
            else:
                if c.is_integer():
                    val_str = str(int(c))
                else:
                    val_str = str(round(c, 6))
                    
        if deg == 0:
            term_str = val_str if val_str else "1"
        elif deg == 1:
            term_str = f"{val_str}x"
        elif deg == 2:
            term_str = f"{val_str}x²"
        elif deg == 3:
            term_str = f"{val_str}x³"
        else:
            superscripts = {
                '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', 
                '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'
            }
            deg_str = "".join(superscripts[d] for d in str(deg))
            term_str = f"{val_str}x{deg_str}"
            
        if len(terms) == 0:
            if is_negative:
                terms.append(f"-{term_str}")
            else:
                terms.append(term_str)
        else:
            terms.append(f"{sign}{term_str}")
            
    if not terms:
        return "0 = 0"
        
    return "".join(terms) + " = 0"


def format_coefficient_step(prefix, val):
    """Utility to format steps (e.g. handling -(-5) as 5)"""
    if isinstance(val, complex):
        return f"{prefix}({format_complex(val)})"
    if val < 0:
        if prefix == "-":
            return format_complex(-val)
        return f"{prefix}({format_complex(val)})"
    return f"{prefix}{format_complex(val)}"


def solve_linear(a, b):
    """Solves ax + b = 0 step-by-step."""
    steps = []
    steps.append(f"Equation: {format_poly_equation([a, b])}")
    if abs(a) < 1e-15:
        if abs(b) < 1e-15:
            steps.append("This is an identity (0 = 0). Infinitely many solutions.")
            return {"roots": [0.0], "steps": "\n".join(steps)}
        else:
            steps.append("Contradiction (constant = 0, constant != 0). No solution.")
            return {"roots": [], "steps": "\n".join(steps)}
    
    root = -b / a
    steps.append(f"Step 1: Isolate the variable term: {format_complex(a)}x = {format_coefficient_step('-', b)}")
    steps.append(f"Step 2: Divide both sides by coefficient a: x = {format_coefficient_step('-', b)} / {format_complex(a)}")
    steps.append(f"Result: x = {format_complex(root)}")
    return {"roots": [root], "steps": "\n".join(steps)}


def solve_quadratic(a, b, c):
    """Solves ax^2 + bx + c = 0 step-by-step using the quadratic formula."""
    steps = []
    steps.append(f"Equation: {format_poly_equation([a, b, c])}")
    if abs(a) < 1e-15:
        steps.append("Leading coefficient a is 0. Reducing to linear equation.")
        return solve_linear(b, c)
        
    d = b**2 - 4*a*c
    steps.append(f"Step 1: Compute discriminant D = b² - 4ac")
    steps.append(f"        D = ({format_complex(b)})² - 4 * ({format_complex(a)}) * ({format_complex(c)})")
    steps.append(f"        D = {format_complex(d)}")
    
    roots = []
    if d > 0:
        steps.append("Discriminant is positive. Two distinct real roots exist.")
        r1 = (-b + math.sqrt(d)) / (2*a)
        r2 = (-b - math.sqrt(d)) / (2*a)
        roots = [r1, r2]
        steps.append(f"Step 2: Apply quadratic formula x = (-b ± √D) / 2a")
        steps.append(f"        x = ({format_coefficient_step('-', b)} ± √{format_complex(d)}) / (2 * {format_complex(a)})")
        steps.append(f"        x1 = {format_complex(r1)}")
        steps.append(f"        x2 = {format_complex(r2)}")
    elif d == 0:
        steps.append("Discriminant is zero. One repeated real root exists.")
        r = -b / (2*a)
        roots = [r]
        steps.append(f"Step 2: Apply quadratic formula x = -b / 2a")
        steps.append(f"        x = {format_coefficient_step('-', b)} / (2 * {format_complex(a)})")
        steps.append(f"        x = {format_complex(r)}")
    else:
        steps.append("Discriminant is negative. Two complex conjugate roots exist.")
        r_part = -b / (2*a)
        i_part = math.sqrt(-d) / (2*a)
        r1 = complex(r_part, i_part)
        r2 = complex(r_part, -i_part)
        roots = [r1, r2]
        steps.append(f"Step 2: Apply quadratic formula with complex numbers")
        steps.append(f"        x = (-b ± i√|D|) / 2a")
        steps.append(f"        x = ({format_coefficient_step('-', b)} ± i√{format_complex(-d)}) / (2 * {format_complex(a)})")
        steps.append(f"        x1 = {format_complex(r1)}")
        steps.append(f"        x2 = {format_complex(r2)}")
        
    return {"roots": roots, "steps": "\n".join(steps)}


def solve_cubic(a, b, c, d):
    """Solves ax^3 + bx^2 + cx + d = 0 step-by-step."""
    steps = []
    steps.append(f"Equation: {format_poly_equation([a, b, c, d])}")
    if abs(a) < 1e-15:
        steps.append("Leading coefficient a is 0. Reducing to quadratic equation.")
        return solve_quadratic(b, c, d)
        
    def f(x):
        return a * x**3 + b * x**2 + c * x + d
    def df(x):
        return 3 * a * x**2 + 2 * b * x + c
        
    r1 = 0.0
    for start in [0.0, 1.0, -1.0, 10.0, -10.0, 100.0, -100.0]:
        x = start
        converged = False
        for _ in range(100):
            deriv = df(x)
            if abs(deriv) < 1e-12:
                break
            next_x = x - f(x) / deriv
            if abs(next_x - x) < 1e-10:
                r1 = next_x
                converged = True
                break
            x = next_x
        if converged:
            break
            
    steps.append(f"Step 1: Find one real root using numerical search")
    steps.append(f"        Found real root x1 ≈ {format_complex(r1)}")
    
    A = a
    B = b + r1 * A
    C = c + r1 * B
    
    steps.append(f"Step 2: Divide the polynomial by (x - {format_complex(r1)}) to factor it")
    steps.append(f"        By synthetic division, the quotient quadratic is:")
    steps.append(f"        {format_poly_equation([A, B, C])}")
    
    quad_res = solve_quadratic(A, B, C)
    steps.append("\n" + quad_res["steps"])
    
    roots = [r1] + quad_res["roots"]
    return {"roots": roots, "steps": "\n".join(steps)}


def solve_higher_order(coeffs):
    """Solves higher order polynomials (degree >= 4) using the Durand-Kerner method."""
    steps = []
    degree = len(coeffs) - 1
    steps.append(f"Equation degree: {degree}")
    steps.append(f"Equation: {format_poly_equation(coeffs)}")
    
    while coeffs and abs(coeffs[0]) < 1e-15:
        coeffs.pop(0)
    if not coeffs or len(coeffs) < 2:
        return {"roots": [], "steps": "Invalid equation"}
        
    n = len(coeffs) - 1
    an = coeffs[0]
    p = [c / an for c in coeffs]
    
    max_p = max(abs(c) for c in p[1:]) if len(p) > 1 else 0
    r = 1.0 + max_p
    
    roots = []
    for j in range(n):
        angle = (2 * math.pi * j) / n + math.pi / (2 * n)
        roots.append(r * cmath.rect(1.0, angle))
        
    def eval_poly(x):
        res = 0.0 + 0.0j
        for c in p:
            res = res * x + c
        return res
        
    max_iter = 200
    tolerance = 1e-12
    for _ in range(max_iter):
        max_diff = 0.0
        for i in range(n):
            denom = 1.0 + 0.0j
            for j in range(n):
                if i != j:
                    denom *= (roots[i] - roots[j])
            if abs(denom) < 1e-30:
                continue
            delta = eval_poly(roots[i]) / denom
            roots[i] -= delta
            max_diff = max(max_diff, abs(delta))
        if max_diff < tolerance:
            break
            
    steps.append(f"Step 1: Apply numerical Durand-Kerner (Weierstrass) root-finding algorithm")
    steps.append(f"        Starting iterations on a complex radius of {round(r, 4)}")
    steps.append("Step 2: Converging on real and complex conjugate pairs...")
    
    clean_roots = []
    for r_val in roots:
        real_part = r_val.real
        imag_part = r_val.imag
        if abs(imag_part) < 1e-9:
            clean_roots.append(real_part)
        else:
            clean_roots.append(r_val)
            
    for i, root in enumerate(clean_roots):
        steps.append(f"        x{i+1} = {format_complex(root)}")
        
    return {"roots": clean_roots, "steps": "\n".join(steps)}


def solve_polynomial(coeffs):
    """High-level dispatcher for solving polynomials based on degree."""
    while coeffs and abs(coeffs[0]) < 1e-15:
        coeffs.pop(0)
        
    if not coeffs or len(coeffs) < 2:
        return {"roots": [], "steps": "No variable terms. Equation has no variable to solve."}
        
    degree = len(coeffs) - 1
    if degree == 1:
        return solve_linear(coeffs[0], coeffs[1])
    elif degree == 2:
        return solve_quadratic(coeffs[0], coeffs[1], coeffs[2])
    elif degree == 3:
        return solve_cubic(coeffs[0], coeffs[1], coeffs[2], coeffs[3])
    else:
        return solve_higher_order(coeffs)
