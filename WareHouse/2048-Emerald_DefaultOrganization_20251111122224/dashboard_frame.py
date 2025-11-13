'''
Module for handling the dashboard frame in the GUI.
'''
import tkinter as tk
import logging
class DashboardFrame(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.create_widgets()
    def create_widgets(self):
        self.label = tk.Label(self, text="Welcome to the Dashboard")
        self.label.pack(pady=10)
        self.entry = tk.Entry(self)
        self.entry.pack(pady=10)
        self.button = tk.Button(self, text="Click Me!", command=self.on_button_click)
        self.button.pack(pady=10)
    def on_button_click(self):
        try:
            entered_text = self.entry.get()
            if not entered_text:
                raise ValueError("Please enter some text.")
            self.label.config(text=f"Hello, {entered_text}!")
        except ValueError as ve:
            self.label.config(text=str(ve))
            logging.error(f"ValueError: {ve}")
        except Exception as e:
            self.label.config(text="Error: An unexpected error occurred.")
            logging.error(f"Unhandled exception: {e}")
# Setup logging
logging.basicConfig(filename='dashboard_errors.log', level=logging.ERROR, format='%(asctime)s:%(levelname)s:%(message)s')