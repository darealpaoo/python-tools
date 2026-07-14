#simple-auto-click.py version 2.4
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import threading
import time
import ctypes
import os
import pyautogui
import configparser
import keyboard

# Remove pyautogui's built-in delay/safety so it doesn't bottleneck high-speed clicking
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

# Direct Windows mouse_event constants (bypasses pyautogui overhead for max cps)
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

FONT = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_SMALL = ("Segoe UI", 8)

# Tk keysym -> keyboard-lib key name, for the few that don't just lowercase cleanly
KEYSYM_TO_KEYBOARD_NAME = {
    "Escape": "esc", "Return": "enter", "BackSpace": "backspace", "Delete": "delete",
    "Tab": "tab", "Prior": "page up", "Next": "page down", "Insert": "insert",
    "Home": "home", "End": "end", "Up": "up", "Down": "down", "Left": "left", "Right": "right",
}
MODIFIER_KEYSYM_TO_NAME = {
    "Control_L": "ctrl", "Control_R": "ctrl",
    "Alt_L": "alt", "Alt_R": "alt",
    "Shift_L": "shift", "Shift_R": "shift",
    "Super_L": "windows", "Super_R": "windows",
}


def fast_click():
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def set_dpi_awareness():
    # Without this, Windows virtualizes screen coordinates on scaled displays and
    # Tk's centering math goes wrong, so the window sometimes lands partly below
    # the screen/taskbar. Must run before any Tk() window is created.
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


set_dpi_awareness()


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


class AutoClicker:
    WINDOW_WIDTH = 340
    WINDOW_HEIGHT = 300

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")

        if not self.config.has_section("Settings"):
            self.config.add_section("Settings")

        # Fill in any keys missing from an older config.ini without clobbering
        # values the user already has (e.g. existing Delay/AlwaysOnTop).
        defaults = {
            "AlwaysOnTop": "0",
            "Delay": "500",
            "ToggleHotkey": "f6",
            "HotkeyEnabled": "1",
            "EmergencyHotkey": "ctrl+alt+f9",
        }
        needs_write = False
        for key, value in defaults.items():
            if not self.config.has_option("Settings", key):
                self.config.set("Settings", key, value)
                needs_write = True
        if needs_write:
            with open("config.ini", "w") as f:
                self.config.write(f)

        self.delay = float(self.config.get("Settings", "Delay"))
        self.always_on_top = bool(int(self.config.get("Settings", "AlwaysOnTop")))
        self.toggle_hotkey = self.config.get("Settings", "ToggleHotkey")
        self.hotkey_enabled = bool(int(self.config.get("Settings", "HotkeyEnabled")))
        self.emergency_hotkey = self.config.get("Settings", "EmergencyHotkey")

        self._toggle_hook = None
        self._emergency_hook = None
        self._capture_mods = []

        self.root = tk.Tk()
        self.root.title("Auto Clicker")
        self.root.resizable(width=False, height=False)
        self.root.attributes("-toolwindow", True)
        self.root.attributes("-topmost", self.always_on_top)
        self.apply_window_position()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.style = ttk.Style()
        try:
            self.style.theme_use("vista")
        except tk.TclError:
            pass
        self.style.configure("TLabelframe.Label", font=FONT_BOLD)
        self.style.configure("TCheckbutton", font=FONT)
        self.style.configure("Green.TButton", font=FONT_BOLD, foreground="black", background="#2e7d32")
        self.style.configure("Red.TButton", font=FONT_BOLD, foreground="black", background="#c62828")

        self.is_running = False

        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        # --- Clicker settings ---
        frame_click = ttk.LabelFrame(main, text="Clicker", padding=10)
        frame_click.pack(fill="x")

        ttk.Label(frame_click, text="Delay (ms):", font=FONT).grid(row=0, column=0, padx=(0, 8), pady=6, sticky="w")
        self.entry_delay = tk.Entry(frame_click, font=FONT, width=8, justify="center")
        self.entry_delay.insert(0, self.format_delay(self.delay))
        self.entry_delay.grid(row=0, column=1, pady=6, sticky="w")

        self.button_start = ttk.Button(frame_click, text="Start", command=self.start_clicker, style="Green.TButton")
        self.button_start.grid(row=1, column=0, padx=(0, 8), pady=(4, 6), sticky="ew")

        self.button_stop = ttk.Button(frame_click, text="Stop", command=self.stop_clicker, state=tk.DISABLED, style="Red.TButton")
        self.button_stop.grid(row=1, column=1, padx=(0, 8), pady=(4, 6), sticky="ew")

        self.button_save = ttk.Button(frame_click, text="Save", command=self.save_config)
        self.button_save.grid(row=1, column=2, pady=(4, 6), sticky="ew")

        self.always_on_top_var = tk.BooleanVar(value=self.always_on_top)
        self.check_always_on_top = ttk.Checkbutton(frame_click, text="Always on top", command=self.set_always_on_top, variable=self.always_on_top_var, state="disabled")
        self.check_always_on_top.grid(row=2, column=0, columnspan=3, pady=(2, 0), sticky="w")

        # --- Hotkeys ---
        frame_hotkeys = ttk.LabelFrame(main, text="Hotkeys", padding=10)
        frame_hotkeys.pack(fill="x", pady=(10, 0))

        ttk.Label(frame_hotkeys, text="Toggle:", font=FONT).grid(row=0, column=0, padx=(0, 8), pady=6, sticky="w")
        self.entry_toggle_hotkey = tk.Entry(frame_hotkeys, font=FONT, width=14, justify="center", state="readonly", readonlybackground="white")
        self._set_entry_text(self.entry_toggle_hotkey, self.toggle_hotkey)
        self.entry_toggle_hotkey.grid(row=0, column=1, pady=6, sticky="w")
        self.entry_toggle_hotkey.bind("<Button-1>", lambda e: self.start_capture(self.entry_toggle_hotkey, "toggle"))

        self.hotkey_enabled_var = tk.BooleanVar(value=self.hotkey_enabled)
        self.check_hotkey_enabled = ttk.Checkbutton(frame_hotkeys, text="Enabled", variable=self.hotkey_enabled_var, command=self.on_hotkey_settings_changed)
        self.check_hotkey_enabled.grid(row=0, column=2, padx=(8, 0), pady=6, sticky="w")

        ttk.Label(frame_hotkeys, text="Emergency stop:", font=FONT).grid(row=1, column=0, padx=(0, 8), pady=6, sticky="w")
        self.entry_emergency_hotkey = tk.Entry(frame_hotkeys, font=FONT, width=14, justify="center", state="readonly", readonlybackground="white")
        self._set_entry_text(self.entry_emergency_hotkey, self.emergency_hotkey)
        self.entry_emergency_hotkey.grid(row=1, column=1, pady=6, sticky="w")
        self.entry_emergency_hotkey.bind("<Button-1>", lambda e: self.start_capture(self.entry_emergency_hotkey, "emergency"))

        ttk.Label(frame_hotkeys, text="Click a box, then press the key combo. Works even when the window isn't focused.",
                  font=FONT_SMALL, foreground="#666666", wraplength=280, justify="left").grid(row=2, column=0, columnspan=3, pady=(6, 0), sticky="w")

        self.set_always_on_top()
        self.apply_hotkeys()

        self.root.mainloop()

    @staticmethod
    def format_delay(value):
        # Display integers without a trailing .0, but keep one decimal for fractional values
        if float(value) == int(value):
            return str(int(value))
        return f"{value:.1f}"

    def get_delay_value(self):
        """Read delay from entry, clamp to minimum 0.1ms, round to 1 decimal place."""
        try:
            value = float(self.entry_delay.get())
        except ValueError:
            value = self.delay

        # Round to 1 decimal place (smallest allowed step is 0.1)
        value = round(value, 1)

        # Enforce minimum of 0.1ms
        if value < 0.1:
            value = 0.1

        # Reflect the clamped/rounded value back into the entry
        self.entry_delay.delete(0, tk.END)
        self.entry_delay.insert(0, self.format_delay(value))

        return value

    def get_work_area(self):
        # Excludes the taskbar, unlike winfo_screenwidth/height, so a restored
        # or centered window never lands hidden behind it.
        rect = RECT()
        SPI_GETWORKAREA = 0x0030
        if ctypes.windll.user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0):
            return rect.left, rect.top, rect.right, rect.bottom
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight()
        return 0, 0, w, h

    def apply_window_position(self):
        left, top, right, bottom = self.get_work_area()
        width, height = self.WINDOW_WIDTH, self.WINDOW_HEIGHT

        raw_x = self.config.get("Settings", "WindowX", fallback=None)
        raw_y = self.config.get("Settings", "WindowY", fallback=None)
        try:
            x, y = int(raw_x), int(raw_y)
        except (TypeError, ValueError):
            x = y = None

        # No saved position, or saved position no longer fits the current
        # monitor layout (e.g. a monitor got disconnected) -> re-center.
        if x is None or y is None or x < left or y < top or x + width > right or y + height > bottom:
            x = left + max(0, (right - left - width) // 2)
            y = top + max(0, (bottom - top - height) // 2)

        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def save_config(self):
        delay = self.get_delay_value()
        self.config.set("Settings", "Delay", str(delay))
        self.config.set("Settings", "AlwaysOnTop", str(int(self.always_on_top_var.get())))

        self.apply_hotkeys()
        self.config.set("Settings", "ToggleHotkey", self.toggle_hotkey)
        self.config.set("Settings", "HotkeyEnabled", str(int(self.hotkey_enabled)))
        self.config.set("Settings", "EmergencyHotkey", self.emergency_hotkey)

        with open("config.ini", "w") as f:
            self.config.write(f)

    def on_hotkey_settings_changed(self):
        self.apply_hotkeys()
        self.save_config()

    @staticmethod
    def _set_entry_text(entry, text):
        was_readonly = entry.cget("state") == "readonly"
        entry.config(state="normal")
        entry.delete(0, tk.END)
        entry.insert(0, text)
        if was_readonly:
            entry.config(state="readonly")

    def _normalize_keysym(self, keysym):
        if keysym in KEYSYM_TO_KEYBOARD_NAME:
            return KEYSYM_TO_KEYBOARD_NAME[keysym]
        return keysym.lower()

    def _suspend_hotkeys(self):
        # Both hotkeys must go fully offline while capturing, otherwise a key
        # pressed to define a new combo can still trigger the old one (e.g.
        # setting Toggle to the current Emergency combo fires a shutdown).
        try:
            if self._toggle_hook is not None:
                keyboard.remove_hotkey(self._toggle_hook)
        except (KeyError, ValueError):
            pass
        self._toggle_hook = None

        try:
            if self._emergency_hook is not None:
                keyboard.remove_hotkey(self._emergency_hook)
        except (KeyError, ValueError):
            pass
        self._emergency_hook = None

    def start_capture(self, entry, kind):
        self._suspend_hotkeys()
        self._capture_mods = []
        self._set_entry_text(entry, "Press a key...")
        entry.focus_set()
        entry.bind("<KeyPress>", lambda e: self._on_capture_key(e, entry, kind))
        entry.bind("<FocusOut>", lambda e: self._end_capture(entry, kind))
        return "break"

    def _end_capture(self, entry, kind):
        entry.unbind("<KeyPress>")
        entry.unbind("<FocusOut>")
        current = self.toggle_hotkey if kind == "toggle" else self.emergency_hotkey
        self._set_entry_text(entry, current)
        self.apply_hotkeys()

    def _on_capture_key(self, event, entry, kind):
        keysym = event.keysym

        if keysym in MODIFIER_KEYSYM_TO_NAME:
            name = MODIFIER_KEYSYM_TO_NAME[keysym]
            if name not in self._capture_mods:
                self._capture_mods.append(name)
            self._set_entry_text(entry, "+".join(self._capture_mods + ["..."]))
            return "break"

        key_name = self._normalize_keysym(keysym)
        combo = "+".join(self._capture_mods + [key_name])
        self._capture_mods = []
        self._set_entry_text(entry, combo)

        entry.unbind("<KeyPress>")
        entry.unbind("<FocusOut>")
        self.root.focus_set()
        self.on_hotkey_settings_changed()
        return "break"

    def apply_hotkeys(self):
        errors = []
        self._suspend_hotkeys()

        enabled = self.hotkey_enabled_var.get()
        toggle_combo = self.entry_toggle_hotkey.get().strip().lower()
        emergency_combo = self.entry_emergency_hotkey.get().strip().lower()

        if enabled:
            try:
                self._toggle_hook = keyboard.add_hotkey(toggle_combo, self.toggle_clicker_hotkey)
                self.toggle_hotkey = toggle_combo
            except Exception as e:
                errors.append(f"Toggle hotkey '{toggle_combo}' invalid: {e}")
                self._set_entry_text(self.entry_toggle_hotkey, self.toggle_hotkey)

        try:
            self._emergency_hook = keyboard.add_hotkey(emergency_combo, self.emergency_shutdown_hotkey)
            self.emergency_hotkey = emergency_combo
        except Exception as e:
            errors.append(f"Emergency hotkey '{emergency_combo}' invalid: {e}")
            self._set_entry_text(self.entry_emergency_hotkey, self.emergency_hotkey)

        self.hotkey_enabled = enabled

        if errors:
            messagebox.showerror("Hotkey error", "\n".join(errors))

    def toggle_clicker_hotkey(self):
        # Fires on keyboard lib's own thread; Tk widgets are only safe to touch
        # from the mainloop thread, so hop over via after().
        self.root.after(0, self._toggle_clicker)

    def _toggle_clicker(self):
        if self.is_running:
            self.stop_clicker()
        else:
            self.start_clicker()

    def emergency_shutdown_hotkey(self):
        self.root.after(0, self._emergency_shutdown)

    def _emergency_shutdown(self):
        self.is_running = False
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass
        os._exit(0)

    def on_close(self):
        self.is_running = False
        try:
            self.config.set("Settings", "WindowX", str(self.root.winfo_x()))
            self.config.set("Settings", "WindowY", str(self.root.winfo_y()))
            with open("config.ini", "w") as f:
                self.config.write(f)
        except Exception:
            pass
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        self.root.destroy()

    def start_clicker(self, event=None):
        if not self.is_running:
            self.is_running = True
            self.button_start.config(state=tk.DISABLED)
            self.button_stop.config(state=tk.NORMAL)
            t = threading.Thread(target=self.clicker, daemon=True)
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

            delay = self.get_delay_value()
            self.config.set("Settings", "Delay", str(delay))
            self.config.set("Settings", "AlwaysOnTop", str(int(self.always_on_top_var.get())))
            with open("config.ini", "w") as f:
                self.config.write(f)

    def stop_clicker(self, event=None):
        self.is_running = False

    def clicker(self):
        delay = self.get_delay_value() / 1000  # convert ms to seconds
        next_time = time.perf_counter()

        while self.is_running:
            fast_click()
            next_time += delay
            sleep_time = next_time - time.perf_counter()
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                # We're behind schedule (delay shorter than system can sustain);
                # reset reference to avoid runaway catch-up burst
                next_time = time.perf_counter()

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
        self.always_on_top = True
        self.always_on_top_var.set(self.always_on_top)
        self.root.attributes("-topmost", self.always_on_top)

    def update_delay(self):
        self.delay = float(self.config.get("Settings", "Delay"))
        self.entry_delay.delete(0, tk.END)
        self.entry_delay.insert(0, self.format_delay(self.delay))

    def reload_config(self):
        self.config.read("config.ini")
        self.update_always_on_top()
        self.update_delay()

if __name__ == "__main__":
    app = AutoClicker()
    app.reload_config()
