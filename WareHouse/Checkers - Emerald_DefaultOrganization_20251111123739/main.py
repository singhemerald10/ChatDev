'''
This is the main file for a simple text editor application using tkinter in Python. It includes functionalities such as open, save, exit, and now features cut, copy, paste, undo, and redo to enhance user interaction.
'''
import tkinter as tk
from tkinter import filedialog, messagebox, Text
import os
class MainApplication(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()
    def create_widgets(self):
        self.text_area = Text(self, undo=True)  # Enable undo feature of Text widget
        self.text_area.pack(expand=True, fill='both')
        self.menu = tk.Menu(self.master)
        self.master.config(menu=self.menu)
        # File menu
        file_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.quit)
        # Edit menu
        edit_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Cut", command=lambda: self.text_area.event_generate('<<Cut>>'))
        edit_menu.add_command(label="Copy", command=lambda: self.text_area.event_generate('<<Copy>>'))
        edit_menu.add_command(label="Paste", command=lambda: self.text_area.event_generate('<<Paste>>'))
        edit_menu.add_command(label="Undo", command=self.text_area.edit_undo)
        edit_menu.add_command(label="Redo", command=self.text_area.edit_redo)
        # Help menu
        help_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.about)
    def open_file(self):
        """
        Open a file dialog to select a file and read its contents into the text area.
        If an error occurs during file opening, display an error message.
        """
        file_path = filedialog.askopenfilename()
        if file_path:
            try:
                self.text_area.delete(1.0, tk.END)
                with open(file_path, 'r') as file:
                    self.text_area.insert(tk.END, file.read())
            except Exception as e:
                messagebox.showerror("Open File", f"Failed to open file: {e}")
    def save_file(self):
        """
        Open a save file dialog to specify the file path where the text will be saved.
        Write the contents of the text area to the file. If an error occurs during file saving, display an error message.
        """
        file_path = filedialog.asksaveasfilename()
        if file_path:
            try:
                with open(file_path, 'w') as file:
                    file.write(self.text_area.get(1.0, tk.END))
            except Exception as e:
                messagebox.showerror("Save File", f"Failed to save file: {e}")
    def about(self):
        """
        Display an informational message about the application.
        """
        messagebox.showinfo("About", "Simple Text Editor\nCreated in Python with tkinter. Now includes cut, copy, paste, undo, and redo functionalities.")
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Simple Text Editor")
    root.geometry("600x400")
    app = MainApplication(master=root)
    app.mainloop()