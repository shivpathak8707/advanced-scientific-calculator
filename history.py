import json
import os

class HistoryManager:
    def __init__(self, filename="history.json"):
        # Put the history file in the same directory as this script
        dir_path = os.path.dirname(os.path.abspath(__file__))
        self.filepath = os.path.join(dir_path, filename)
        self.history = []
        self.load_history()

    def load_history(self):
        """Loads history from the JSON file."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except Exception:
                # If there's an error reading (e.g. corruption), start with empty
                self.history = []
        else:
            self.history = []

    def save_history(self):
        """Saves history to the JSON file."""
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving history: {e}")

    def add_entry(self, expression, result):
        """Adds a calculation entry to the history."""
        # Clean up input strings
        entry = {
            "expression": expression,
            "result": result
        }
        # Avoid duplicate consecutive entries
        if not self.history or self.history[-1]["expression"] != expression:
            self.history.append(entry)
            # Limit history to last 50 entries
            if len(self.history) > 50:
                self.history.pop(0)
            self.save_history()

    def get_all(self):
        """Returns all history entries."""
        return self.history

    def clear(self):
        """Clears all history entries."""
        self.history = []
        self.save_history()
