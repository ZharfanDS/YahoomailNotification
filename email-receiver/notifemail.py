import imaplib
import email
import time
import requests
from email.header import decode_header

print(" === PROGRAM NOTIF EMAIL DINYALKAN! ===")

# Fungsi untuk membaca konfigurasi dari file data.txt
def load_config(file_path):
    config = {}
    with open(file_path, "r") as file:
        for line in file:
            key, value = line.strip().split("=")
            config[key] = value
    return config

# Load konfigurasi dari data.txt
config = load_config(r"email-receiver\data.txt")

# Ambil variabel dari konfigurasi
email_user = config.get("email_user")
email_pass = config.get("email_pass")
telegram_bot_token = config.get("telegram_bot_token")
telegram_chat_id = config.get("telegram_chat_id")

# Fungsi untuk mengirimkan pesan ke Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": telegram_chat_id,
        "text": message
    }
    response = requests.post(url, data=payload)
    return response.json()

# Fungsi untuk menghubungkan ke server IMAP Yahoo dan memeriksa email
def check_yahoo_email():
    
    # Menghubungkan ke server Yahoo IMAP
    mail = imaplib.IMAP4_SSL("imap.mail.yahoo.com")

    # Login ke akun
    mail.login(email_user, email_pass)

    # Pilih folder inbox
    mail.select("inbox")

    # Cari email yang belum dibaca (UNSEEN)
    status, messages = mail.search(None, 'UNSEEN')

    if status == "OK":
        # Jika ada email baru, ambil email terbaru
        if messages[0]:
            # Ambil ID email terbaru
            latest_email_id = messages[0].split()[-1]
            
            # Fetch email berdasarkan ID
            status, msg_data = mail.fetch(latest_email_id, "(RFC822)")

            if status == "OK":
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        # Parsing email
                        msg = email.message_from_bytes(response_part[1])

                        # Dekode subject
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")

                        # Ambil pengirim
                        sender = msg.get("From")

                        # Menampilkan Subject dan pengirim
                        print("=== NEW EMAIL ===")
                        print(f"Subject: {subject}")
                        print(f"From: {sender}")

                        # Mengecek dan menampilkan isi email (hanya plain text)
                        email_body = ""
                        if msg.is_multipart():
                            # Jika email multipart, kita perlu memeriksa bagian-bagian email
                            for part in msg.walk():
                                # Ambil tipe konten email
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))

                                # Jika bagian tersebut adalah text/plain
                                if "attachment" not in content_disposition and content_type == "text/plain":
                                    email_body = part.get_payload(decode=True).decode()
                                    print(f"Isi :\n{email_body}")
                                    print(f"====================")
                        else:
                            # Jika email hanya memiliki satu bagian (misalnya email biasa tanpa lampiran)
                            content_type = msg.get_content_type()
                            if content_type == "text/plain":
                                email_body = msg.get_payload(decode=True).decode()
                                print(f"Isi :\n{email_body}")
                                print(f"====================")

                        # Kirimkan informasi email ke Telegram
                        message = f"Subject: {subject}\nFrom: {sender}\n\n{email_body}"
                        send_telegram_message(message)

    else:
        print("Tidak ada email baru.")

    # Logout dari server
    mail.logout()

# Loop untuk memeriksa email baru setiap 10 detik
while True:
    check_yahoo_email()
    # Tunggu 10 detik sebelum memeriksa lagi
    time.sleep(10)
