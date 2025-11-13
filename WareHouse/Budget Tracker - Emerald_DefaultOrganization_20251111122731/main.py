'''
Main application file for the Dashboard application.
This script initializes the GUI and starts the application.
'''
import tkinter as tk
from system_info import SystemInfo
import threading
class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Dashboard")
        self.system_info = SystemInfo()
        self.setup_ui()
    def setup_ui(self):
        # Display system information
        self.info_label = tk.Label(self.root, text=self.system_info.get_info(), font=('Arial', 12))
        self.info_label.pack(pady=20)
        # Refresh button to update the information
        refresh_button = tk.Button(self.root, text="Refresh", command=self.async_update_info)
        refresh_button.pack(pady=10)
    def async_update_info(self):
        thread = threading.Thread(target=self.refresh_info)
        thread.start()
    def refresh_info(self):
        # Fetch new info in a separate thread
        new_info = self.system_info.get_info()
        # Schedule the GUI update on the main thread
        self.root.after(0, self.update_info_label, new_info)
    def update_info_label(self, new_info):
        # Update the GUI with new information
        self.info_label.config(text=new_info)
def create_app():
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()
if __name__ == "__main__":
    create_app()