import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import threading
import pystray
from PIL import Image, ImageDraw
import time
import os
import queue
import json

os.environ['PYTHONOPTIMIZE'] = '1'

class EyeSaverApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the main window
        self.popup = None
        self.close_button = None
        self.textbox = None
        self.popup_active = threading.Event()
        self.load_settings()
        self.running = True
        self.icon = None
        self.queue = queue.Queue()
        self.scheduled_popup = None  # Initialize scheduled_popup to None

    def load_settings(self):
        try:
            with open("eye_saver_settings.json", "r") as f:
                settings = json.load(f)
                self.REMINDER_INTERVAL = settings.get("reminder_interval", 1200000)  # Default 20 minutes
                self.LOOK_AWAY_TIME = settings.get("look_away_time", 20000)  # Default 20 seconds
                self.REMINDER_UNIT = settings.get("reminder_unit", "minutes")  # Default to minutes
        except FileNotFoundError:
            self.REMINDER_INTERVAL = 1200000  # 20 minutes in milliseconds
            self.LOOK_AWAY_TIME = 20000  # 20 seconds in milliseconds
            self.REMINDER_UNIT = "minutes"

    def save_settings(self):
        settings = {
            "reminder_interval": self.REMINDER_INTERVAL,
            "look_away_time": self.LOOK_AWAY_TIME,
            "reminder_unit": self.REMINDER_UNIT
        }
        with open("eye_saver_settings.json", "w") as f:
            json.dump(settings, f)

    def create_popup(self):
        if self.popup_active.is_set() or not self.running:
            return  # Don't create a new popup if one is already active or app is stopping

        self.popup = tk.Toplevel(self.root)
        self.popup.title("Eye Saver Reminder")
        self.popup.attributes('-topmost', True)
        self.popup.configure(bg='black')
        self.popup.geometry("300x150")

        self.textbox = tk.Text(self.popup, bg='black', fg='white', font=("Arial", 12), wrap=tk.WORD)
        self.textbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.textbox.insert(tk.END, f"Remember to look away\nfrom the screen\nfor {self.LOOK_AWAY_TIME // 1000} seconds")
        self.textbox.config(state=tk.DISABLED)

        self.close_button = tk.Button(self.popup, text="Close", command=self.close_popup, state=tk.DISABLED)
        self.close_button.pack(pady=10)

        self.popup.protocol("WM_DELETE_WINDOW", lambda: None)
        self.root.after(self.LOOK_AWAY_TIME, self.enable_closing)
        
        self.popup_active.set()

    def enable_closing(self):
        if not self.popup:
            return

        self.close_button.config(state=tk.NORMAL)
        self.textbox.config(state=tk.NORMAL)
        self.textbox.delete('1.0', tk.END)
        self.textbox.insert(tk.END, f"{self.LOOK_AWAY_TIME // 1000} seconds have passed.\nYou can now close this window\nand return to your work.")
        self.textbox.config(state=tk.DISABLED)
        self.popup.protocol("WM_DELETE_WINDOW", self.close_popup)

    def close_popup(self):
        if self.popup:
            self.popup.destroy()
            self.popup = None
        self.popup_active.clear()
        if self.running:
            self.schedule_next_popup()

    def schedule_next_popup(self):
        # Cancel existing scheduled popup if it exists
        if hasattr(self, 'scheduled_popup') and self.scheduled_popup is not None:
            self.root.after_cancel(self.scheduled_popup)
        # Schedule the next popup and store its ID
        self.scheduled_popup = self.root.after(self.REMINDER_INTERVAL, self.create_popup)

    def show_error(self, message):
        messagebox.showerror("Error", message)

    def create_image(self):
        image = Image.new('RGB', (64, 64), color=(73, 109, 137))
        d = ImageDraw.Draw(image)
        d.text((10, 10), "Eye", fill=(255, 255, 0))
        return image

    def open_settings(self):
        self.queue.put("OPEN_SETTINGS")

    def create_settings_window(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Eye Saver Settings")
        settings_window.geometry("300x250")

        tk.Label(settings_window, text="Reminder Interval:").pack(pady=5)
        reminder_entry = tk.Entry(settings_window)
        current_reminder_value = self.REMINDER_INTERVAL // (60000 if self.REMINDER_UNIT == "minutes" else 1000)
        reminder_entry.insert(0, str(current_reminder_value))
        reminder_entry.pack(pady=5)

        reminder_unit = tk.StringVar(value=self.REMINDER_UNIT)
        tk.Radiobutton(settings_window, text="Minutes", variable=reminder_unit, value="minutes").pack()
        tk.Radiobutton(settings_window, text="Seconds", variable=reminder_unit, value="seconds").pack()

        tk.Label(settings_window, text="Look Away Time (seconds):").pack(pady=5)
        look_away_entry = tk.Entry(settings_window)
        look_away_entry.insert(0, str(self.LOOK_AWAY_TIME // 1000))
        look_away_entry.pack(pady=5)

        def save_settings():
            try:
                new_reminder_unit = reminder_unit.get()
                new_reminder_interval = float(reminder_entry.get().strip())
                new_look_away_time = float(look_away_entry.get().strip())

                if new_reminder_interval <= 0 or new_look_away_time <= 0:
                    raise ValueError("Both Reminder Interval and Look Away Time must be positive numbers.")

                if new_reminder_unit == "minutes":
                    new_reminder_interval *= 60000
                else:
                    new_reminder_interval *= 1000

                new_look_away_time *= 1000

                self.REMINDER_INTERVAL = int(new_reminder_interval)
                self.LOOK_AWAY_TIME = int(new_look_away_time)
                self.REMINDER_UNIT = new_reminder_unit

                self.save_settings()
                settings_window.destroy()
                messagebox.showinfo("Settings Saved", "Your settings have been saved and applied.")
                
                # Reschedule the next popup with the updated interval
                self.schedule_next_popup()
            except ValueError as e:
                messagebox.showerror("Error", str(e))

        tk.Button(settings_window, text="Save", command=save_settings).pack(pady=10)

    def setup_tray_icon(self):
    # Dynamically generate an image for the icon
        image = Image.new('RGB', (64, 64), color=(73, 109, 137))  # Create a new image with specific size and background color
        d = ImageDraw.Draw(image)
        d.text((10, 10), "Eye", fill=(255, 255, 0))  # Draw text on the image

        # Convert the PIL Image object to a format suitable for pystray.Icon
        icon_image = image.resize((64, 64)).convert("RGBA")

        menu = (
            pystray.MenuItem('Settings', self.open_settings),
            pystray.MenuItem('Quit', self.quit_app)
        )

        self.icon = pystray.Icon("eye_saver", icon_image, "Eye Saver", menu)
        self.icon.run()

    def quit_app(self):
        self.running = False
        self.queue.put("QUIT")
        if self.icon:
            self.icon.stop()

    def run(self):
        try:
            self.schedule_next_popup()
            threading.Thread(target=self.setup_tray_icon, daemon=True).start()
            
            while self.running:
                self.root.update()
                try:
                    message = self.queue.get(False)
                    if message == "QUIT":
                        break
                    elif message == "OPEN_SETTINGS":
                        self.create_settings_window()
                except queue.Empty:
                    time.sleep(0.1)
        except Exception as e:
            self.show_error(f"Error in main loop: {str(e)}")
        finally:
            self.root.quit()
            os._exit(0)  # Force exit the program

if __name__ == "__main__":
    app = EyeSaverApp()
    app.run()
