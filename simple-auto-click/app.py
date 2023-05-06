import tkinter as tk
import threading
import time
import keyboard
import pyautogui

class AutoClicker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Auto Clicker")
        self.root.resizable(width=False, height=False)

        self.is_running = False
        self.always_on_top = False

        self.label_delay = tk.Label(self.root, text="Delay (ms):")
        self.label_delay.grid(row=0, column=0, padx=10, pady=10)

        self.entry_delay = tk.Entry(self.root)
        self.entry_delay.insert(0, "500")
        self.entry_delay.grid(row=0, column=1, padx=10, pady=10)

        self.button_start = tk.Button(self.root, text="Start", command=self.start_clicker)
        self.button_start.grid(row=1, column=0, padx=10, pady=10)

        self.button_stop = tk.Button(self.root, text="Stop", command=self.stop_clicker, state=tk.DISABLED)
        self.button_stop.grid(row=1, column=1, padx=10, pady=10)

        self.check_always_on_top = tk.Checkbutton(self.root, text="Always on top", command=self.set_always_on_top)
        self.check_always_on_top.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

        self.root.bind("<F5>", self.start_clicker)
        self.root.bind("<F6>", self.stop_clicker)

        self.root.mainloop()

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
                    self.root.after(100, check_running)

            check_running()

    def stop_clicker(self, event=None):
        self.is_running = False

    def clicker(self):
        delay = int(self.entry_delay.get())

        while self.is_running:
            pyautogui.click()
            time.sleep(delay / 1000)

    def set_always_on_top(self):
        self.always_on_top = not self.always_on_top
        self.root.attributes("-topmost", self.always_on_top)

if __name__ == "__main__":
    AutoClicker()
