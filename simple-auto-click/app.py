#simple-auto-click.py version 1.0
import tkinter as tk
import tkinter.ttk as ttk
import threading
import time
import keyboard
import pyautogui
import configparser


class AutoClicker:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")

        # Set default values for config if they don't exist
        if not self.config.has_section("Settings"):
            self.config.add_section("Settings")
            self.config.set("Settings", "AlwaysOnTop", "0")
            self.config.set("Settings", "Delay", "500")
            with open("config.ini", "w") as f:
                self.config.write(f)

        self.delay = int(self.config.get("Settings", "Delay"))
        self.always_on_top = bool(int(self.config.get("Settings", "AlwaysOnTop")))

        self.root = tk.Tk()
        self.root.title("Auto Clicker")
        self.root.geometry("300x150")
        self.root.resizable(width=False, height=False)
        self.root.attributes("-topmost", self.always_on_top)

        self.is_running = False

        self.label_delay = tk.Label(self.root, text="Delay (ms):", font=("Arial", 12))
        self.label_delay.grid(row=0, column=0, padx=10, pady=10)

        self.entry_delay = tk.Entry(self.root, font=("Arial", 12), width=7)
        self.entry_delay.insert(0, str(self.delay))
        self.entry_delay.grid(row=0, column=1, padx=10, pady=10)

        self.button_start = ttk.Button(self.root, text="Start", command=self.start_clicker, style="Green.TButton")
        self.button_start.grid(row=1, column=0, padx=10, pady=10)

        self.button_stop = ttk.Button(self.root, text="Stop", command=self.stop_clicker, state=tk.DISABLED, style="Red.TButton")
        self.button_stop.grid(row=1, column=1, padx=10, pady=10)

        self.always_on_top_var = tk.BooleanVar(value=self.always_on_top)
        self.check_always_on_top = tk.Checkbutton(self.root, text="Always on top", command=self.set_always_on_top, variable=self.always_on_top_var, font=("Arial", 12))
        self.check_always_on_top.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

        self.button_save = ttk.Button(self.root, text="Save", command=self.save_config)
        self.button_save.grid(row=1, column=2, padx=10, pady=10)

        self.root.bind("<F5>", self.start_clicker)
        self.root.bind("<F6>", self.stop_clicker)

        self.style = ttk.Style()
        self.style.configure("Green.TButton", foreground="black", background="green")
        self.style.configure("Red.TButton", foreground="black", background="red")
        
        self.set_always_on_top()
        
        self.root.mainloop()

    def save_config(self):
        delay = int(self.entry_delay.get())
        self.config.set("Settings", "Delay", str(delay))
        self.config.set("Settings", "AlwaysOnTop", str(int(self.always_on_top_var.get())))
        with open("config.ini", "w") as f:
            self.config.write(f)

    def start_clicker(self, event=None):
        if not self.is_running:
            self.is_running = True
            self.button_start.config(state=tk.DISABLED)
            self.button_stop.config(state=tk.NORMAL)
            t = threading.Thread(target=self.clicker)
            t.start()

            def check_running():
                if not self.is_running:
                    self.button_start.config(state=tk.NORMAL)
                    self.button_stop.config(state=tk.DISABLED)
                else:
                    if not self.root.winfo_exists():
                        return
                    self.root.after(100, check_running)

            check_running()

            delay = int(self.entry_delay.get())
            self.config.set("Settings", "Delay", str(delay))
            self.config.set("Settings", "AlwaysOnTop", str(int(self.always_on_top_var.get())))
            with open("config.ini", "w") as f:
                self.config.write(f)

    def stop_clicker(self, event=None):
        self.is_running = False

    def clicker(self):
        delay = int(self.entry_delay.get())

        while self.is_running:
            pyautogui.click()
            time.sleep(delay / 1000)

    def set_always_on_top(self):
        self.always_on_top = self.always_on_top_var.get()
        if not self.root.winfo_exists():
            return
        self.root.attributes("-topmost", self.always_on_top)
        self.config.set("Settings", "AlwaysOnTop", str(int(self.always_on_top_var.get())))
        with open("config.ini", "w") as f:
            self.config.write(f)

    def update_always_on_top(self):
        if self.root is None or not hasattr(self.root, "winfo_exists") or not self.root.winfo_exists():
            return
        self.always_on_top = bool(int(self.config.get("Settings", "AlwaysOnTop")))
        self.always_on_top_var.set(self.always_on_top)
        self.root.attributes("-topmost", self.always_on_top)

    def update_delay(self):
        self.delay = int(self.config.get("Settings", "Delay"))
        self.entry_delay.delete(0, tk.END)
        self.entry_delay.insert(0, str(self.delay))

    def reload_config(self):
        self.config.read("config.ini")
        self.update_always_on_top()
        self.update_delay()

if __name__ == "__main__":
    app = AutoClicker()
    app.reload_config()