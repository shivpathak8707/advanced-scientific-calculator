import ast
import operator
import math
import re

class SafeEvaluator:
    def __init__(self, angle_mode='deg'):
        self.angle_mode = angle_mode
        
        # Supported AST operators mapped to python functions
        self.operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.Mod: operator.mod,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }
        
        # Supported mathematical constants
        self.constants = {
            'pi': math.pi,
            'e': math.e,
        }

    def _eval_call(self, node):
        if not isinstance(node.func, ast.Name):
            raise NameError("Invalid function call structure")
            
        func_name = node.func.id
        args = [self._eval_node(arg) for arg in node.args]
        
        if not args:
            raise ValueError(f"Function {func_name} requires at least one argument")
            
        val = args[0]
        
        if func_name == 'sqrt':
            if val < 0:
                raise ValueError("Domain Error: sqrt of negative")
            return math.sqrt(val)
            
        elif func_name == 'sin':
            if self.angle_mode == 'deg':
                val = math.radians(val)
            res = math.sin(val)
            return 0.0 if abs(res) < 1e-15 else res
            
        elif func_name == 'cos':
            if self.angle_mode == 'deg':
                val = math.radians(val)
            res = math.cos(val)
            return 0.0 if abs(res) < 1e-15 else res
            
        elif func_name == 'tan':
            if self.angle_mode == 'deg':
                val = math.radians(val)
            # Singularity check (cos close to 0)
            if abs(math.cos(val)) < 1e-15:
                raise ValueError("Math Error: tan undefined")
            res = math.tan(val)
            return 0.0 if abs(res) < 1e-15 else res
            
        elif func_name == 'sec':
            if self.angle_mode == 'deg':
                val = math.radians(val)
            cos_val = math.cos(val)
            if abs(cos_val) < 1e-15:
                raise ValueError("Math Error: sec undefined")
            res = 1.0 / cos_val
            return 0.0 if abs(res) < 1e-15 else res
            
        elif func_name in ('cosec', 'csc'):
            if self.angle_mode == 'deg':
                val = math.radians(val)
            sin_val = math.sin(val)
            if abs(sin_val) < 1e-15:
                raise ValueError("Math Error: cosec undefined")
            res = 1.0 / sin_val
            return 0.0 if abs(res) < 1e-15 else res
            
        elif func_name == 'cot':
            if self.angle_mode == 'deg':
                val = math.radians(val)
            sin_val = math.sin(val)
            cos_val = math.cos(val)
            if abs(sin_val) < 1e-15:
                raise ValueError("Math Error: cot undefined")
            res = cos_val / sin_val
            return 0.0 if abs(res) < 1e-15 else res
            
        elif func_name == 'abs':
            return abs(val)

        elif func_name in ('asin', 'arcsin'):
            if not -1 <= val <= 1:
                raise ValueError("Domain Error: arcsin domain is [-1, 1]")
            res = math.asin(val)
            return math.degrees(res) if self.angle_mode == 'deg' else res
            
        elif func_name in ('acos', 'arccos'):
            if not -1 <= val <= 1:
                raise ValueError("Domain Error: arccos domain is [-1, 1]")
            res = math.acos(val)
            return math.degrees(res) if self.angle_mode == 'deg' else res
            
        elif func_name in ('atan', 'arctan'):
            res = math.atan(val)
            return math.degrees(res) if self.angle_mode == 'deg' else res

        elif func_name in ('asec', 'arcsec'):
            if abs(val) < 1.0:
                raise ValueError("Domain Error: arcsec requires |x| >= 1")
            res = math.acos(1.0 / val)
            return math.degrees(res) if self.angle_mode == 'deg' else res

        elif func_name in ('acosec', 'acsc', 'arccsc', 'arccosec'):
            if abs(val) < 1.0:
                raise ValueError("Domain Error: arccosec requires |x| >= 1")
            res = math.asin(1.0 / val)
            return math.degrees(res) if self.angle_mode == 'deg' else res

        elif func_name in ('acot', 'arccot'):
            if abs(val) < 1e-30:
                res = math.pi / 2.0
            else:
                res = math.atan(1.0 / val)
            return math.degrees(res) if self.angle_mode == 'deg' else res
            
        elif func_name == 'log':
            if val <= 0:
                raise ValueError("Domain Error: log10 of non-positive")
            return math.log10(val)
            
        elif func_name == 'ln':
            if val <= 0:
                raise ValueError("Domain Error: ln of non-positive")
            return math.log(val)
            
        elif func_name in ('fact', 'factorial'):
            if val < 0 or not val.is_integer():
                raise ValueError("Domain Error: factorial expects non-negative integer")
            # Limit factorial argument to prevent overflow hang
            if val > 1000:
                raise OverflowError("Overflow Error: factorial argument too large")
            return float(math.factorial(int(val)))
            
        else:
            raise NameError(f"Unsupported function: {func_name}")

    def _eval_node(self, node):
        if isinstance(node, ast.Expression):
            return self._eval_node(node.body)
            
        elif isinstance(node, ast.Constant):
            # Safe numeric conversion
            try:
                return float(node.value)
            except (ValueError, TypeError):
                raise TypeError(f"Invalid constant value: {node.value}")
            
        elif isinstance(node, ast.Name):
            name = node.id.lower()
            if name in self.constants:
                return self.constants[name]
            raise NameError(f"Unknown symbol: {name}")
            
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_type = type(node.op)
            
            if op_type in self.operators:
                if op_type == ast.Div and right == 0:
                    raise ZeroDivisionError("Math Error: Division by zero")
                try:
                    # Prevent huge power operations that hang the CPU
                    if op_type == ast.Pow:
                        if abs(left) > 1e100 or abs(right) > 1000:
                            # Safeguard against 9^9^9
                            if left == 1.0 or left == 0.0 or right == 0.0:
                                pass
                            else:
                                raise OverflowError("Overflow Error")
                    res = self.operators[op_type](left, right)
                    if isinstance(res, complex):
                        raise ValueError("Domain Error: Complex result not supported")
                    return float(res)
                except OverflowError:
                    raise OverflowError("Overflow Error")
            raise TypeError(f"Unsupported binary operator: {op_type}")
            
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op_type = type(node.op)
            if op_type in self.operators:
                res = self.operators[op_type](operand)
                return float(res)
            raise TypeError(f"Unsupported unary operator: {op_type}")
            
        elif isinstance(node, ast.Call):
            return self._eval_call(node)
            
        else:
            raise TypeError(f"Unsupported expression construct: {type(node)}")

    def evaluate(self, expr_str):
        """Parses and evaluates a mathematical expression string safely."""
        expr_str = expr_str.strip()
        if not expr_str:
            return 0.0
        
        # Parse expression into AST and evaluate
        try:
            parsed = ast.parse(expr_str, mode='eval')
            result = self._eval_node(parsed)
            # Return integer if result is equivalent to integer
            if result.is_integer():
                return int(result)
            return result
        except SyntaxError:
            raise SyntaxError("Syntax Error")


def preprocess_percentage(expr_str):
    """
    Finds percentage symbols (%) and replaces their preceding operand with (operand/100).
    Scans backward to handle parentheses and numbers safely.
    """
    i = len(expr_str) - 1
    while i >= 0:
        if expr_str[i] == '%':
            j = i - 1
            # Skip spaces
            while j >= 0 and expr_str[j].isspace():
                j -= 1
            if j < 0:
                raise ValueError("Syntax Error: % operator requires an operand")
            
            if expr_str[j] == ')':
                # Trace back to find matching '('
                paren_count = 1
                k = j - 1
                while k >= 0 and paren_count > 0:
                    if expr_str[k] == ')':
                        paren_count += 1
                    elif expr_str[k] == '(':
                        paren_count -= 1
                    k -= 1
                if paren_count > 0:
                    raise ValueError("Syntax Error: Unbalanced parentheses before %")
                operand = expr_str[k+1 : j+1]
                expr_str = expr_str[:k+1] + f"({operand}/100)" + expr_str[i+1:]
                i = k + 1
            else:
                # Trace back alphanumeric/decimal characters representing numbers or constants
                k = j
                while k >= 0 and (expr_str[k].isalnum() or expr_str[k] in '._'):
                    k -= 1
                operand = expr_str[k+1 : j+1]
                if not operand:
                    raise ValueError("Syntax Error: % operator requires a valid operand")
                expr_str = expr_str[:k+1] + f"({operand}/100)" + expr_str[i+1:]
                i = k + 1
        else:
            i -= 1
    return expr_str


def insert_implicit_multiplication(expr_str):
    """
    Inserts explicit multiplication '*' symbols where they are mathematically implicit.
    Example: 2(3+4) -> 2*(3+4), (2)3 -> (3)*3, 2pi -> 2*pi, 2sin(30) -> 2*sin(30)
    """
    # 1. Digit followed by '('
    expr_str = re.sub(r'(\d)(?=\()', r'\1*', expr_str)
    # 2. ')' followed by digit
    expr_str = re.sub(r'(\))(?=\d)', r'\1*', expr_str)
    # 3. ')' followed by '('
    expr_str = re.sub(r'(\))(?=\()', r'\1*', expr_str)
    # 4. Digit followed by letter (constant or function name)
    expr_str = re.sub(r'(\d)(?=[a-zA-Z_])', r'\1*', expr_str)
    # 5. ')' followed by letter (constant or function name)
    expr_str = re.sub(r'(\))(?=[a-zA-Z_])', r'\1*', expr_str)
    # 6. Constants and variables (pi, e, x) followed by '('
    expr_str = re.sub(r'\b(pi|e|x)(?=\()', r'\1*', expr_str)
    
    return expr_str


def preprocess_abs_bars(expr_str):
    """
    Replaces absolute value bars |expr| with abs(expr).
    Recursively processes nested bars from inside out.
    """
    old_expr = ""
    while old_expr != expr_str:
        old_expr = expr_str
        expr_str = re.sub(r'\|([^|]+)\|', r'abs(\1)', expr_str)
    return expr_str


def normalize_expression(expr_str):
    """
    Normalizes function names to uniform internal representation (e.g. asin to arcsin, acos to arccos, atan to arctan, and |x| to abs(x)).
    """
    # 1. |x| -> abs(x)
    expr_str = preprocess_abs_bars(expr_str)
    # 2. asin -> arcsin, acos -> arccos, atan -> arctan
    expr_str = re.sub(r'\basin\b', 'arcsin', expr_str)
    expr_str = re.sub(r'\bacos\b', 'arccos', expr_str)
    expr_str = re.sub(r'\batan\b', 'arctan', expr_str)
    return expr_str


def clean_expression_for_eval(expr_str):
    """
    Converts display symbols and normalizes functions to standard mathematical syntax.
    """
    # Apply normalization layer
    expr_str = normalize_expression(expr_str)
    
    # Replace display operators
    expr_str = expr_str.replace('×', '*').replace('÷', '/').replace('^', '**')
    # Replace constants
    expr_str = re.sub(r'\bπ\b', 'pi', expr_str)
    # Replace square root symbol
    # In display, we insert 'sqrt(' when user clicks root, but if they enter '√', replace it
    expr_str = expr_str.replace('√', 'sqrt')
    
    # Preprocess percentages
    expr_str = preprocess_percentage(expr_str)
    # Preprocess implicit multiplication
    expr_str = insert_implicit_multiplication(expr_str)
    
    return expr_str


def evaluate_expression(expr_str, angle_mode='deg'):
    """
    High-level entry point to clean and evaluate a math expression string.
    """
    cleaned = clean_expression_for_eval(expr_str)
    evaluator = SafeEvaluator(angle_mode=angle_mode)
    return evaluator.evaluate(cleaned)


def backspace_expression(expr_str):
    """
    Deletes the last token or character from the math expression, handling functions and spaces cleanly.
    """
    if not expr_str:
        return ""
    
    # Check multi-char functions ending with '('
    # Order matters: check longer prefixes first (e.g. cosec before sec, asin before sin)
    functions = [
        'acosec(', 'cosec(',
        'asin(', 'acos(', 'atan(', 'asec(', 'acot(', 'sqrt(', 'fact(',
        'sin(', 'cos(', 'tan(', 'sec(', 'cot(', 'log(',
        'ln('
    ]
    for func in functions:
        if expr_str.endswith(func):
            return expr_str[:-len(func)]
    
    # Check space-padded operators
    operators = [' + ', ' - ', ' × ', ' ÷ ', ' ^ ']
    for op in operators:
        if expr_str.endswith(op):
            return expr_str[:-len(op)]
            
    # Default: delete last character
    return expr_str[:-1]

