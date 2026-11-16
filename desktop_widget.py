"""DEYEapp live-only desktop widget. No telemetry is written to disk.

Setup: py -m pip install playwright
       py -m playwright install chromium
Run:   py desktop_widget.py
Log in to the logger in the browser window, then click Start monitoring.
"""
import json
import queue
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from playwright.sync_api import sync_playwright

LOGGER_IP = "192.168.1.93"
POLL_SECONDS = 5
PROFILE = str(Path(__file__).resolve().parent / ".deye_browser_profile")


def poller(messages, start_event, stop_event):
    try:
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(PROFILE, headless=False)
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(f"http://{LOGGER_IP}/index.html", wait_until="domcontentloaded")
            messages.put(("status", "Log in in Chromium, then click Start monitoring"))
            while not start_event.wait(0.2):
                if stop_event.is_set():
                    context.close()
                    return
            while not stop_event.is_set():
                try:
                    data = page.evaluate("""() => new Promise((resolve, reject) => {
                        if (typeof request !== 'function' || typeof handleResText !== 'function') {
                            reject(new Error('Logger status page not ready'));
                            return;
                        }
                        const timer = setTimeout(() => reject(new Error('Request timeout')), 10000);
                        request({
                            url: 'status.cgi?t=' + Math.random(),
                            retryCount: 0,
                            keyResyncRetryCount: 0,
                            successCb: response => {
                                clearTimeout(timer);
                                try {
                                    const result = handleResText(response);
                                    resolve({
                                        time: result.inverter?.time ?? '',
                                        info: Object.fromEntries((result.inverter?.info || []).map(x => [x.key, x.value]))
                                    });
                                } catch(e) { reject(e); }
                            },
                            failedCb: () => { clearTimeout(timer); reject(new Error('Request failed')); }
                        });
                    })""")
                    messages.put(("data", data))
                except Exception as exc:
                    messages.put(("status", f"Read failed: {str(exc)[:90]}"))
                stop_event.wait(POLL_SECONDS)
            context.close()
    except Exception as exc:
        messages.put(("status", f"Browser error: {str(exc)[:90]}"))


def main():
    root = tk.Tk()
    root.title("DEYEapp · Live")
    root.geometry("300x255")
    root.resizable(False, False)
    root.attributes("-topmost", True)
    root.configure(bg="#14202b")

    messages = queue.Queue()
    start_event = threading.Event()
    stop_event = threading.Event()

    title = tk.Label(root, text="DEYEapp  •  LOCAL", fg="#a9c5d5", bg="#14202b",
                     font=("Segoe UI", 11, "bold"))
    title.pack(pady=(15, 4))
    power = tk.StringVar(value="— W")
    tk.Label(root, textvariable=power, fg="#ffffff", bg="#14202b",
             font=("Segoe UI", 30, "bold")).pack()
    tk.Label(root, text="Inverter currentPower (logger)", fg="#9bb4c5",
             bg="#14202b", font=("Segoe UI", 9)).pack()
    details = tk.StringVar(value="Today: —    Total: —")
    tk.Label(root, textvariable=details, fg="#d5e7f0", bg="#14202b",
             font=("Segoe UI", 10)).pack(pady=(14, 2))
    stamp = tk.StringVar(value="Last reading: —")
    tk.Label(root, textvariable=stamp, fg="#9bb4c5", bg="#14202b",
             font=("Segoe UI", 9)).pack()
    status = tk.StringVar(value="Opening logger browser…")
    tk.Label(root, textvariable=status, fg="#8cdda9", bg="#14202b",
             wraplength=275, font=("Segoe UI", 9)).pack(pady=(8, 5))
    start_button = ttk.Button(root, text="Start monitoring", command=lambda: (
        start_event.set(), start_button.configure(state="disabled")))
    start_button.pack()

    def drain():
        try:
            while True:
                kind, payload = messages.get_nowait()
                if kind == "status":
                    status.set(payload)
                else:
                    info = payload["info"]
                    power.set(info.get("currentPower", "— W"))
                    details.set(f"Today: {info.get('yieldToday', '—')}    Total: {info.get('totalYield', '—')}")
                    stamp.set(f"Last reading: {payload.get('time', '—')}")
                    status.set("Connected · updates every 5 seconds")
        except queue.Empty:
            pass
        if not stop_event.is_set():
            root.after(250, drain)

    def close():
        stop_event.set()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", close)
    threading.Thread(target=poller, args=(messages, start_event, stop_event),
                     daemon=True).start()
    root.after(250, drain)
    root.mainloop()


if __name__ == "__main__":
    main()
