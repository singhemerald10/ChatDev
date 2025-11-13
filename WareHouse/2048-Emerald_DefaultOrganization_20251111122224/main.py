'''
Main application file for the dashboard GUI.
'''
import tkinter as tk
from dashboard_frame import DashboardFrame
from config import WINDOW_TITLE, WINDOW_SIZE  # Import configuration settings
class MainApplication(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title(WINDOW_TITLE)  # Use the imported title
        self.geometry(WINDOW_SIZE)  # Use the imported window size
        # Initialize the dashboard frame
        dashboard = DashboardFrame(self)
        dashboard.pack(fill='both', expand=True)
if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()