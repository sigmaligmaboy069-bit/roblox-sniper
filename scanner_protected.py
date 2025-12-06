#!/usr/bin/env python3
"""
RobloxSniper - Licensed Version with Cherry Picker Mode
- Full Market Scan: Scans entire marketplace (3-5M items/day)
- Cherry Picker: Monitor specific items by asset ID
- License key validation
- HWID locking
- Auto-update system

From Magester's Market
"""

import json
import time
import requests
import urllib3
import sys
import uuid
import platform
import hashlib
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
LICENSE_FILE = APP_DATA_DIR / "license.dat"
ACCOUNTS_FILE = Path("accounts.json")
PURCHASE_LOG = APP_DATA_DIR / "purchases.log"
STATISTICS_FILE = APP_DATA_DIR / "statistics.json"

# Version info for auto-update
VERSION = "1.3.1"
UPDATE_CHECK_URL = "https://raw.githubusercontent.com/sigmaligmaboy069-bit/roblox-sniper/main/version.json"
LICENSE_SERVER_URL = "https://robloxlimscannermh.pythonanywhere.com/api/validate"

# Cherry Picker Access Code
CHERRY_PICKER_CODE = "865UB1Magester1BU568"

# Valid license keys embedded in program
INITIAL_KEYS = {
    # Monthly Keys (30 days)
    "M-7K2P-9X4L-H6TY-3QW8": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None}, #used
    "M-5N8M-2R7V-K9YH-4PT6": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None}, #used
    "M-3Q9L-6X2N-8WR4-7TH5": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None}, #used
    "M-8Y4H-5L9P-2KX6-3NR7": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-2W7K-4N8X-9PL5-6YH3": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-6R3Y-8K2H-4NX7-9PL5": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-9L4X-7P2K-5NH8-3YR6": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-4K8N-2Y7P-6XL9-5RH3": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-7X2P-9K4L-3NH8-6YR5": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-5N9L-8R3K-2YH7-4PX6": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-3P6K-7L2Y-9RH4-8NX5": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-8H4Y-2N7K-5XL9-3RP6": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-2R9P-6K3Y-8LH4-7NX5": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-6Y3L-9H2K-4RP8-5NX7": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-9K7X-4P2L-8NH5-3YR6": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-4L8R-2K7N-6YP9-5HX3": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-7P2Y-9L4K-3RH8-6NX5": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-5X9K-8N3P-2LH7-4YR6": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-3N6P-7Y2K-9LH4-8RX5": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-8R4L-2P7Y-5KH9-3NX6": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-2K9Y-6L3P-8RH4-7NX5": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-6P3K-9Y2L-4NH8-5RX7": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-9L7R-4K2P-8YH5-3NX6": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-4Y8P-2L7K-6RH9-5NX3": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-7K2R-9P4Y-3LH8-6NX5": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-5R9L-8K3Y-2PH7-4NX6": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-3P6Y-7R2L-9KH4-8NX5": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-8L4K-2R7P-5YH9-3NX6": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-2Y9K-6P3R-8LH4-7NX5": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-6K3P-9L2Y-4RH8-5NX7": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-9R7L-4Y2P-8KH5-3NX6": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-4P8L-2Y7R-6KH9-5NX3": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-7Y2K-9R4P-3LH8-6NX5": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-5L9R-8P3K-2YH7-4NX6": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-3K6R-7P2Y-9LH4-8NX5": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-8Y4P-2L7R-5KH9-3NX6": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-2R9L-6Y3P-8KH4-7NX5": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-6P3Y-9K2R-4LH8-5NX7": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-9K7P-4R2L-8YH5-3NX6": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-4L8Y-2K7P-6RH9-5NX3": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-7R2P-9K4Y-3LH8-6NX5": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-5Y9P-8R3L-2KH7-4NX6": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-3P6L-7Y2R-9KH4-8NX5": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-8K4R-2P7Y-5LH9-3NX6": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-2Y9R-6P3K-8LH4-7NX5": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-6R3L-9P2Y-4KH8-5NX7": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-9P7K-4Y2R-8LH5-3NX6": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-4R8P-2Y7K-6LH9-5NX3": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-7L2Y-9P4R-3KH8-6NX5": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-5K9Y-8L3R-2PH7-4NX6": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    
    # Lifetime Keys (Permanent)
    "L-9X4M-7K2P-5NH8-3YR6": {"type": "lifetime", "used": False, "hwid": None, "activated_date": None}, #used
    "L-4P8L-2Y7K-6RH9-5NX3": {"type": "lifetime", "used": False, "hwid": None, "activated_date": None},
    "L-7K2R-9P4Y-3LH8-6NX5": {"type": "lifetime", "used": False, "hwid": None, "activated_date": None},
    "L-5N9L-8R3K-2YH7-4PX6": {"type": "lifetime", "used": False, "hwid": None, "activated_date": None},
    "L-3P6Y-7R2L-9KH4-8NX5": {"type": "lifetime", "used": False, "hwid": None, "activated_date": None},
    "L-8Y4P-2L7R-5KH9-3NX6": {"type": "lifetime", "used": False, "hwid": None, "activated_date": None},
    "L-2R9L-6Y3P-8KH4-7NX5": {"type": "lifetime", "used": False, "hwid": None, "activated_date": None},
    "L-6P3Y-9K2R-4LH8-5NX7": {"type": "lifetime", "used": False, "hwid": None, "activated_date": None},
    "L-9K7P-4R2L-8YH5-3NX6": {"type": "lifetime", "used": False, "hwid": None, "activated_date": None},
    "L-4L8Y-2K7P-6RH9-5NX3": {"type": "lifetime", "used": False, "hwid": None, "activated_date": None},
    "L-7R2P-9K4Y-3LH8-6NX5": {"type": "lifetime", "used": False, "hwid": None, "activated_date": None},
    "L-5Y9P-8R3L-2KH7-4NX6": {"type": "lifetime", "used": False, "hwid": None, "activated_date": None},
    "L-3P6L-7Y2R-9KH4-8NX5": {"type": "lifetime", "used": False, "hwid": None, "activated_date": None},
    "L-8K4R-2P7Y-5LH9-3NX6": {"type": "lifetime", "used": False, "hwid": None, "activated_date": None},
    "L-2Y9R-6P3K-8LH4-7NX5": {"type": "lifetime", "used": False, "hwid": None, "activated_date": None},
    "L-6R3L-9P2Y-4KH8-5NX7": {"type": "lifetime", "used": False, "hwid": None, "activated_date": None},
    "L-9P7K-4Y2R-8LH5-3NX6": {"type": "lifetime", "used": False, "hwid": None, "activated_date": None},
    "L-4R8P-2Y7K-6LH9-5NX3": {"type": "lifetime", "used": False, "hwid": None, "activated_date": None},
    "L-7L2Y-9P4R-3KH8-6NX5": {"type": "lifetime", "used": False, "hwid": None, "activated_date": None},
    "L-5K9Y-8L3R-2PH7-4NX6": {"type": "lifetime", "used": False, "hwid": None, "activated_date": None},
}



CONFIG_FILE = APP_DATA_DIR / "config.json"
LICENSE_FILE = APP_DATA_DIR / "license.dat"
ACCOUNTS_FILE = Path("accounts.json")
PURCHASE_LOG = APP_DATA_DIR / "purchases.log"
STATISTICS_FILE = APP_DATA_DIR / "statistics.json"

# Improved config with faster scanning
DEFAULT_CONFIG = {
    "scan_interval": 0.05,
    "discount_threshold": 50,
    "max_price": 1000000,
    "min_price": 100,
    "request_timeout": 5,  # Increased timeout to avoid failed requests
    "auto_buy_enabled": True,
    "max_pages_per_scan": 250,
    "delay_between_pages": 0.05,  # Reduced from 0.1 to 0.05
    "purchase_delay": 0.15,
    "max_purchase_attempts": 3,
    "progress_interval": 250,
}

class Colors:
    WHITE = ''
    BRIGHT_RED = ''
    RED = ''
    GREEN = ''
    DARK_GREEN = ''
    GRAY = ''
    ENDC = ''
    BOLD = ''

def get_hwid():
    """Get unique hardware ID for this computer"""
    system = platform.system()
    machine = platform.machine()
    processor = platform.processor()
    node = platform.node()
    
    hwid_string = f"{system}-{machine}-{processor}-{node}"
    hwid_hash = hashlib.sha256(hwid_string.encode()).hexdigest()
    return hwid_hash[:32]


class LicenseManager:
    def __init__(self):
        self.license_file = LICENSE_FILE
        self.hwid = get_hwid()
        
    def save_license(self, key, license_type):
        """Save license key locally"""
        data = {
            "key": key,
            "type": license_type,
            "hwid": self.hwid,
            "activated_at": datetime.now().isoformat()
        }
        with open(self.license_file, 'w') as f:
            json.dump(data, f)
    
    def load_license(self):
        """Load saved license"""
        if self.license_file.exists():
            try:
                with open(self.license_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return None
    
    def validate_license_online(self, key):
        """Validate license with online server"""
        try:
            response = requests.post(
                LICENSE_SERVER_URL,
                json={"key": key, "hwid": self.hwid},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('valid'):
                    return True, data.get('type', 'Unknown'), data.get('message', '')
         
                else:
                    return False, None, data.get('message', 'Invalid key')
            else:
                return False, None, "Server error"
       

        except Exception as e:
            return False, None, f"Cannot reach license server: {str(e)}"
    
    def check_license(self):
        """Check if valid license exists"""
        saved = self.load_license()
        
        if not saved:
            return False, "No license found"
        
        if saved.get('hwid') != self.hwid:
            return False, "License locked to different computer"
        
        key = saved['key']
        valid, license_type, message = self.validate_license_online(key)
        
        if not valid:
            return False, message
        
        return True, license_type


def check_for_updates():
    """Check for new version"""
    try:
        response = requests.get(UPDATE_CHECK_URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            latest_version = data.get('version')
            if latest_version and latest_version != VERSION:
                print(f"\nNew version available: {latest_version}")
                print(f"Current version: {VERSION}")
                print(f"Download from: Magester's Market\n")
                return True
    except:
        pass
    return False


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
    def __init__(self, config, accounts, cherry_pick_mode=False, cherry_pick_items=None):
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
        self.cherry_pick_mode = cherry_pick_mode
        self.cherry_pick_items = cherry_pick_items or set()
    
    def log(self, message, color=''):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {message}")
    
    def log_purchase(self, scanner_name, item_name, asset_id, price, rap, discount):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"{timestamp} | Found by: {scanner_name} | {item_name} | ID:{asset_id} | Price:{price}R$ | RAP:{rap}R$ | Discount:{discount:.1f}%\n"
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
            response = session.post("https://auth.roblox.com/v2/logout", timeout=5, verify=False)
            if 'x-csrf-token' in response.headers:
                token = response.headers['x-csrf-token']
                session.headers['X-CSRF-TOKEN'] = token
                return token
        except:
            pass
        return None
    
    def authenticate_account(self, account, account_type):
        self.log(f"Authenticating {account_type}: {account['name']}...")
        
        session = self.create_session(account)
        csrf = self.get_csrf_token(session)
        
        if not csrf:
            self.log(f"  Failed to get CSRF token")
            return None
        
        try:
            response = session.get("https://users.roblox.com/v1/users/authenticated", timeout=10, verify=False)
            if response.status_code == 200:
                user_data = response.json()
                username = user_data.get('name', 'Unknown')
                user_id = user_data.get('id')
                
                self.log(f"  {account['name']}: {username} (ID: {user_id})")
                
                return {
                    'session': session,
                    'csrf': csrf,
                    'username': username,
                    'user_id': user_id,
                    'account_name': account['name']
                }
        except:
            pass
        return None
    
    def setup_sessions(self):
        print("\n" + "="*70)
        print("Magester's Market - RobloxSniper v" + VERSION)
        print("Licensed Version - " + ("Cherry Picker Mode" if self.cherry_pick_mode else "Full Market Mode"))
        print("="*70 + "\n")
        
        self.log("Setting up BUYER account...")
        buyer_data = self.authenticate_account(self.accounts['buyer'], "BUYER")
        if not buyer_data:
            self.log("Failed to authenticate buyer account!")
            return False
        self.buyer_session = buyer_data
        
        print()
        self.log("Setting up SCANNER accounts...")
        
        for scanner in self.accounts['scanners']:
            scanner_data = self.authenticate_account(scanner, "SCANNER")
            if scanner_data:
                self.scanner_sessions.append(scanner_data)
            time.sleep(0.2)
        
        if not self.scanner_sessions:
            self.log("No scanner accounts authenticated!")
            return False
        
        print()
        self.log(f"1 Buyer account ready")
        self.log(f"{len(self.scanner_sessions)}/{len(self.accounts['scanners'])} Scanner accounts ready")
        return True
    
    def scan_marketplace_page(self, scanner_data, cursor=None):
        try:
            url = "https://catalog.roblox.com/v1/search/items/details"
            params = {
                "Category": "11",
                "SalesTypeFilter": "2",
                "Limit": "30",
                "CreatorName": "Roblox",
                "taxonomy": "tZsUsd2BqGViQrJ9Vs3Wah"
            }
            if cursor:
                params["Cursor"] = cursor
            
            response = scanner_data['session'].get(url, params=params, timeout=self.config['request_timeout'], verify=False)
            
            if response.status_code == 429:
                time.sleep(15)
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
            response = scanner_data['session'].get(url, timeout=3, verify=False)
            if response.status_code == 200:
                data = response.json()
                return {'lowest_price': data.get('lowestPrice'), 'rap': data.get('recentAveragePrice')}
        except:
            pass
        return None
    
    def get_item_details(self, scanner_data, asset_id):
        """Get item name and details from asset ID - returns None if not limited/doesn't exist"""
        try:
            url = f"https://catalog.roblox.com/v1/catalog/items/details"
            payload = {"items": [{"itemType": "Asset", "id": asset_id}]}
            
            # Add headers to ensure proper request
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            response = scanner_data['session'].post(url, json=payload, headers=headers, timeout=5, verify=False)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('data', [])
                if items and len(items) > 0:
                    item = items[0]
                    item_name = item.get('name', 'Unknown')
                    
                    # Debug: print the full item data to see structure
                    # print(f"DEBUG: {json.dumps(item, indent=2)}")
                    
                    # Check multiple ways if item is limited
                    is_limited = False
                    
                    # Method 1: Check itemRestrictions
                    item_restrictions = item.get('itemRestrictions', [])
                    if 'Limited' in item_restrictions or 'LimitedUnique' in item_restrictions:
                        is_limited = True
                    
                    # Method 2: Check if lowestPrice exists (only limiteds have resale)
                    if item.get('lowestPrice') is not None:
                        is_limited = True
                    
                    # Method 3: Check priceStatus
                    price_status = item.get('priceStatus', '')
                    if price_status in ['Limited', 'LimitedUnique']:
                        is_limited = True
                    
                    # Method 4: Check if it has unitsAvailableForConsumption (U limiteds)
                    if item.get('unitsAvailableForConsumption') is not None:
                        is_limited = True
                    
                    if is_limited:
                        return item
                    else:
                        # Item exists but not limited
                        return {'error': 'not_limited', 'name': item_name}
                
                # Empty response means item doesn't exist
                return {'error': 'not_exist'}
                
            elif response.status_code == 429:
                # Rate limited, wait and retry once
                time.sleep(2)
                response = scanner_data['session'].post(url, json=payload, headers=headers, timeout=5, verify=False)
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('data', [])
                    if items and len(items) > 0:
                        item = items[0]
                        item_name = item.get('name', 'Unknown')
                        
                        # Same checks as above
                        is_limited = False
                        item_restrictions = item.get('itemRestrictions', [])
                        if 'Limited' in item_restrictions or 'LimitedUnique' in item_restrictions:
                            is_limited = True
                        if item.get('lowestPrice') is not None:
                            is_limited = True
                        price_status = item.get('priceStatus', '')
                        if price_status in ['Limited', 'LimitedUnique']:
                            is_limited = True
                        if item.get('unitsAvailableForConsumption') is not None:
                            is_limited = True
                        
                        if is_limited:
                            return item
                        else:
                            return {'error': 'not_limited', 'name': item_name}
                    return {'error': 'not_exist'}
            
            # API error
            print(f"  ⚠️ API returned status code: {response.status_code}")
            return {'error': 'api_error', 'status': response.status_code}
            
        except Exception as e:
            print(f"  ⚠️ Exception: {str(e)}")
            return {'error': 'exception', 'message': str(e)}
    
    def get_lowest_reseller(self, asset_id):
        try:
            url = f"https://economy.roblox.com/v1/assets/{asset_id}/resellers"
            response = self.buyer_session['session'].get(url, params={"limit": 1}, timeout=3, verify=False)
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
            
            response = self.buyer_session['session'].post(url, json=payload, headers=headers, timeout=5, verify=False)
            
            if response.status_code == 403 and 'x-csrf-token' in response.headers:
                self.buyer_session['csrf'] = response.headers['x-csrf-token']
                self.buyer_session['session'].headers['X-CSRF-TOKEN'] = self.buyer_session['csrf']
                headers['X-CSRF-TOKEN'] = self.buyer_session['csrf']
                time.sleep(0.2)
                response = self.buyer_session['session'].post(url, json=payload, headers=headers, timeout=5, verify=False)
            
            if response.status_code == 200:
                return True, "Success"
            
            if response.status_code in [403, 429]:
                time.sleep(0.3)
                response = self.buyer_session['session'].post(url, json=payload, headers=headers, timeout=5, verify=False)
                if response.status_code == 200:
                    return True, "Success after confirmation"
            
            try:
                error_data = response.json()
                error_msg = error_data.get('message', '') or error_data.get('error', '')
                if 'InsufficientFunds' in str(error_data):
                    return False, "Insufficient Robux"
                if 'AlreadyOwned' in str(error_data):
                    return False, "Already owned"
                if 'PriceChanged' in str(error_data):
                    return False, "Price changed"
                if error_msg:
                    return False, error_msg[:50]
            except:
                pass
            
            return False, f"Status {response.status_code}"
        except Exception as e:
            return False, str(e)[:50]
    
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
                
                self.log(f"DEAL FOUND by {scanner_data['account_name']}: {name[:40]}")
                self.log(f"  Price: {lowest_price}R$ | RAP: {rap}R$ | Discount: {discount:.1f}% | Profit: {profit}R$")
                
                if self.config['auto_buy_enabled']:
                    user_asset_id, seller_id = self.get_lowest_reseller(asset_id)
                    if user_asset_id and seller_id:
                        time.sleep(self.config['purchase_delay'])
                        self.log(f"  Buying with {self.buyer_session['username']}...")
                        success, message = self.attempt_purchase(asset_id, user_asset_id, lowest_price, seller_id)
                        
                        if success:
                            with self.lock:
                                self.log(f"  PURCHASED! (Found by {scanner_data['account_name']})")
                                self.purchased_items.add(asset_id)
                                self.total_purchases += 1
                                self.log_purchase(scanner_data['account_name'], name, asset_id, lowest_price, rap, discount)
                        else:
                            self.log(f"  Purchase failed: {message}")
                    else:
                        self.log(f"  Could not get listing")
            except:
                continue
    
    def process_item(self, scanner_data, item):
        try:
            asset_id = item.get('id')
            name = item.get('name', 'Unknown Item')
            
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
        if self.cherry_pick_mode:
            # Cherry picker mode - check specific items only
            local_items = 0
            for asset_id in self.cherry_pick_items:
                try:
                    with self.lock:
                        items_counter['total'] += 1
                        local_items += 1
                        if items_counter['total'] % 10 == 0:
                            self.log(f"Progress: {items_counter['total']} cherry pick checks")
                    
                    # Get item details for name and validation
                    item_details = self.get_item_details(scanner_data, asset_id)
                    if item_details:
                        if 'error' in item_details:
                            # Skip this item, it was already validated during input
                            continue
                        item = item_details
                    else:
                        continue
                    
                    # Process the valid limited item
                    self.process_item(scanner_data, item)
                    
                    time.sleep(0.2)
                except:
                    pass
            
            with self.lock:
                self.log(f"{scanner_data['account_name']}: Checked {local_items} cherry pick items")
        
        else:
            # Full market mode - original logic
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
                        self.log(f"Progress: {items_counter['total']} items scanned")
                
                for item in items:
                    if item.get('itemType') != 'Bundle':
                        self.process_item(scanner_data, item)
                
                if not next_cursor:
                    break
                cursor = next_cursor
                time.sleep(self.config['delay_between_pages'])
            
            with self.lock:
                self.log(f"{scanner_data['account_name']}: Completed ({local_items} items)")
    
    def run(self):
        if not self.setup_sessions():
            self.log("Failed to set up accounts")
            return
        
        print()
        self.log(f"Configuration:")
        self.log(f"  Buyer: {self.buyer_session['username']}")
        self.log(f"  Scanners: {len(self.scanner_sessions)} accounts")
        self.log(f"  Mode: {'Cherry Picker' if self.cherry_pick_mode else 'Full Market (Roblox-Created Items)'}")
        if self.cherry_pick_mode:
            self.log(f"  Monitoring: {len(self.cherry_pick_items)} specific items")
        else:
            self.log(f"  Filter: Roblox-created items with taxonomy tZsUsd2BqGViQrJ9Vs3Wah")
        self.log(f"  Discount Threshold: {self.config['discount_threshold']}%")
        self.log(f"  Price Range: {self.config['min_price']:,}R$ - {self.config['max_price']:,}R$")
        if not self.cherry_pick_mode:
            self.log(f"  Pages per Scanner: {self.config['max_pages_per_scan']}")
        self.log(f"  Auto-Buy: {'ENABLED' if self.config['auto_buy_enabled'] else 'DISABLED'}")
        
        print()
        self.log("Starting marketplace scan...")
        self.log("Press Ctrl+C to stop gracefully")
        print()
        
        scan_cycle = 0
        try:
            while True:
                scan_cycle += 1
                cycle_start = time.time()
                
                print("="*70)
                self.log(f"Scan Cycle #{scan_cycle} - {datetime.now().strftime('%H:%M:%S')}")
                print("="*70)
                
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
                self.log(f"Cycle Complete:")
                self.log(f"  Items Checked: {items_counter['total']}")
                self.log(f"  Cycle Time: {cycle_time:.1f}s")
                self.log(f"  Total Purchases: {self.total_purchases}")
                self.log(f"  Runtime: {runtime/60:.1f} minutes")
                print()
                
                time.sleep(self.config['scan_interval'])
                
        except KeyboardInterrupt:
            print()
            self.log("Stopping scanner gracefully...")
            runtime = time.time() - self.start_time
            print()
            self.log(f"Final Statistics:")
            self.log(f"  Total Runtime: {runtime/60:.1f} minutes")
            self.log(f"  Total Purchases: {self.total_purchases}")
            self.log(f"  Buyer Account: {self.buyer_session['username']}")
            print()
            self.log("Scanner stopped successfully")

def main():
    print("\n" + "="*70)
    print("Magester's Market | Roblox Sniper v" + VERSION)
    print("Licensed Version")
    print("="*70 + "\n")
    
    # Check for updates
    check_for_updates()
    
    # License check
    license_mgr = LicenseManager()
    valid, license_type = license_mgr.check_license()
    
    if not valid:
        print(f"License Error: {license_type}\n")
        print("Please enter your license key:")
        print("(Format: M-XXXX-XXXX-XXXX-XXXX or L-XXXX-XXXX-XXXX-XXXX)")
        key = input("\nLicense Key: ").strip().upper()
        
        print("\nValidating with license server...")
        valid, l_type, message = license_mgr.validate_license_online(key)
        if not valid:
            print(f"\nActivation Failed: {message}")
            print("\nPossible reasons:")
            print("  - Key is invalid or doesn't exist")
            print("  - Key has already been used on another computer")
            print("  - Cannot reach license server (check internet)")
            print("\nContact Magester's Market for support")
            sys.exit(1)
        
        license_mgr.save_license(key, l_type)
        print(f"\nLicense activated successfully!")
        print(f"Type: {l_type}")
        print(f"Hardware ID: {license_mgr.hwid}")
        print(f"Message: {message}")
        print()
    else:
        print(f"License: {license_type} - Active")
        print(f"HWID: {license_mgr.hwid}\n")
    
    # Load accounts
    if not ACCOUNTS_FILE.exists():
        print("ERROR: accounts.json file not found!")
        print("Please create accounts.json with your account cookies.")
        sys.exit(1)
    
    try:
        with open(ACCOUNTS_FILE, 'r') as f:
            accounts = json.load(f)
    except Exception as e:
        print(f"ERROR: Failed to load accounts.json: {e}")
        sys.exit(1)
    
    # Scanning mode selection
    print("="*70)
    print("SCANNING MODE SELECTION")
    print("="*70 + "\n")
    print("Choose scanning mode:")
    print("  1. Full Market Scan - Scans Roblox-created limited items (Filtered)")
    print("  2. Cherry Picker - Only scans specific items you choose (CODE REQUIRED)")
    print()
    
    mode_choice = input("Enter mode (1 or 2): ").strip()
    
    cherry_pick_mode = False
    cherry_pick_items = set()
    
    if mode_choice == "2":
        # Require access code for cherry picker
        print("\n" + "="*70)
        print("CHERRY PICKER ACCESS")
        print("="*70 + "\n")
        print("Cherry Picker mode requires an access code.")
        print("Enter the access code to continue:")
        print()
        
        access_code = input("Access Code: ").strip()
        
        if access_code != CHERRY_PICKER_CODE:
            print("\nACCESS DENIED: Invalid access code")
            print("Contact Magester's Market to purchase Cherry Picker access")
            sys.exit(1)
        
        print("\nACCESS GRANTED: Cherry Picker Mode Unlocked")
        
        cherry_pick_mode = True
        print("\nCherry Picker Mode Selected")
        print("Enter asset IDs to monitor (one per line)")
        print("Type 'done' when finished")
        print("Example: 1365767, 20573078, etc.")
        print()
        
        # Use first scanner account for validation
        temp_scanner = accounts['scanners'][0] if accounts.get('scanners') else accounts.get('buyer')
        temp_session_obj = requests.Session()
        temp_session_obj.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        })
        temp_session_obj.cookies.set('.ROBLOSECURITY', temp_scanner['cookie'], domain='.roblox.com', path='/')
        
        temp_scanner_data = {'session': temp_session_obj}
        temp_marketplace = MarketplaceScanner(ConfigManager.load(), accounts)
        
        while True:
            asset_input = input("Asset ID (or 'done'): ").strip()
            if asset_input.lower() == 'done':
                break
            if asset_input.isdigit():
                asset_id = int(asset_input)
                # Validate the item
                print(f"  Checking item {asset_id}...")
                time.sleep(0.5)  # Small delay to avoid rate limiting
                item_details = temp_marketplace.get_item_details(temp_scanner_data, asset_id)
                
                if item_details:
                    if 'error' in item_details:
                        if item_details['error'] == 'not_limited':
                            print(f"  ❌ Item not limited: {item_details.get('name', 'Unknown')}")
                        elif item_details['error'] == 'api_error':
                            print(f"  ❌ API Error - Status: {item_details.get('status', 'unknown')}")
                        elif item_details['error'] == 'exception':
                            print(f"  ❌ Exception: {item_details.get('message', 'unknown')}")
                        else:
                            print(f"  ❌ Item does not exist")
                    else:
                        item_name = item_details.get('name', 'Unknown')
                        print(f"  ✓ Added: {item_name} (ID: {asset_id})")
                        cherry_pick_items.add(asset_id)
                else:
                    print(f"  ❌ Could not verify item - no response")
            else:
                print("  Invalid - must be a number")
        
        if not cherry_pick_items:
            print("\nNo valid items added! Switching to Full Market mode")
            cherry_pick_mode = False
        else:
            print(f"\n✓ Monitoring {len(cherry_pick_items)} valid limited items")
    else:
        print("\nFull Market Scan Mode Selected")
        print("Scanning: Roblox-created items (taxonomy: tZsUsd2BqGViQrJ9Vs3Wah)")
        print("This filters for specific Roblox limited items")
    
    print()
    
    # Load config
    config = ConfigManager.load()
    
    # Session configuration menu
    print("="*70)
    print("SESSION CONFIGURATION")
    print("="*70 + "\n")
    
    print(f"Current discount threshold: {config['discount_threshold']}%")
    discount_input = input("Enter discount threshold for this session (press Enter to keep current): ").strip()
    if discount_input:
        try:
            config['discount_threshold'] = int(discount_input)
            print(f"Set to {config['discount_threshold']}%")
        except ValueError:
            print("Invalid input, keeping current setting")
    
    print(f"\nCurrent max price: {config['max_price']:,} R$")
    max_price_input = input("Enter max price for this session (press Enter to keep current): ").strip()
    if max_price_input:
        try:
            config['max_price'] = int(max_price_input)
            print(f"Set to {config['max_price']:,} R$")
        except ValueError:
            print("Invalid input, keeping current setting")
    
    print(f"\nCurrent min price: {config['min_price']:,} R$")
    min_price_input = input("Enter min price for this session (press Enter to keep current): ").strip()
    if min_price_input:
        try:
            config['min_price'] = int(min_price_input)
            print(f"Set to {config['min_price']:,} R$")
        except ValueError:
            print("Invalid input, keeping current setting")
    
    print(f"\nAuto-buy currently: {'ENABLED' if config['auto_buy_enabled'] else 'DISABLED'}")
    auto_buy_input = input("Enable auto-buy for this session? (y/n, press Enter to keep current): ").strip().lower()
    if auto_buy_input:
        if auto_buy_input == 'y':
            config['auto_buy_enabled'] = True
            print("Auto-buy ENABLED")
        elif auto_buy_input == 'n':
            config['auto_buy_enabled'] = False
            print("Auto-buy DISABLED (will only show deals)")
        else:
            print("Invalid input, keeping current setting")
    
    print("\n" + "-"*70)
    save_input = input("Save these settings as defaults for future runs? (y/n): ").strip().lower()
    if save_input == 'y':
        ConfigManager.save(config)
        print("Settings saved")
    else:
        print("Settings will only apply to this session")
    
    print("\n" + "="*70)
    print("STARTING SCANNER")
    print("="*70 + "\n")
    
    scanner = MarketplaceScanner(config, accounts, cherry_pick_mode, cherry_pick_items)
    scanner.run()

if __name__ == "__main__":
    main()