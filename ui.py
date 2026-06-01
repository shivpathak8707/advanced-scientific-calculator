import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import re
import csv
import math
from PIL import Image, ImageDraw

# Module imports
from engine import evaluate_expression, backspace_expression
from history import HistoryManager
from solver import solve_polynomial, format_complex

# Exact values lookup table for trigonometric results and standard constants
EXACT_VALUES = [
    (0.5, "1/2"),
    (math.sqrt(2)/2, "√2/2"),
    (math.sqrt(3)/2, "√3/2"),
    (math.sqrt(3)/3, "√3/3"),
    (math.sqrt(3), "√3"),
    (math.sqrt(2), "√2"),
    (math.sqrt(5), "√5"),
    (2 * math.sqrt(3)/3, "2√3/3"),
    (math.pi, "π"),
    (math.pi/2, "π/2"),
    (math.pi/3, "π/3"),
    (math.pi/4, "π/4"),
    (math.pi/6, "π/6"),
    (math.e, "e")
]

def get_exact_representation(val):
    """Checks if a numeric value is close to a standard mathematical constant or radical, and returns its symbol."""
    if not isinstance(val, (int, float)):
        return None
    abs_val = abs(val)
    sign = "-" if val < 0 else ""
    for numeric_val, symbolic_str in EXACT_VALUES:
        if abs(abs_val - numeric_val) < 1e-9:
            return f"{sign}{symbolic_str}"
    return None

def get_all_representations(val):
    """Returns a list of unique string representations (exact radical, simplified fraction, decimal) for a float."""
    if not isinstance(val, (int, float)):
        return [str(val)]
        
    reprs = []
    
    # 1. Exact Symbolic Form (Trig values, radicals, pi, e)
    exact = get_exact_representation(val)
    if exact:
        reprs.append(exact)
        
    # 2. Simplified Fraction Form
    from fractions import Fraction
    try:
        f = Fraction(abs(val)).limit_denominator(1000)
        if f.denominator > 1 and abs(abs(val) - float(f)) < 1e-9:
            if f.denominator < 100:  # Only show simple fractions
                sign_str = "-" if val < 0 else ""
                frac_str = f"{sign_str}{f.numerator}/{f.denominator}"
                if frac_str not in reprs:
                    reprs.append(frac_str)
    except Exception:
        pass
        
    # 3. Decimal Form
    dec_str = str(int(val)) if val.is_integer() else str(round(val, 10))
    if dec_str not in reprs:
        reprs.append(dec_str)
        
    # Fallback
    if not reprs:
        reprs.append(str(val))
        
    return reprs


class HoverButton(tk.Button):
    """Highly interactive Tkinter Button with custom hover background transitions and flat design."""
    def __init__(self, master, normal_bg, hover_bg, text_color, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.normal_bg = normal_bg
        self.hover_bg = hover_bg
        self.text_color = text_color
        self.configure(
            bg=self.normal_bg,
            fg=self.text_color,
            activebackground=self.hover_bg,
            activeforeground=self.text_color,
            relief="flat",
            bd=0,
            highlightthickness=0
        )
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        
    def on_enter(self, event):
        self.configure(bg=self.hover_bg)
        
    def on_leave(self, event):
        self.configure(bg=self.normal_bg)
        
    def update_colors(self, normal_bg, hover_bg, text_color):
        self.normal_bg = normal_bg
        self.hover_bg = hover_bg
        self.text_color = text_color
        self.configure(bg=self.normal_bg, fg=self.text_color, activebackground=self.hover_bg, activeforeground=self.text_color)


class ScrollableFrame(tk.Frame):
    """A vertical scrollable frame layout container."""
    def __init__(self, container, bg_color, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self, bg=bg_color, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg_color)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self.canvas.bind("<Enter>", lambda _: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.canvas.bind("<Leave>", lambda _: self.canvas.unbind_all("<MouseWheel>"))

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
    def update_bg(self, bg_color):
        self.canvas.configure(bg=bg_color)
        self.scrollable_frame.configure(bg=bg_color)


class CalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Scientific Calculator")
        
        # Dimensions
        self.calc_width = 420
        self.calc_height = 680
        self.sidebar_width = 330
        self.root.geometry(f"{self.calc_width}x{self.calc_height}")
        self.root.minsize(self.calc_width, self.calc_height)
        
        # Style configuration
        self.light_mode = False
        
        # Cyberpunk Slate Dark Theme
        self.colors_dark = {
            "bg": "#121217",
            "display_bg": "#0b0b0f",
            "text_primary": "#ffffff",
            "text_secondary": "#a2a2ad",
            "btn_num": "#1c1c24",
            "btn_num_hover": "#262632",
            "btn_op": "#282a36",
            "btn_op_hover": "#343746",
            "btn_sci": "#16161f",
            "btn_sci_hover": "#20202d",
            "btn_action": "#3b1e3b",
            "btn_action_hover": "#4f2b4f",
            "btn_equal": "#6c5ce7",
            "btn_equal_hover": "#8070ff",
            "error": "#ff5555",
            "graph_grid": "#1c1c24",
            "graph_axis": "#a2a2ad"
        }
        
        # Soft Indigo Light Theme
        self.colors_light = {
            "bg": "#f0f2f5",
            "display_bg": "#ffffff",
            "text_primary": "#1c1e21",
            "text_secondary": "#5f6672",
            "btn_num": "#e4e6eb",
            "btn_num_hover": "#d8dadf",
            "btn_op": "#dadde1",
            "btn_op_hover": "#ccd0d5",
            "btn_sci": "#edf2f7",
            "btn_sci_hover": "#cbd5e0",
            "btn_action": "#fadcd9",
            "btn_action_hover": "#f8b4b0",
            "btn_equal": "#3182ce",
            "btn_equal_hover": "#2b6cb0",
            "error": "#d93025",
            "graph_grid": "#e2e8f0",
            "graph_axis": "#5f6672"
        }
        
        self.current_colors = self.colors_dark
        
        # State values
        self.expression = ""
        self.angle_mode = "deg"
        self.inverse_mode = False
        self.second_mode = False
        self.memory = 0.0
        self.memory_active = False
        self.x_value = 0.0  # Variable x default evaluation coordinate
        
        # Converter cycle variables
        self.value_representations = []
        self.repr_index = 0
        
        self.is_result_shown = False
        self.is_error_state = False
        self.sidebar_visible = False
        
        # Viewport boundaries for graphing canvas
        self.x_min, self.x_max = -10.0, 10.0
        self.y_min, self.y_max = -10.0, 10.0
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.start_x_min, self.start_x_max = -10.0, 10.0
        self.start_y_min, self.start_y_max = -10.0, 10.0
        
        self.history_manager = HistoryManager()
        self.history_items_refs = []
        
        # Build interface
        self.create_widgets()
        self.bind_keys()
        self.apply_theme()

    def create_widgets(self):
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=0)
        self.root.rowconfigure(0, weight=1)
        
        # --- Calculator Left Column ---
        self.main_container = tk.Frame(self.root, bg=self.current_colors["bg"])
        self.main_container.grid(row=0, column=0, sticky="nsew")
        self.main_container.columnconfigure(0, weight=1)
        self.main_container.rowconfigure(0, weight=0)  # Display screen
        self.main_container.rowconfigure(1, weight=0)  # Memory bar
        self.main_container.rowconfigure(2, weight=1)  # Keypad grid
        
        # Display screen panel
        self.display_frame = tk.Frame(self.main_container, bg=self.current_colors["display_bg"], height=140)
        self.display_frame.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 6))
        self.display_frame.pack_propagate(False)
        
        self.display_top_frame = tk.Frame(self.display_frame, bg=self.current_colors["display_bg"])
        self.display_top_frame.pack(fill="x", side="top", padx=10, pady=(6, 0))
        
        # DEG / RAD indicator (Clickable)
        self.mode_indicator_label = tk.Label(
            self.display_top_frame,
            text="DEG",
            font=("Segoe UI", 9, "bold"),
            fg=self.current_colors["btn_equal"],
            bg=self.current_colors["display_bg"],
            cursor="hand2"
        )
        self.mode_indicator_label.pack(side="left", padx=2)
        self.mode_indicator_label.bind("<Button-1>", lambda _: self.toggle_angle_mode())
        
        # Memory value indicator
        self.memory_label = tk.Label(
            self.display_top_frame,
            text="",
            font=("Segoe UI", 9, "italic"),
            fg=self.current_colors["text_secondary"],
            bg=self.current_colors["display_bg"]
        )
        self.memory_label.pack(side="left", padx=15)
        
        # Light / Dark Switch label
        self.theme_btn = tk.Label(
            self.display_top_frame,
            text="☀",
            font=("Segoe UI", 11, "bold"),
            fg=self.current_colors["text_secondary"],
            bg=self.current_colors["display_bg"],
            cursor="hand2"
        )
        self.theme_btn.pack(side="left", padx=5)
        self.theme_btn.bind("<Button-1>", lambda _: self.toggle_theme())
        
        # Running Formula display label
        self.formula_label = tk.Label(
            self.display_top_frame,
            text="",
            font=("Segoe UI", 11),
            fg=self.current_colors["text_secondary"],
            bg=self.current_colors["display_bg"],
            anchor="e"
        )
        self.formula_label.pack(side="right", fill="x", expand=True)
        
        # Current main formula text
        self.display_label = tk.Label(
            self.display_frame,
            text="0",
            font=("Segoe UI", 26, "bold"),
            fg=self.current_colors["text_primary"],
            bg=self.current_colors["display_bg"],
            anchor="e"
        )
        self.display_label.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        
        # --- Memory Bar ---
        self.memory_bar = tk.Frame(self.main_container, bg=self.current_colors["bg"])
        self.memory_bar.grid(row=1, column=0, sticky="ew", padx=12, pady=2)
        for i in range(4):
            self.memory_bar.columnconfigure(i, weight=1)
            
        mem_specs = [
            ("MC", self.memory_clear),
            ("MR", self.memory_recall),
            ("M+", self.memory_add),
            ("M-", self.memory_subtract)
        ]
        
        self.mem_buttons = []
        for idx, (lbl, cmd) in enumerate(mem_specs):
            btn = HoverButton(
                self.memory_bar,
                normal_bg=self.current_colors["btn_sci"],
                hover_bg=self.current_colors["btn_sci_hover"],
                text_color=self.current_colors["text_secondary"],
                text=lbl,
                font=("Segoe UI", 9, "bold"),
                command=cmd
            )
            btn.grid(row=0, column=idx, padx=2, sticky="ew")
            self.mem_buttons.append(btn)
            
        # --- Keypad Grid ---
        self.keypad_frame = tk.Frame(self.main_container, bg=self.current_colors["bg"])
        self.keypad_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=(6, 12))
        
        for r in range(7):
            self.keypad_frame.rowconfigure(r, weight=1)
        for c in range(5):
            self.keypad_frame.columnconfigure(c, weight=1)
            
        # 5 Columns Keypad layout mapping
        button_specs = [
            # Row 0
            ("Inv", 0, 0, "action"),
            ("sin", 0, 1, "sci"),
            ("cos", 0, 2, "sci"),
            ("tan", 0, 3, "sci"),
            ("⌫", 0, 4, "action"),
            
            # Row 1
            ("RAD/DEG", 1, 0, "action"),
            ("log", 1, 1, "sci"),
            ("ln", 1, 2, "sci"),
            ("^", 1, 3, "sci"),
            ("C", 1, 4, "action"),
            
            # Row 2
            ("History", 2, 0, "action"),
            ("(", 2, 1, "sci"),
            (")", 2, 2, "sci"),
            ("√", 2, 3, "sci"),
            ("÷", 2, 4, "op"),
            
            # Row 3
            ("x", 3, 0, "sci"),
            ("7", 3, 1, "num"),
            ("8", 3, 2, "num"),
            ("9", 3, 3, "num"),
            ("×", 3, 4, "op"),
            
            # Row 4
            ("π", 4, 0, "sci"),
            ("4", 4, 1, "num"),
            ("5", 4, 2, "num"),
            ("6", 4, 3, "num"),
            ("-", 4, 4, "op"),
            
            # Row 5
            ("%", 5, 0, "sci"),
            ("1", 5, 1, "num"),
            ("2", 5, 2, "num"),
            ("3", 5, 3, "num"),
            ("+", 5, 4, "op"),
            
            # Row 6
            ("2nd", 6, 0, "action"),
            ("0", 6, 1, "num"),
            (".", 6, 2, "num"),
            ("F↔D", 6, 3, "sci"),
            ("=", 6, 4, "equal")
        ]
        
        self.buttons_dict = {}
        for text, r, c, category in button_specs:
            cmd = self.get_button_command(text)
            font = ("Segoe UI", 12, "bold") if category in ("num", "op", "equal") else ("Segoe UI", 10, "bold")
            
            btn = HoverButton(
                self.keypad_frame,
                normal_bg=self.current_colors[f"btn_{category}"],
                hover_bg=self.current_colors[f"btn_{category}_hover"],
                text_color=self.current_colors["text_primary"],
                text=text,
                font=font,
                command=cmd
            )
            btn.grid(row=r, column=c, sticky="nsew", padx=3, pady=3)
            self.buttons_dict[text] = (btn, category)

        # --- Sidebar (Tabs) ---
        self.sidebar_frame = tk.Frame(self.root, bg=self.current_colors["bg"], bd=0, width=self.sidebar_width)
        
        self.sep = tk.Frame(self.sidebar_frame, bg=self.current_colors["btn_op"], width=1)
        self.sep.pack(side="left", fill="y")
        
        self.sidebar_content = tk.Frame(self.sidebar_frame, bg=self.current_colors["bg"])
        self.sidebar_content.pack(side="right", fill="both", expand=True, padx=8, pady=8)
        
        # Tabs control headers
        self.tabs_bar = tk.Frame(self.sidebar_content, bg=self.current_colors["bg"])
        self.tabs_bar.pack(fill="x", side="top", pady=(0, 10))
        
        self.tab_history_btn = HoverButton(
            self.tabs_bar,
            normal_bg=self.current_colors["btn_sci"], hover_bg=self.current_colors["btn_sci_hover"],
            text_color=self.current_colors["text_primary"], text="History", font=("Segoe UI", 8, "bold"),
            command=lambda: self.switch_tab("history"), padx=6, pady=4
        )
        self.tab_history_btn.pack(side="left", fill="x", expand=True, padx=1)
        
        self.tab_solver_btn = HoverButton(
            self.tabs_bar,
            normal_bg=self.current_colors["btn_sci"], hover_bg=self.current_colors["btn_sci_hover"],
            text_color=self.current_colors["text_primary"], text="Solver", font=("Segoe UI", 8, "bold"),
            command=lambda: self.switch_tab("solver"), padx=6, pady=4
        )
        self.tab_solver_btn.pack(side="left", fill="x", expand=True, padx=1)
        
        self.tab_graph_btn = HoverButton(
            self.tabs_bar,
            normal_bg=self.current_colors["btn_sci"], hover_bg=self.current_colors["btn_sci_hover"],
            text_color=self.current_colors["text_primary"], text="Graph", font=("Segoe UI", 8, "bold"),
            command=lambda: self.switch_tab("graph"), padx=6, pady=4
        )
        self.tab_graph_btn.pack(side="left", fill="x", expand=True, padx=1)
        
        # Tabs frame sheets
        self.history_panel = tk.Frame(self.sidebar_content, bg=self.current_colors["bg"])
        self.solver_panel = tk.Frame(self.sidebar_content, bg=self.current_colors["bg"])
        self.graph_panel = tk.Frame(self.sidebar_content, bg=self.current_colors["bg"])
        
        self.setup_history_panel()
        self.setup_solver_panel()
        self.setup_graph_panel()
        
        self.switch_tab("history")

    def setup_history_panel(self):
        search_frame = tk.Frame(self.history_panel, bg=self.current_colors["bg"])
        search_frame.pack(fill="x", side="top", pady=(0, 6))
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_history())
        
        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=("Segoe UI", 10),
            bg=self.current_colors["display_bg"],
            fg=self.current_colors["text_primary"],
            insertbackground=self.current_colors["text_primary"],
            relief="flat",
            bd=5
        )
        self.search_entry.pack(fill="x")
        
        self.scroll_hist = ScrollableFrame(self.history_panel, bg_color=self.current_colors["bg"])
        self.scroll_hist.pack(fill="both", expand=True)
        
        bottom_frame = tk.Frame(self.history_panel, bg=self.current_colors["bg"])
        bottom_frame.pack(fill="x", side="bottom", pady=(6, 0))
        
        self.export_csv_btn = HoverButton(
            bottom_frame,
            normal_bg=self.current_colors["btn_sci"], hover_bg=self.current_colors["btn_sci_hover"],
            text_color=self.current_colors["text_primary"], text="CSV", font=("Segoe UI", 8, "bold"),
            command=self.export_csv
        )
        self.export_csv_btn.pack(side="left", fill="x", expand=True, padx=1)
        
        self.export_txt_btn = HoverButton(
            bottom_frame,
            normal_bg=self.current_colors["btn_sci"], hover_bg=self.current_colors["btn_sci_hover"],
            text_color=self.current_colors["text_primary"], text="TXT", font=("Segoe UI", 8, "bold"),
            command=self.export_txt
        )
        self.export_txt_btn.pack(side="left", fill="x", expand=True, padx=1)
        
        self.clear_hist_btn = HoverButton(
            bottom_frame,
            normal_bg=self.current_colors["btn_action"], hover_bg=self.current_colors["btn_action_hover"],
            text_color=self.current_colors["text_secondary"], text="Clear", font=("Segoe UI", 8, "bold"),
            command=self.clear_history_ui
        )
        self.clear_hist_btn.pack(side="right", fill="x", expand=True, padx=1)

    def setup_solver_panel(self):
        lbl = tk.Label(self.solver_panel, text="Polynomial Solver", font=("Segoe UI", 11, "bold"), fg=self.current_colors["text_primary"], bg=self.current_colors["bg"])
        lbl.pack(fill="x", pady=2)
        
        dropdown_frame = tk.Frame(self.solver_panel, bg=self.current_colors["bg"])
        dropdown_frame.pack(fill="x", pady=4)
        
        tk.Label(dropdown_frame, text="Degree:", font=("Segoe UI", 9), fg=self.current_colors["text_secondary"], bg=self.current_colors["bg"]).pack(side="left")
        
        self.degree_var = tk.StringVar(value="Quadratic (ax²+bx+c=0)")
        self.degree_opt = ttk.OptionMenu(
            dropdown_frame,
            self.degree_var,
            "Quadratic (ax²+bx+c=0)",
            "Linear (ax+b=0)",
            "Quadratic (ax²+bx+c=0)",
            "Cubic (ax³+bx²+cx+d=0)",
            "Quartic (ax⁴+bx³+cx²+dx+e=0)",
            command=self.update_solver_inputs
        )
        self.degree_opt.pack(side="right", fill="x", expand=True, padx=5)
        
        self.coeff_frame = tk.Frame(self.solver_panel, bg=self.current_colors["bg"])
        self.coeff_frame.pack(fill="x", pady=6)
        
        results_lbl = tk.Label(self.solver_panel, text="Steps and Solution:", font=("Segoe UI", 9, "bold"), fg=self.current_colors["text_secondary"], bg=self.current_colors["bg"], anchor="w")
        results_lbl.pack(fill="x", pady=(8, 2))
        
        text_frame = tk.Frame(self.solver_panel, bg=self.current_colors["display_bg"])
        text_frame.pack(fill="both", expand=True)
        
        self.solver_text = tk.Text(
            text_frame,
            font=("Consolas", 9),
            bg=self.current_colors["display_bg"],
            fg=self.current_colors["text_primary"],
            insertbackground=self.current_colors["text_primary"],
            relief="flat",
            wrap="word",
            bd=4
        )
        scroll = tk.Scrollbar(text_frame, command=self.solver_text.yview)
        self.solver_text.configure(yscrollcommand=scroll.set)
        
        self.solver_text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        
        self.solve_btn = HoverButton(
            self.solver_panel,
            normal_bg=self.current_colors["btn_equal"], hover_bg=self.current_colors["btn_equal_hover"],
            text_color="#ffffff", text="Solve Equation", font=("Segoe UI", 10, "bold"),
            command=self.solve_equation_ui, pady=5
        )
        self.solve_btn.pack(fill="x", side="bottom", pady=(5, 0))
        self.update_solver_inputs()

    def setup_graph_panel(self):
        eq_frame = tk.Frame(self.graph_panel, bg=self.current_colors["bg"])
        eq_frame.pack(fill="x", pady=2)
        
        colors = ["#ff5252", "#ffc107", "#00e676"]
        self.graph_entries = []
        default_equations = ["sin(x)", "x^2", ""]
        
        for i in range(3):
            row = tk.Frame(eq_frame, bg=self.current_colors["bg"])
            row.pack(fill="x", pady=2)
            
            lbl = tk.Label(row, text=f"y{i+1}(x) =", font=("Segoe UI", 9, "bold"), fg=colors[i], bg=self.current_colors["bg"], width=7, anchor="e")
            lbl.pack(side="left")
            
            ent = tk.Entry(
                row,
                font=("Segoe UI", 9),
                bg=self.current_colors["display_bg"],
                fg=self.current_colors["text_primary"],
                insertbackground=self.current_colors["text_primary"],
                relief="flat",
                bd=3
            )
            ent.pack(side="right", fill="x", expand=True, padx=4)
            ent.insert(0, default_equations[i])
            self.graph_entries.append(ent)
            
        bounds_frame = tk.Frame(self.graph_panel, bg=self.current_colors["bg"])
        bounds_frame.pack(fill="x", pady=4)
        
        self.bounds_vars = {}
        bounds_labels = [("Xmin", "x_min", -10), ("Xmax", "x_max", 10), ("Ymin", "y_min", -10), ("Ymax", "y_max", 10)]
        
        for idx, (name, key, val) in enumerate(bounds_labels):
            cell = tk.Frame(bounds_frame, bg=self.current_colors["bg"])
            cell.grid(row=idx // 2, column=idx % 2, sticky="ew", padx=2, pady=1)
            bounds_frame.columnconfigure(idx % 2, weight=1)
            
            tk.Label(cell, text=f"{name}:", font=("Segoe UI", 8), fg=self.current_colors["text_secondary"], bg=self.current_colors["bg"]).pack(side="left")
            
            var = tk.StringVar(value=str(val))
            ent = tk.Entry(
                cell,
                textvariable=var,
                font=("Segoe UI", 8),
                bg=self.current_colors["display_bg"],
                fg=self.current_colors["text_primary"],
                relief="flat",
                width=6,
                bd=2
            )
            ent.pack(side="right", fill="x", expand=True, padx=2)
            self.bounds_vars[key] = var
            
        canvas_border = tk.Frame(self.graph_panel, bg=self.current_colors["btn_op"], bd=1)
        canvas_border.pack(fill="both", expand=True, pady=6)
        
        self.graph_canvas = tk.Canvas(
            canvas_border,
            bg=self.current_colors["display_bg"],
            highlightthickness=0,
            cursor="crosshair"
        )
        self.graph_canvas.pack(fill="both", expand=True)
        
        self.graph_canvas.bind("<ButtonPress-1>", self.on_graph_drag_press)
        self.graph_canvas.bind("<B1-Motion>", self.on_graph_drag_motion)
        self.graph_canvas.bind("<MouseWheel>", self.on_graph_scroll_zoom)
        
        ctl_frame = tk.Frame(self.graph_panel, bg=self.current_colors["bg"])
        ctl_frame.pack(fill="x", side="bottom", pady=(5, 0))
        
        self.plot_btn = HoverButton(
            ctl_frame,
            normal_bg=self.current_colors["btn_equal"], hover_bg=self.current_colors["btn_equal_hover"],
            text_color="#ffffff", text="Plot Graph", font=("Segoe UI", 9, "bold"),
            command=self.draw_graphs_ui
        )
        self.plot_btn.pack(side="left", fill="x", expand=True, padx=1)
        
        self.export_graph_btn = HoverButton(
            ctl_frame,
            normal_bg=self.current_colors["btn_sci"], hover_bg=self.current_colors["btn_sci_hover"],
            text_color=self.current_colors["text_primary"], text="Export Image", font=("Segoe UI", 9, "bold"),
            command=self.export_graph_png
        )
        self.export_graph_btn.pack(side="right", fill="x", expand=True, padx=1)

    def get_button_command(self, text):
        if text == "C":
            return self.clear_display
        elif text == "⌫":
            return self.backspace
        elif text == "RAD/DEG":
            return self.toggle_angle_mode
        elif text == "Inv":
            return self.toggle_inverse
        elif text == "2nd":
            return self.toggle_second
        elif text == "History":
            return self.toggle_sidebar
        elif text == "=":
            return self.evaluate_current
        elif text == "F↔D":
            return self.toggle_fraction_decimal
        elif text in ("sin", "cos", "tan", "log", "ln", "√", "x", "π", "%"):
            return lambda: self.append_keypad_char(text)
        elif text in ("+", "-", "×", "÷", "^"):
            return lambda: self.append_operator(f" {text} ")
        else:
            return lambda: self.append_to_expression(text)

    def switch_tab(self, tab_name):
        self.history_panel.pack_forget()
        self.solver_panel.pack_forget()
        self.graph_panel.pack_forget()
        
        inactive_bg = self.current_colors["btn_sci"]
        inactive_hover = self.current_colors["btn_sci_hover"]
        active_bg = self.current_colors["btn_equal"]
        active_hover = self.current_colors["btn_equal_hover"]
        
        self.tab_history_btn.update_colors(inactive_bg, inactive_hover, self.current_colors["text_primary"])
        self.tab_solver_btn.update_colors(inactive_bg, inactive_hover, self.current_colors["text_primary"])
        self.tab_graph_btn.update_colors(inactive_bg, inactive_hover, self.current_colors["text_primary"])
        
        if tab_name == "history":
            self.history_panel.pack(fill="both", expand=True)
            self.tab_history_btn.update_colors(active_bg, active_hover, "#ffffff")
            self.refresh_history_ui()
        elif tab_name == "solver":
            self.solver_panel.pack(fill="both", expand=True)
            self.tab_solver_btn.update_colors(active_bg, active_hover, "#ffffff")
        elif tab_name == "graph":
            self.graph_panel.pack(fill="both", expand=True)
            self.tab_graph_btn.update_colors(active_bg, active_hover, "#ffffff")
            self.root.after(100, self.draw_graphs_ui)

    def append_to_expression(self, value):
        if self.is_error_state:
            self.clear_display()
        if self.is_result_shown:
            if value.isdigit() or value in (".", "π", "e", "(", "x"):
                self.expression = ""
            self.is_result_shown = False
        self.expression += value
        self.update_display()

    def append_operator(self, op_value):
        if self.is_error_state:
            return
        if self.is_result_shown:
            self.is_result_shown = False
            
        stripped = self.expression.rstrip()
        if stripped and op_value.strip() in ("+", "×", "÷", "^"):
            last_three = self.expression[-3:]
            if last_three in (" + ", " - ", " × ", " ÷ ", " ^ "):
                self.expression = self.expression[:-3] + op_value
                self.update_display()
                return
                
        self.expression += op_value
        self.update_display()

    def append_keypad_char(self, label):
        """Processes keypad functions, variables, and constants depending on secondary modes."""
        if self.is_error_state:
            self.clear_display()
            
        prefix = ""
        # 1. Trigonometric Functions Mappings
        if label == "sin":
            if self.second_mode:
                prefix = "asec(" if self.inverse_mode else "sec("
            else:
                prefix = "asin(" if self.inverse_mode else "sin("
        elif label == "cos":
            if self.second_mode:
                prefix = "acosec(" if self.inverse_mode else "cosec("
            else:
                prefix = "acos(" if self.inverse_mode else "cos("
        elif label == "tan":
            if self.second_mode:
                prefix = "acot(" if self.inverse_mode else "cot("
            else:
                prefix = "atan(" if self.inverse_mode else "tan("
                
        # 2. Mathematical Functions
        elif label == "log":
            prefix = "10^(" if self.second_mode else "log("
        elif label == "ln":
            prefix = "e^(" if self.second_mode else "ln("
        elif label == "√":
            if self.second_mode:
                if self.is_result_shown and not self.is_error_state:
                    self.expression = f"({self.expression})^2"
                    self.is_result_shown = False
                    self.update_display()
                    return
                else:
                    self.expression += "^2"
                    self.update_display()
                    return
            else:
                prefix = "sqrt("
                
        # 3. Variable Key (x)
        elif label == "x":
            if self.second_mode:
                prefix = "fact("
            else:
                self.append_to_expression("x")
                return
                
        # 4. Constant Key (pi)
        elif label == "π":
            if self.second_mode:
                self.append_to_expression("e")
            else:
                self.append_to_expression("π")
            return
            
        # 5. Percentage Key (%)
        elif label == "%":
            self.append_to_expression("%")
            return
            
        # Wrap result or append function
        if prefix:
            if self.is_result_shown and not self.is_error_state:
                self.expression = f"{prefix}{self.expression})"
                self.is_result_shown = False
            else:
                self.expression += prefix
            self.update_display()

    def clear_display(self):
        self.expression = ""
        self.formula_label.configure(text="")
        self.is_result_shown = False
        self.is_error_state = False
        self.update_display()

    def backspace(self):
        if self.is_error_state or self.is_result_shown:
            self.clear_display()
            return
        self.expression = backspace_expression(self.expression)
        self.update_display()

    def update_display(self):
        txt = self.expression if self.expression else "0"
        if self.is_error_state:
            self.display_label.configure(text=txt, fg=self.current_colors["error"])
        else:
            self.display_label.configure(text=txt, fg=self.current_colors["text_primary"])

    def evaluate_current(self):
        if not self.expression or self.is_error_state:
            return
            
        formula_to_eval = self.expression
        try:
            # Substitute independent variable x with self.x_value on main display evaluations
            formula_for_eval = re.sub(r'\bx\b', f"({self.x_value})", formula_to_eval.replace('X', 'x'))
            
            res = evaluate_expression(formula_for_eval, self.angle_mode)
            
            # Format and generate converter representations list
            if isinstance(res, (int, float)):
                val_float = float(res)
                self.value_representations = get_all_representations(val_float)
                self.repr_index = 0
                res_str = self.value_representations[0]
            else:
                res_str = str(res)
                self.value_representations = [res_str]
                self.repr_index = 0
                
            self.formula_label.configure(text=f"{formula_to_eval} =")
            self.expression = res_str
            self.is_result_shown = True
            self.is_error_state = False
            
            # Save history
            self.history_manager.add_entry(formula_to_eval, res_str)
            if self.sidebar_visible:
                self.refresh_history_ui()
        except Exception as e:
            err_msg = str(e)
            if "Division by zero" in err_msg or "DivisionByZero" in err_msg:
                display_msg = "Math Error: Division by zero"
            elif "Domain" in err_msg or "out of range" in err_msg or "domain" in err_msg.lower():
                display_msg = "Domain Error"
            elif "Overflow" in err_msg:
                display_msg = "Overflow Error"
            elif "Math Error" in err_msg:
                display_msg = err_msg.split(":")[1].strip() if ":" in err_msg else "Math Error"
            elif "SyntaxError" in err_msg or "Syntax Error" in err_msg:
                display_msg = "Syntax Error"
            else:
                display_msg = "Math Error"
                
            self.formula_label.configure(text=f"{formula_to_eval} =")
            self.expression = display_msg
            self.is_result_shown = True
            self.is_error_state = True
            self.value_representations = []
            
        self.update_display()

    def toggle_angle_mode(self):
        if self.angle_mode == "deg":
            self.angle_mode = "rad"
            self.mode_indicator_label.configure(text="RAD")
        else:
            self.angle_mode = "deg"
            self.mode_indicator_label.configure(text="DEG")

    def toggle_inverse(self):
        self.inverse_mode = not self.inverse_mode
        self.update_keypad_labels()

    def toggle_second(self):
        self.second_mode = not self.second_mode
        self.update_keypad_labels()

    def update_keypad_labels(self):
        sin_btn, _ = self.buttons_dict["sin"]
        cos_btn, _ = self.buttons_dict["cos"]
        tan_btn, _ = self.buttons_dict["tan"]
        log_btn, _ = self.buttons_dict["log"]
        ln_btn, _ = self.buttons_dict["ln"]
        sqrt_btn, _ = self.buttons_dict["√"]
        x_btn, _ = self.buttons_dict["x"]
        pi_btn, _ = self.buttons_dict["π"]
        inv_btn, _ = self.buttons_dict["Inv"]
        sec_btn, _ = self.buttons_dict["2nd"]
        
        active_color = self.current_colors["btn_equal"]
        active_hover = self.current_colors["btn_equal_hover"]
        normal_act_color = self.current_colors["btn_action"]
        normal_act_hover = self.current_colors["btn_action_hover"]
        
        # Inv visual state toggle
        if self.inverse_mode:
            inv_btn.configure(bg=active_color, activebackground=active_hover)
            inv_btn.normal_bg = active_color
            inv_btn.hover_bg = active_hover
        else:
            inv_btn.configure(bg=normal_act_color, activebackground=normal_act_hover)
            inv_btn.normal_bg = normal_act_color
            inv_btn.hover_bg = normal_act_hover
            
        # 2nd visual state toggle
        if self.second_mode:
            sec_btn.configure(bg=active_color, activebackground=active_hover)
            sec_btn.normal_bg = active_color
            sec_btn.hover_bg = active_hover
        else:
            sec_btn.configure(bg=normal_act_color, activebackground=normal_act_hover)
            sec_btn.normal_bg = normal_act_color
            sec_btn.hover_bg = normal_act_hover

        if self.second_mode:
            sin_btn.configure(text="sec⁻¹" if self.inverse_mode else "sec")
            cos_btn.configure(text="csc⁻¹" if self.inverse_mode else "csc")
            tan_btn.configure(text="cot⁻¹" if self.inverse_mode else "cot")
            log_btn.configure(text="10^x")
            ln_btn.configure(text="e^x")
            sqrt_btn.configure(text="x^2")
            x_btn.configure(text="fact")
            pi_btn.configure(text="e")
        else:
            sin_btn.configure(text="sin⁻¹" if self.inverse_mode else "sin")
            cos_btn.configure(text="cos⁻¹" if self.inverse_mode else "cos")
            tan_btn.configure(text="tan⁻¹" if self.inverse_mode else "tan")
            log_btn.configure(text="log")
            ln_btn.configure(text="ln")
            sqrt_btn.configure(text="√")
            x_btn.configure(text="x")
            pi_btn.configure(text="π")

    def toggle_fraction_decimal(self):
        """Cycles through exact, simplified fraction, and decimal representations of the current display value."""
        if self.is_error_state or not self.expression:
            return
            
        # If representations list is empty, generate it from current display string
        if not self.value_representations:
            try:
                # Resolve value of display expression
                cleaned = re.sub(r'\bx\b', f"({self.x_value})", self.expression.replace('X', 'x'))
                val = evaluate_expression(cleaned, self.angle_mode)
                if isinstance(val, (int, float)):
                    self.value_representations = get_all_representations(float(val))
                    # Match current displayed string to align index
                    if self.expression in self.value_representations:
                        self.repr_index = self.value_representations.index(self.expression)
                    else:
                        self.repr_index = 0
            except Exception:
                pass
                
        if self.value_representations:
            self.repr_index = (self.repr_index + 1) % len(self.value_representations)
            self.expression = self.value_representations[self.repr_index]
            self.update_display()

    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar_frame.grid_forget()
            self.sidebar_visible = False
            self.root.geometry(f"{self.calc_width}x{self.calc_height}")
        else:
            self.sidebar_frame.grid(row=0, column=1, sticky="nsew")
            self.sidebar_visible = True
            self.root.geometry(f"{self.calc_width + self.sidebar_width}x{self.calc_height}")
            self.refresh_history_ui()

    # --- Memory Operations ---
    def memory_clear(self):
        self.memory = 0.0
        self.memory_active = False
        self.update_memory_indicator()

    def memory_recall(self):
        self.append_to_expression(str(self.memory))

    def memory_add(self):
        try:
            cleaned = re.sub(r'\bx\b', f"({self.x_value})", self.expression.replace('X', 'x'))
            val = evaluate_expression(cleaned, self.angle_mode)
            self.memory += float(val)
            self.memory_active = True
            self.update_memory_indicator()
        except Exception:
            pass

    def memory_subtract(self):
        try:
            cleaned = re.sub(r'\bx\b', f"({self.x_value})", self.expression.replace('X', 'x'))
            val = evaluate_expression(cleaned, self.angle_mode)
            self.memory -= float(val)
            self.memory_active = True
            self.update_memory_indicator()
        except Exception:
            pass

    def update_memory_indicator(self):
        if self.memory_active:
            m_val = round(self.memory, 4)
            if m_val.is_integer():
                m_val = int(m_val)
            self.memory_label.configure(text=f"M: {m_val}")
        else:
            self.memory_label.configure(text="")

    # --- Sidebar History Logic ---
    def refresh_history_ui(self):
        for widget in self.scroll_hist.scrollable_frame.winfo_children():
            widget.destroy()
            
        self.history_items_refs = []
        history_list = self.history_manager.get_all()
        
        if not history_list:
            empty = tk.Label(
                self.scroll_hist.scrollable_frame,
                text="No calculation history.",
                font=("Segoe UI", 9, "italic"),
                fg=self.current_colors["text_secondary"],
                bg=self.current_colors["bg"],
                pady=15
            )
            empty.pack(fill="x")
            return
            
        for entry in reversed(history_list):
            entry_frame = tk.Frame(self.scroll_hist.scrollable_frame, bg=self.current_colors["bg"], bd=0, cursor="hand2")
            entry_frame.pack(fill="x", pady=4, padx=2)
            
            expr_lbl = tk.Label(
                entry_frame,
                text=entry["expression"],
                font=("Segoe UI", 9),
                fg=self.current_colors["text_secondary"],
                bg=self.current_colors["bg"],
                anchor="w",
                justify="left"
            )
            expr_lbl.pack(fill="x", anchor="w")
            
            res_lbl = tk.Label(
                entry_frame,
                text=f"= {entry['result']}",
                font=("Segoe UI", 10, "bold"),
                fg=self.current_colors["text_primary"],
                bg=self.current_colors["bg"],
                anchor="w",
                justify="left"
            )
            res_lbl.pack(fill="x", anchor="w")
            
            divider = tk.Frame(entry_frame, bg=self.current_colors["btn_num"], height=1)
            divider.pack(fill="x", pady=(3, 0))
            
            def click_cmd(event, expr=entry["expression"]):
                self.expression = expr
                self.is_result_shown = False
                self.is_error_state = False
                self.formula_label.configure(text="")
                self.value_representations = []
                self.update_display()
                
            entry_frame.bind("<Button-1>", click_cmd)
            expr_lbl.bind("<Button-1>", click_cmd)
            res_lbl.bind("<Button-1>", click_cmd)
            
            self.history_items_refs.append({
                "frame": entry_frame,
                "expression": entry["expression"].lower(),
                "result": entry["result"].lower()
            })
            
            def on_enter(event, f=entry_frame, el=expr_lbl, rl=res_lbl):
                hl = "#1f1f26" if not self.light_mode else "#e4e6eb"
                f.configure(bg=hl)
                el.configure(bg=hl)
                rl.configure(bg=hl)
            def on_leave(event, f=entry_frame, el=expr_lbl, rl=res_lbl):
                hl = self.current_colors["bg"]
                f.configure(bg=hl)
                el.configure(bg=hl)
                rl.configure(bg=hl)
                
            entry_frame.bind("<Enter>", on_enter)
            entry_frame.bind("<Leave>", on_leave)
            expr_lbl.bind("<Enter>", on_enter)
            expr_lbl.bind("<Leave>", on_leave)
            res_lbl.bind("<Enter>", on_enter)
            res_lbl.bind("<Leave>", on_leave)
            
        self.filter_history()

    def filter_history(self):
        term = self.search_var.get().lower().strip()
        for item in self.history_items_refs:
            if term in item["expression"] or term in item["result"]:
                item["frame"].pack(fill="x", pady=4, padx=2)
            else:
                item["frame"].pack_forget()

    def clear_history_ui(self):
        self.history_manager.clear()
        self.refresh_history_ui()

    def export_csv(self):
        history_list = self.history_manager.get_all()
        if not history_list:
            messagebox.showinfo("Export Warning", "No calculations in history to export.")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if filepath:
            try:
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    w = csv.writer(f)
                    w.writerow(["Expression", "Result"])
                    for item in history_list:
                        w.writerow([item["expression"], item["result"]])
                messagebox.showinfo("Success", "History exported successfully to CSV!")
            except Exception as e:
                messagebox.showerror("Error", f"Could not export CSV file: {e}")

    def export_txt(self):
        history_list = self.history_manager.get_all()
        if not history_list:
            messagebox.showinfo("Export Warning", "No calculations in history to export.")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    for item in history_list:
                        f.write(f"{item['expression']} = {item['result']}\n")
                messagebox.showinfo("Success", "History exported successfully to TXT!")
            except Exception as e:
                messagebox.showerror("Error", f"Could not export TXT file: {e}")

    # --- Polynomial Solver UI ---
    def update_solver_inputs(self, event=None):
        for w in self.coeff_frame.winfo_children():
            w.destroy()
            
        degree_text = self.degree_var.get()
        if "Linear" in degree_text:
            labels = ["a (coefficient of x)", "b (constant term)"]
        elif "Quadratic" in degree_text:
            labels = ["a (x² term)", "b (x term)", "c (constant term)"]
        elif "Cubic" in degree_text:
            labels = ["a (x³ term)", "b (x² term)", "c (x term)", "d (constant term)"]
        else:
            labels = ["a (x⁴ term)", "b (x³ term)", "c (x² term)", "d (x term)", "e (constant)"]
            
        self.solver_entries = []
        for i, text in enumerate(labels):
            row = tk.Frame(self.coeff_frame, bg=self.current_colors["bg"])
            row.pack(fill="x", pady=2)
            
            lbl = tk.Label(row, text=f"{text}:", font=("Segoe UI", 9), fg=self.current_colors["text_secondary"], bg=self.current_colors["bg"], width=15, anchor="w")
            lbl.pack(side="left")
            
            ent = tk.Entry(
                row,
                font=("Segoe UI", 9),
                bg=self.current_colors["display_bg"],
                fg=self.current_colors["text_primary"],
                insertbackground=self.current_colors["text_primary"],
                relief="flat",
                bd=3
            )
            ent.pack(side="right", fill="x", expand=True, padx=4)
            ent.insert(0, "0")
            self.solver_entries.append(ent)

    def solve_equation_ui(self):
        coeffs = []
        for idx, ent in enumerate(self.solver_entries):
            val_str = ent.get().strip()
            try:
                val = float(val_str)
                coeffs.append(val)
            except ValueError:
                try:
                    if '/' in val_str:
                        num, den = map(float, val_str.split('/'))
                        coeffs.append(num / den)
                        continue
                except Exception:
                    pass
                messagebox.showerror("Coefficient Error", f"Invalid numeric entry at field index {idx+1}")
                return
                
        res = solve_polynomial(coeffs)
        
        self.solver_text.configure(state="normal")
        self.solver_text.delete("1.0", tk.END)
        self.solver_text.insert(tk.END, res["steps"] + "\n\n")
        self.solver_text.insert(tk.END, "Roots found:\n")
        
        for idx, root in enumerate(res["roots"]):
            self.solver_text.insert(tk.END, f" x{idx+1} = {format_complex(root)}\n")
            
        self.solver_text.configure(state="disabled")

    # --- Graph Canvas Plotter ---
    def eval_fx(self, expr, x):
        expr_clean = expr.replace('X', 'x')
        expr_clean = re.sub(r'\bx\b', f"({x})", expr_clean)
        return evaluate_expression(expr_clean, angle_mode="rad")

    def draw_graphs_ui(self):
        try:
            self.x_min = float(self.bounds_vars["x_min"].get())
            self.x_max = float(self.bounds_vars["x_max"].get())
            self.y_min = float(self.bounds_vars["y_min"].get())
            self.y_max = float(self.bounds_vars["y_max"].get())
        except ValueError:
            pass
            
        if self.x_min >= self.x_max or self.y_min >= self.y_max:
            return
            
        self.graph_canvas.delete("all")
        
        c_width = self.graph_canvas.winfo_width()
        c_height = self.graph_canvas.winfo_height()
        if c_width <= 1: c_width = 280
        if c_height <= 1: c_height = 280
        
        grid_color = self.current_colors["graph_grid"]
        axis_color = self.current_colors["graph_axis"]
        text_color = self.current_colors["text_secondary"]
        
        plot_colors = ["#ff5252", "#ffc107", "#00e676"] if not self.light_mode else ["#b00020", "#c68400", "#007a22"]
        
        def to_canvas(mx, my):
            cx = ((mx - self.x_min) / (self.x_max - self.x_min)) * c_width
            cy = c_height - (((my - self.y_min) / (self.y_max - self.y_min)) * c_height)
            return cx, cy
            
        # Draw math grid background
        grid_steps = 10
        y_step = (self.y_max - self.y_min) / grid_steps
        for i in range(grid_steps + 1):
            my = self.y_min + i * y_step
            _, cy = to_canvas(0, my)
            self.graph_canvas.create_line(0, cy, c_width, cy, fill=grid_color, width=1)
            if abs(my) > 1e-9:
                self.graph_canvas.create_text(20, cy - 6, text=f"{round(my, 2)}", font=("Segoe UI", 7), fill=text_color)
                
        x_step = (self.x_max - self.x_min) / grid_steps
        for i in range(grid_steps + 1):
            mx = self.x_min + i * x_step
            cx, _ = to_canvas(mx, 0)
            self.graph_canvas.create_line(cx, 0, cx, c_height, fill=grid_color, width=1)
            if abs(mx) > 1e-9:
                self.graph_canvas.create_text(cx + 10, c_height - 10, text=f"{round(mx, 2)}", font=("Segoe UI", 7), fill=text_color)

        # Main X and Y axes
        cx_axis, cy_axis = to_canvas(0, 0)
        self.graph_canvas.create_line(0, cy_axis, c_width, cy_axis, fill=axis_color, width=2)
        self.graph_canvas.create_line(cx_axis, 0, cx_axis, c_height, fill=axis_color, width=2)
        
        # Axis labels
        if 0 <= cy_axis <= c_height:
            self.graph_canvas.create_text(c_width - 15, cy_axis - 10, text="x", font=("Segoe UI", 9, "bold"), fill=axis_color)
        if 0 <= cx_axis <= c_width:
            self.graph_canvas.create_text(cx_axis + 10, 15, text="y", font=("Segoe UI", 9, "bold"), fill=axis_color)
            
        if 0 <= cx_axis <= c_width and 0 <= cy_axis <= c_height:
            self.graph_canvas.create_text(cx_axis - 10, cy_axis + 10, text="0", font=("Segoe UI", 8, "bold"), fill=axis_color)

        # Plot curves
        steps = 250
        step_dx = (self.x_max - self.x_min) / steps
        
        for eq_idx, ent in enumerate(self.graph_entries):
            eq_expr = ent.get().strip()
            if not eq_expr:
                continue
                
            prev_pt = None
            color = plot_colors[eq_idx]
            
            for i in range(steps + 1):
                mx = self.x_min + i * step_dx
                try:
                    my = self.eval_fx(eq_expr, mx)
                    if math.isnan(my) or math.isinf(my) or abs(my) > 1e6:
                        prev_pt = None
                        continue
                        
                    cx, cy = to_canvas(mx, my)
                    
                    if prev_pt:
                        # Asymptote crossing check
                        # If Y values cross the zero line and the delta is larger than 1.5 * Y range,
                        # skip drawing the connecting line segment (prevents vertical line artifacts).
                        y_range = self.y_max - self.y_min
                        prev_my = prev_pt[2]
                        if (prev_my * my < 0) and (abs(my - prev_my) > 1.5 * y_range):
                            pass
                        else:
                            self.graph_canvas.create_line(prev_pt[0], prev_pt[1], cx, cy, fill=color, width=2)
                    prev_pt = (cx, cy, my)
                except Exception:
                    prev_pt = None

    def on_graph_drag_press(self, event):
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.start_x_min = self.x_min
        self.start_x_max = self.x_max
        self.start_y_min = self.y_min
        self.start_y_max = self.y_max

    def on_graph_drag_motion(self, event):
        c_width = self.graph_canvas.winfo_width()
        c_height = self.graph_canvas.winfo_height()
        if c_width <= 1: c_width = 280
        if c_height <= 1: c_height = 280
        
        dcx = event.x - self.pan_start_x
        dcy = event.y - self.pan_start_y
        
        x_range = self.start_x_max - self.start_x_min
        y_range = self.start_y_max - self.start_y_min
        
        dx = (dcx / c_width) * x_range
        dy = (dcy / c_height) * y_range
        
        self.x_min = self.start_x_min - dx
        self.x_max = self.start_x_max - dx
        self.y_min = self.start_y_min + dy
        self.y_max = self.start_y_max + dy
        
        self.bounds_vars["x_min"].set(str(round(self.x_min, 3)))
        self.bounds_vars["x_max"].set(str(round(self.x_max, 3)))
        self.bounds_vars["y_min"].set(str(round(self.y_min, 3)))
        self.bounds_vars["y_max"].set(str(round(self.y_max, 3)))
        
        self.draw_graphs_ui()

    def on_graph_scroll_zoom(self, event):
        c_width = self.graph_canvas.winfo_width()
        c_height = self.graph_canvas.winfo_height()
        if c_width <= 1: c_width = 280
        if c_height <= 1: c_height = 280
        
        mx = self.x_min + (event.x / c_width) * (self.x_max - self.x_min)
        my = self.y_min + ((c_height - event.y) / c_height) * (self.y_max - self.y_min)
        
        factor = 0.85 if event.delta > 0 else 1.15
        
        self.x_min = mx - (mx - self.x_min) * factor
        self.x_max = mx + (self.x_max - mx) * factor
        self.y_min = my - (my - self.y_min) * factor
        self.y_max = my + (self.y_max - my) * factor
        
        self.bounds_vars["x_min"].set(str(round(self.x_min, 3)))
        self.bounds_vars["x_max"].set(str(round(self.x_max, 3)))
        self.bounds_vars["y_min"].set(str(round(self.y_min, 3)))
        self.bounds_vars["y_max"].set(str(round(self.y_max, 3)))
        
        self.draw_graphs_ui()

    def export_graph_png(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Images", "*.png")])
        if not filepath:
            return
            
        width, height = 500, 500
        img = Image.new("RGB", (width, height), self.current_colors["display_bg"])
        draw = ImageDraw.Draw(img)
        
        grid_color = self.current_colors["graph_grid"]
        axis_color = self.current_colors["graph_axis"]
        plot_colors = ["#ff5252", "#ffc107", "#00e676"] if not self.light_mode else ["#b00020", "#c68400", "#007a22"]
        
        def to_img_canvas(mx, my):
            cx = ((mx - self.x_min) / (self.x_max - self.x_min)) * width
            cy = height - (((my - self.y_min) / (self.y_max - self.y_min)) * height)
            return cx, cy

        # Draw grid
        for i in range(11):
            my = self.y_min + i * (self.y_max - self.y_min) / 10
            _, cy = to_img_canvas(0, my)
            draw.line([(0, cy), (width, cy)], fill=grid_color)
            
        for i in range(11):
            mx = self.x_min + i * (self.x_max - self.x_min) / 10
            cx, _ = to_img_canvas(mx, 0)
            draw.line([(cx, 0), (cx, height)], fill=grid_color)
            
        cx_axis, cy_axis = to_img_canvas(0, 0)
        draw.line([(0, cy_axis), (width, cy_axis)], fill=axis_color, width=2)
        draw.line([(cx_axis, 0), (cx_axis, height)], fill=axis_color, width=2)
        
        # Plot curves
        steps = 250
        dx = (self.x_max - self.x_min) / steps
        for eq_idx, ent in enumerate(self.graph_entries):
            expr = ent.get().strip()
            if not expr:
                continue
            prev = None
            color = plot_colors[eq_idx]
            for i in range(steps + 1):
                mx = self.x_min + i * dx
                try:
                    my = self.eval_fx(expr, mx)
                    if math.isnan(my) or math.isinf(my) or abs(my) > 1e6:
                        prev = None
                        continue
                    cx, cy = to_img_canvas(mx, my)
                    if prev:
                        y_range = self.y_max - self.y_min
                        prev_my = prev[2]
                        if (prev_my * my < 0) and (abs(my - prev_my) > 1.5 * y_range):
                            pass
                        else:
                            draw.line([(prev[0], prev[1]), (cx, cy)], fill=color, width=2)
                    prev = (cx, cy, my)
                except Exception:
                    prev = None
        try:
            img.save(filepath)
            messagebox.showinfo("Success", "Graph exported successfully as PNG image!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image: {e}")

    # --- Clipboard Clipboard Support ---
    def copy_to_clipboard(self, event=None):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.display_label.cget("text"))
        self.formula_label.configure(text="Result Copied!")
        return "break"

    def paste_from_clipboard(self, event=None):
        try:
            text = self.root.clipboard_get()
            clean_text = "".join(c for c in text if c.isalnum() or c in "+-*/^%()._ =×÷πe√")
            self.append_to_expression(clean_text)
        except Exception:
            pass
        return "break"

    # --- Themes Toggle ---
    def toggle_theme(self):
        self.light_mode = not self.light_mode
        self.theme_btn.configure(text="☾" if self.light_mode else "☀")
        self.apply_theme()
        self.update_keypad_labels()
        if self.sidebar_visible:
            self.refresh_history_ui()
            self.draw_graphs_ui()

    def apply_theme(self):
        theme = self.colors_light if self.light_mode else self.colors_dark
        self.current_colors = theme
        
        self.root.configure(bg=theme["bg"])
        self.main_container.configure(bg=theme["bg"])
        self.display_frame.configure(bg=theme["display_bg"])
        self.display_top_frame.configure(bg=theme["display_bg"])
        self.mode_indicator_label.configure(bg=theme["display_bg"], fg=theme["btn_equal"])
        self.memory_label.configure(bg=theme["display_bg"], fg=theme["text_secondary"])
        self.theme_btn.configure(bg=theme["display_bg"], fg=theme["text_secondary"])
        self.formula_label.configure(bg=theme["display_bg"], fg=theme["text_secondary"])
        self.display_label.configure(bg=theme["display_bg"])
        self.update_display()
        
        self.memory_bar.configure(bg=theme["bg"])
        self.keypad_frame.configure(bg=theme["bg"])
        
        for btn in self.mem_buttons:
            btn.update_colors(theme["btn_sci"], theme["btn_sci_hover"], theme["text_secondary"])
            
        for text, (btn, category) in self.buttons_dict.items():
            btn.update_colors(theme[f"btn_{category}"], theme[f"btn_{category}_hover"], theme["text_primary"])
            
        self.sidebar_frame.configure(bg=theme["bg"])
        self.sep.configure(bg=theme["btn_op"])
        self.sidebar_content.configure(bg=theme["bg"])
        self.tabs_bar.configure(bg=theme["bg"])
        
        inactive_bg = theme["btn_sci"]
        inactive_hover = theme["btn_sci_hover"]
        self.tab_history_btn.update_colors(inactive_bg, inactive_hover, theme["text_primary"])
        self.tab_solver_btn.update_colors(inactive_bg, inactive_hover, theme["text_primary"])
        self.tab_graph_btn.update_colors(inactive_bg, inactive_hover, theme["text_primary"])
        
        self.history_panel.configure(bg=theme["bg"])
        self.solver_panel.configure(bg=theme["bg"])
        self.graph_panel.configure(bg=theme["bg"])
        
        self.search_entry.configure(bg=theme["display_bg"], fg=theme["text_primary"], insertbackground=theme["text_primary"])
        self.scroll_hist.update_bg(theme["bg"])
        self.export_csv_btn.update_colors(theme["btn_sci"], theme["btn_sci_hover"], theme["text_primary"])
        self.export_txt_btn.update_colors(theme["btn_sci"], theme["btn_sci_hover"], theme["text_primary"])
        self.clear_hist_btn.update_colors(theme["btn_action"], theme["btn_action_hover"], theme["text_secondary"])
        
        self.coeff_frame.configure(bg=theme["bg"])
        self.solver_text.configure(bg=theme["display_bg"], fg=theme["text_primary"], insertbackground=theme["text_primary"])
        self.solve_btn.update_colors(theme["btn_equal"], theme["btn_equal_hover"], "#ffffff")
        
        self.graph_canvas.configure(bg=theme["display_bg"])
        self.plot_btn.update_colors(theme["btn_equal"], theme["btn_equal_hover"], "#ffffff")
        self.export_graph_btn.update_colors(theme["btn_sci"], theme["btn_sci_hover"], theme["text_primary"])

    # --- Keyboard Support ---
    def bind_keys(self):
        self.root.bind("<Key>", self.handle_key)
        self.root.bind("<Control-c>", self.copy_to_clipboard)
        self.root.bind("<Control-v>", self.paste_from_clipboard)
        self.root.bind("<Control-C>", self.copy_to_clipboard)
        self.root.bind("<Control-V>", self.paste_from_clipboard)

    def handle_key(self, event):
        char = event.char
        keysym = event.keysym
        
        if event.state & 0x4:  # Control key pressed
            return
            
        # Allow typing direct alphanumeric variables and standard mathematical syntax
        if char and (char.isalnum() or char in "+-*/^%()._ =×÷πe√"):
            if char == "=":
                self.evaluate_current()
            elif char == " ":
                self.append_to_expression(char)
            else:
                # Key mappings to nicely formatted display operators
                if char == "*":
                    self.append_operator(" × ")
                elif char == "/":
                    self.append_operator(" ÷ ")
                elif char == "^":
                    self.append_operator(" ^ ")
                elif char in ("+", "-"):
                    self.append_operator(f" {char} ")
                else:
                    self.append_to_expression(char)
        elif keysym in ("Return", "KP_Enter"):
            self.evaluate_current()
        elif keysym == "BackSpace":
            self.backspace()
        elif keysym in ("Escape", "Delete"):
            self.clear_display()
