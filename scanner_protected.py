
import json
import time
import requests
import urllib3
import random
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import statistics
import threading
from queue import Queue

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

APP_DATA_DIR = Path.home() / "Library" / "Application Support" / "RoScanner"
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = APP_DATA_DIR / "config.json"
# Look for accounts.json in the same folder as the executable
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    ACCOUNTS_FILE = Path(sys.executable).parent / "accounts.json"
else:
    # Running as script
    ACCOUNTS_FILE = Path("accounts.json")
PURCHASE_LOG = APP_DATA_DIR / "purchases.log"
STATISTICS_FILE = APP_DATA_DIR / "statistics.json"

DEFAULT_CONFIG = {
    "scan_interval": 0.1,
    "discount_threshold": 50,
    "max_price": 1000000,
    "min_price": 100,
    "request_timeout": 5,
    "auto_buy_enabled": True,
    "max_pages_per_scan": 100,
    "delay_between_pages": 0.15,
    "purchase_delay": 0.2,
    "max_purchase_attempts": 2,
    "progress_interval": 100,
}

class Colors:
    WHITE = ''
    BRIGHT_RED = ''
    RED = ''
    GREEN = ''
    DARK_GREEN = ''
    GRAY = ''
    DARK_GRAY = ''
    ENDC = ''
    BOLD = ''
    DIM = ''

class ConfigManager:
    @staticmethod
    def load():
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    for key, value in DEFAULT_CONFIG.items():
                        if key not in config:
                            config[key] = value
                    return config
            except:
                pass
        return DEFAULT_CONFIG.copy()
    
    @staticmethod
    def save(config):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

class MarketplaceScanner:
    def __init__(self, config, accounts):
        self.config = config
        self.accounts = accounts
        self.buyer_session = None
        self.scanner_sessions = []
        self.purchased_items = set()
        self.total_scans = 0
        self.total_purchases = 0
        self.start_time = time.time()
        self.lock = threading.Lock()
        self.deal_queue = Queue()
        
    def log(self, message, color=Colors.WHITE):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"{Colors.GRAY}[{timestamp}]{Colors.ENDC} {color}{message}{Colors.ENDC}")
    
    def log_purchase(self, scanner_name, item_name, asset_id, price, rap, discount):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"{timestamp} | Found by: {scanner_name} | {item_name} | ID:{asset_id} | Price:{price}R$ | RAP:{rap}R$ | Discount:{discount:.1f}%\\n"
        with open(PURCHASE_LOG, 'a') as f:
            f.write(log_entry)
    
    def create_session(self, account):
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
        })
        session.cookies.set('.ROBLOSECURITY', account['cookie'], domain='.roblox.com', path='/')
        return session
    
    def get_csrf_token(self, session):
        try:
            response = session.post(
                "https://auth.roblox.com/v2/logout",
                timeout=self.config['request_timeout'],
                verify=False
            )
            if 'x-csrf-token' in response.headers:
                token = response.headers['x-csrf-token']
                session.headers['X-CSRF-TOKEN'] = token
                return token
        except:
            pass
        return None
    
    def authenticate_account(self, account, account_type):
        self.log(f"Authenticating {account_type}: {account['name']}...", Colors.WHITE)
        
        session = self.create_session(account)
        csrf = self.get_csrf_token(session)
        
        if not csrf:
            self.log(f"  Failed to get CSRF token", Colors.RED)
            return None
        
        try:
            auth_url = "https://users.roblox.com/v1/users/authenticated"
            response = session.get(auth_url, timeout=10, verify=False)
            if response.status_code == 200:
                user_data = response.json()
                username = user_data.get('name', 'Unknown')
                user_id = user_data.get('id')
                
                color = Colors.BRIGHT_RED if account_type == "BUYER" else Colors.GREEN
                self.log(f"  {account['name']}: {username} (ID: {user_id})", color)
                
                return {
                    'session': session,
                    'csrf': csrf,
                    'username': username,
                    'user_id': user_id,
                    'account_name': account['name']
                }
            else:
                self.log(f"  Auth failed: {response.status_code}", Colors.RED)
                return None
        except Exception as e:
            self.log(f"  Error: {str(e)}", Colors.RED)
            return None
    
    def setup_sessions(self):
        print(f"\n{Colors.BOLD}{Colors.WHITE}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.WHITE}Magester's Hub - RobloxSniper{Colors.ENDC}")
        print(f"{Colors.GRAY}Created by Magester | AEST{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.WHITE}{'='*70}{Colors.ENDC}\n")
        
        self.log("Setting up BUYER account...", Colors.BRIGHT_RED)
        buyer_data = self.authenticate_account(self.accounts['buyer'], "BUYER")
        if not buyer_data:
            self.log("Failed to authenticate buyer account!", Colors.RED)
            return False
        self.buyer_session = buyer_data
        
        print()
        self.log("Setting up SCANNER accounts...", Colors.WHITE)
        
        for scanner in self.accounts['scanners']:
            scanner_data = self.authenticate_account(scanner, "SCANNER")
            if scanner_data:
                self.scanner_sessions.append(scanner_data)
            time.sleep(0.3)
        
        if not self.scanner_sessions:
            self.log("No scanner accounts authenticated!", Colors.RED)
            return False
        
        print()
        self.log(f"1 Buyer account ready", Colors.BRIGHT_RED)
        self.log(f"{len(self.scanner_sessions)}/5 Scanner accounts ready", Colors.GREEN)
        return True
    
    def scan_marketplace_page(self, scanner_data, cursor=None):
        try:
            url = "https://catalog.roblox.com/v1/search/items/details"
            params = {"Category": "11", "SalesTypeFilter": "2", "Limit": "30"}
            if cursor:
                params["Cursor"] = cursor
            
            response = scanner_data['session'].get(url, params=params, timeout=self.config['request_timeout'], verify=False)
            
            if response.status_code == 429:
                time.sleep(30)
                return [], None
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', []), data.get('nextPageCursor')
            return [], None
        except:
            return [], None
    
    def get_resale_data(self, scanner_data, asset_id):
        try:
            url = f"https://economy.roblox.com/v1/assets/{asset_id}/resale-data"
            response = scanner_data['session'].get(url, timeout=5, verify=False)
            if response.status_code == 200:
                data = response.json()
                return {'lowest_price': data.get('lowestPrice'), 'rap': data.get('recentAveragePrice')}
        except:
            pass
        return None
    
    def get_lowest_reseller(self, asset_id):
        try:
            url = f"https://economy.roblox.com/v1/assets/{asset_id}/resellers"
            response = self.buyer_session['session'].get(url, params={"limit": 1}, timeout=5, verify=False)
            if response.status_code == 200:
                resellers = response.json().get('data', [])
                if resellers:
                    return resellers[0].get('userAssetId'), resellers[0].get('seller', {}).get('id')
        except:
            pass
        return None, None
    
    def attempt_purchase(self, asset_id, user_asset_id, price, seller_id):
        try:
            url = f"https://economy.roblox.com/v1/purchases/products/{user_asset_id}"
            payload = {"expectedCurrency": 1, "expectedPrice": price, "expectedSellerId": seller_id}
            headers = {"Content-Type": "application/json", "X-CSRF-TOKEN": self.buyer_session['csrf']}
            
            response = self.buyer_session['session'].post(url, json=payload, headers=headers, timeout=self.config['request_timeout'], verify=False)
            
            if response.status_code == 403 and 'x-csrf-token' in response.headers:
                self.buyer_session['csrf'] = response.headers['x-csrf-token']
                self.buyer_session['session'].headers['X-CSRF-TOKEN'] = self.buyer_session['csrf']
                time.sleep(0.2)
                response = self.buyer_session['session'].post(url, json=payload, headers=headers, timeout=5, verify=False)
            
            if response.status_code == 200:
                return True, "Success"
            return False, response.text[:100] if response.text else f"Status {response.status_code}"
        except Exception as e:
            return False, str(e)
    
    def process_deal_queue(self):
        while True:
            try:
                deal = self.deal_queue.get(timeout=1)
                if deal is None:
                    break
                
                scanner_data, item, discount, profit, roi, lowest_price, rap = deal
                asset_id = item.get('id')
                name = item.get('name', 'Unknown')
                
                with self.lock:
                    if asset_id in self.purchased_items:
                        continue
                
                self.log(f"DEAL FOUND by {scanner_data['account_name']}: {name[:40]}", Colors.BRIGHT_RED)
                self.log(f"  Price: {lowest_price}R$ | RAP: {rap}R$ | Discount: {discount:.1f}% | Profit: {profit}R$", Colors.WHITE)
                
                if self.config['auto_buy_enabled']:
                    user_asset_id, seller_id = self.get_lowest_reseller(asset_id)
                    if user_asset_id and seller_id:
                        time.sleep(self.config['purchase_delay'])
                        self.log(f"  Buying with {self.buyer_session['username']}...", Colors.BRIGHT_RED)
                        success, message = self.attempt_purchase(asset_id, user_asset_id, lowest_price, seller_id)
                        
                        if success:
                            with self.lock:
                                self.log(f"  PURCHASED! (Found by {scanner_data['account_name']})", Colors.GREEN)
                                self.purchased_items.add(asset_id)
                                self.total_purchases += 1
                                self.log_purchase(scanner_data['account_name'], name, asset_id, lowest_price, rap, discount)
                        else:
                            self.log(f"  Purchase failed: {message[:50]}", Colors.RED)
                    else:
                        self.log(f"  Could not get listing", Colors.RED)
            except:
                continue
    
    def process_item(self, scanner_data, item):
        try:
            asset_id = item.get('id')
            with self.lock:
                if asset_id in self.purchased_items:
                    return
            
            resale_data = self.get_resale_data(scanner_data, asset_id)
            if not resale_data:
                return
            
            lowest_price = resale_data.get('lowest_price')
            rap = resale_data.get('rap')
            
            if not lowest_price or not rap or lowest_price == 0 or rap == 0:
                return
            if lowest_price > self.config['max_price'] or lowest_price < self.config['min_price']:
                return
            
            discount = ((rap - lowest_price) / rap) * 100
            if discount >= self.config['discount_threshold']:
                profit = rap - lowest_price
                roi = (profit / lowest_price) * 100
                self.deal_queue.put((scanner_data, item, discount, profit, roi, lowest_price, rap))
        except:
            pass
    
    def scan_with_scanner(self, scanner_data, items_counter):
        cursor = None
        local_items = 0
        
        for page in range(self.config['max_pages_per_scan']):
            items, next_cursor = self.scan_marketplace_page(scanner_data, cursor)
            if not items:
                break
            
            local_items += len(items)
            with self.lock:
                items_counter['total'] += len(items)
                if items_counter['total'] % self.config['progress_interval'] == 0:
                    self.log(f"Progress: {items_counter['total']} items scanned", Colors.GRAY)
            
            for item in items:
                if item.get('itemType') != 'Bundle':
                    self.process_item(scanner_data, item)
            
            if not next_cursor:
                break
            cursor = next_cursor
            time.sleep(self.config['delay_between_pages'])
        
        with self.lock:
            self.log(f"{scanner_data['account_name']}: Completed ({local_items} items)", Colors.DARK_GREEN)
    
    def run(self):
        if not self.setup_sessions():
            self.log("Failed to set up accounts", Colors.RED)
            return
        
        print()
        self.log(f"Configuration:", Colors.WHITE)
        self.log(f"  Buyer: {self.buyer_session['username']}", Colors.BRIGHT_RED)
        self.log(f"  Scanners: {len(self.scanner_sessions)} accounts", Colors.GREEN)
        self.log(f"  Discount Threshold: {self.config['discount_threshold']}%", Colors.WHITE)
        self.log(f"  Price Range: {self.config['min_price']:,}R$ - {self.config['max_price']:,}R$", Colors.WHITE)
        self.log(f"  Pages per Scanner: {self.config['max_pages_per_scan']}", Colors.WHITE)
        self.log(f"  Auto-Buy: {'ENABLED' if self.config['auto_buy_enabled'] else 'DISABLED'}", 
                Colors.GREEN if self.config['auto_buy_enabled'] else Colors.RED)
        
        print()
        self.log("Starting parallel marketplace scan...", Colors.GREEN)
        self.log("Press Ctrl+C to stop gracefully", Colors.GRAY)
        print()
        
        scan_cycle = 0
        try:
            while True:
                scan_cycle += 1
                cycle_start = time.time()
                
                print(f"{Colors.BOLD}{Colors.WHITE}{'='*70}{Colors.ENDC}")
                self.log(f"Scan Cycle #{scan_cycle} - {datetime.now().strftime('%H:%M:%S')}", Colors.BOLD + Colors.WHITE)
                print(f"{Colors.BOLD}{Colors.WHITE}{'='*70}{Colors.ENDC}")
                
                items_counter = {'total': 0}
                purchase_thread = threading.Thread(target=self.process_deal_queue, daemon=True)
                purchase_thread.start()
                
                threads = []
                for scanner_data in self.scanner_sessions:
                    thread = threading.Thread(target=self.scan_with_scanner, args=(scanner_data, items_counter), daemon=True)
                    thread.start()
                    threads.append(thread)
                
                for thread in threads:
                    thread.join()
                
                self.deal_queue.put(None)
                purchase_thread.join(timeout=5)
                
                cycle_time = time.time() - cycle_start
                runtime = time.time() - self.start_time
                
                print()
                self.log(f"Cycle Complete:", Colors.GREEN)
                self.log(f"  Items Checked: {items_counter['total']}", Colors.WHITE)
                self.log(f"  Cycle Time: {cycle_time:.1f}s", Colors.WHITE)
                self.log(f"  Total Purchases: {self.total_purchases}", Colors.GREEN)
                self.log(f"  Runtime: {runtime/60:.1f} minutes", Colors.WHITE)
                print()
                self.log(f"Waiting {self.config['scan_interval']}s before next cycle...", Colors.GRAY)
                time.sleep(self.config['scan_interval'])
        except KeyboardInterrupt:
            print()
            self.log("Stopping scanner gracefully...", Colors.BRIGHT_RED)
            runtime = time.time() - self.start_time
            print()
            self.log(f"Final Statistics:", Colors.WHITE)
            self.log(f"  Total Runtime: {runtime/60:.1f} minutes", Colors.WHITE)
            self.log(f"  Total Purchases: {self.total_purchases}", Colors.GREEN)
            self.log(f"  Buyer Account: {self.buyer_session['username']}", Colors.BRIGHT_RED)
            print()
            self.log("Scanner stopped successfully", Colors.GREEN)

def main():
    print(f"\n{Colors.BOLD}{Colors.WHITE}Magester's Hub | Roblox Sniper{Colors.ENDC}")
    print(f"{Colors.GRAY}Thank You For Purchasing 5 Mil{Colors.ENDC}")
    print(f"{Colors.WHITE}Roblox Sniper | Magester's Hub{Colors.ENDC}\n")
    
    if not ACCOUNTS_FILE.exists():
        print(f"{Colors.RED}ERROR: accounts.json file not found!{Colors.ENDC}")
        print(f"{Colors.WHITE}Please create accounts.json with your account cookies.{Colors.ENDC}")
        sys.exit(1)
    
    try:
        with open(ACCOUNTS_FILE, 'r') as f:
            accounts = json.load(f)
    except Exception as e:
        print(f"{Colors.RED}ERROR: Failed to load accounts.json: {e}{Colors.ENDC}")
        sys.exit(1)
    
    config = ConfigManager.load()
    
    if not CONFIG_FILE.exists():
        print(f"{Colors.WHITE}First time setup:{Colors.ENDC}\\n")
        discount = input(f"Minimum discount % to buy [50]: ").strip()
        config['discount_threshold'] = int(discount) if discount else 50
        max_price = input(f"Maximum price per item [1000000]: ").strip()
        config['max_price'] = int(max_price) if max_price else 1000000
        min_price = input(f"Minimum price per item [100]: ").strip()
        config['min_price'] = int(min_price) if min_price else 100
        auto_buy = input(f"Enable auto-buy? (y/n) [y]: ").strip().lower()
        config['auto_buy_enabled'] = auto_buy != 'n'
        ConfigManager.save(config)
        print()
    
    scanner = MarketplaceScanner(config, accounts)
    scanner.run()

if __name__ == "__main__":
    main()