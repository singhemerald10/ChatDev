'''
File operations module for handling open, save, and save as functionalities in a text editor.
'''
import tkinter as tk
from tkinter import filedialog, messagebox
class FileOperations:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.current_file = None
    def open_file(self, file_path):
        try:
            with open(file_path, 'r') as file:
                file_contents = file.read()
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.insert(tk.END, file_contents)
            self.current_file = file_path
        except Exception as e:
            messagebox.showerror("Open File", f"Failed to open file: {e}")
    def save_file(self):
        if self.current_file:
            self._write_to_file(self.current_file)
        else:
            self.save_as_file()
    def save_as_file(self, file_path=None):
        if not file_path:
            file_path = filedialog.asksaveasfilename(defaultextension=".txt")
        if file_path:
            self._write_to_file(file_path)
            self.current_file = file_path
    def _write_to_file(self, file_path):
        try:
            file_contents = self.text_widget.get(1.0, tk.END)
            with open(file_path, 'w') as file:
                file.write(file_contents)
            self.current_file = file_path
        except Exception as e:
            messagebox.showerror("Save File", f"Failed to save file: {e}")