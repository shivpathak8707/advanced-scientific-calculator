import tkinter as tk
from ui import CalculatorApp

def main():
    root = tk.Tk()
    
    # Initialize the Calculator App
    app = CalculatorApp(root)
    
    # Keep running the UI main event loop
    root.mainloop()

if __name__ == "__main__":
    main()
