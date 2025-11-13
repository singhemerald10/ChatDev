'''
Main application file for a simple text editor. This file initializes the GUI and ties together user interactions with the application functionality.
'''
import tkinter as tk
from tkinter import filedialog, messagebox
from file_operations import FileOperations
class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Text Editor")
        self.text_area = tk.Text(self.root, undo=True)
        self.text_area.pack(fill=tk.BOTH, expand=1)
        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)
        self.file_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open", command=self.open_file)
        self.file_menu.add_command(label="Save", command=self.save_file)
        self.file_menu.add_command(label="Save As...", command=self.save_as_file)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.exit_app)
        self.file_ops = FileOperations(self.text_area)
    def open_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_ops.open_file(file_path)
    def save_file(self):
        self.file_ops.save_file()
    def save_as_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt")
        if file_path:
            self.file_ops.save_as_file(file_path)
    def exit_app(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.destroy()
if __name__ == "__main__":
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()