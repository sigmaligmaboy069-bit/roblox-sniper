#!/usr/bin/env python3
"""
License Server for RobloxSniper
Validates and tracks license key activations
Host this on Replit, PythonAnywhere, or Vercel
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime, timedelta
import hashlib

app = Flask(__name__)
CORS(app)

# Database file
DB_FILE = "license_database.json"

# Admin password (change this!)
ADMIN_PASSWORD = "6ce99aa71f_MagesterRulez"

# Initial valid keys
INITIAL_KEYS = {
    # Monthly Keys + Test key M-7K2P-9X4L-H6TY-3QW8
    "M-7K2P-9X4L-H6TY-3QW8": {"type": "monthly", "duration_days": 0.020833, "used": False, "hwid": None, "activated_date": None},
    "M-5N8M-2R7V-K9YH-4PT6": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
    "M-3Q9L-6X2N-8WR4-7TH5": {"type": "monthly", "duration_days": 30, "used": False, "hwid": None, "activated_date": None},
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
    
    # Lifetime Keys
    "L-9X4M-7K2P-5NH8-3YR6": {"type": "lifetime", "duration_days": "unlimited", "used": False, "hwid": None, "activated_date": None},
    "L-4P8L-2Y7K-6RH9-5NX3": {"type": "lifetime", "duration_days": "unlimited", "used": False, "hwid": None, "activated_date": None},
    "L-7K2R-9P4Y-3LH8-6NX5": {"type": "lifetime", "duration_days": "unlimited", "used": False, "hwid": None, "activated_date": None},
    "L-5N9L-8R3K-2YH7-4PX6": {"type": "lifetime", "duration_days": "unlimited", "used": False, "hwid": None, "activated_date": None},
    "L-3P6Y-7R2L-9KH4-8NX5": {"type": "lifetime", "duration_days": "unlimited", "used": False, "hwid": None, "activated_date": None},
    "L-8Y4P-2L7R-5KH9-3NX6": {"type": "lifetime", "duration_days": "unlimited", "used": False, "hwid": None, "activated_date": None},
    "L-2R9L-6Y3P-8KH4-7NX5": {"type": "lifetime", "duration_days": "unlimited", "used": False, "hwid": None, "activated_date": None},
    "L-6P3Y-9K2R-4LH8-5NX7": {"type": "lifetime", "duration_days": "unlimited", "used": False, "hwid": None, "activated_date": None},
    "L-9K7P-4R2L-8YH5-3NX6": {"type": "lifetime", "duration_days": "unlimited", "used": False, "hwid": None, "activated_date": None},
    "L-4L8Y-2K7P-6RH9-5NX3": {"type": "lifetime", "duration_days": "unlimited", "used": False, "hwid": None, "activated_date": None},
    "L-7R2P-9K4Y-3LH8-6NX5": {"type": "lifetime", "duration_days": "unlimited", "used": False, "hwid": None, "activated_date": None},
    "L-5Y9P-8R3L-2KH7-4NX6": {"type": "lifetime", "duration_days": "unlimited", "used": False, "hwid": None, "activated_date": None},
    "L-3P6L-7Y2R-9KH4-8NX5": {"type": "lifetime", "duration_days": "unlimited", "used": False, "hwid": None, "activated_date": None},
    "L-8K4R-2P7Y-5LH9-3NX6": {"type": "lifetime", "duration_days": "unlimited", "used": False, "hwid": None, "activated_date": None},
    "L-2Y9R-6P3K-8LH4-7NX5": {"type": "lifetime", "duration_days": "unlimited", "used": False, "hwid": None, "activated_date": None},
    "L-6R3L-9P2Y-4KH8-5NX7": {"type": "lifetime", "duration_days": "unlimited", "used": False, "hwid": None, "activated_date": None},
    "L-9P7K-4Y2R-8LH5-3NX6": {"type": "lifetime", "duration_days": "unlimited", "used": False, "hwid": None, "activated_date": None},
    "L-4R8P-2Y7K-6LH9-5NX3": {"type": "lifetime", "duration_days": "unlimited", "used": False, "hwid": None, "activated_date": None},
    "L-7L2Y-9P4R-3KH8-6NX5": {"type": "lifetime", "duration_days": "unlimited", "used": False, "hwid": None, "activated_date": None},
    "L-5K9Y-8L3R-2PH7-4NX6": {"type": "lifetime", "duration_days": "unlimited", "used": False, "hwid": None, "activated_date": None},
}

def load_database():
    """Load database from file"""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    # Initialize with default keys
    save_database(INITIAL_KEYS)
    return INITIAL_KEYS

def save_database(db):
    """Save database to file"""
    with open(DB_FILE, 'w') as f:
        json.dump(db, f, indent=2)

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "RobloxSniper License Server",
        "version": "1.0.0"
    })

@app.route('/api/validate', methods=['POST'])
def validate_license():
    """Validate and activate a license key"""
    data = request.get_json()
    
    if not data:
        return jsonify({"valid": False, "message": "No data provided"}), 400
    
    key = data.get('key', '').strip().upper()
    hwid = data.get('hwid', '').strip()
    
    if not key or not hwid:
        return jsonify({"valid": False, "message": "Missing key or HWID"}), 400
    
    # Load database
    db = load_database()
    
    # Check if key exists
    if key not in db:
        return jsonify({"valid": False, "message": "Invalid key"}), 200
    
    key_data = db[key]
    
    # Check if key is already used by different HWID
    if key_data['used']:
        if key_data['hwid'] != hwid:
            return jsonify({
                "valid": False,
                "message": "Key already activated on another computer"
            }), 200
        # Key was used by this HWID - check expiration
        if key_data['type'] == 'monthly':
            activated = datetime.fromisoformat(key_data['activated_date'])
            days_passed = (datetime.now() - activated).days
            if days_passed > 30:
                return jsonify({
                    "valid": False,
                    "message": "License expired"
                }), 200
            remaining = 30 - days_passed
            return jsonify({
                "valid": True,
                "type": "Monthly",
                "days_remaining": remaining,
                "message": f"Valid - {remaining} days remaining"
            }), 200
        else:
            return jsonify({
                "valid": True,
                "type": "Lifetime",
                "message": "Valid - Lifetime license"
            }), 200
    
    # First time activation
    db[key]['used'] = True
    db[key]['hwid'] = hwid
    db[key]['activated_date'] = datetime.now().isoformat()
    save_database(db)
    
    license_type = key_data['type'].capitalize()
    
    return jsonify({
        "valid": True,
        "type": license_type,
        "message": f"License activated successfully - {license_type}",
        "days_remaining": 30 if key_data['type'] == 'monthly' else "unlimited"
    }), 200

@app.route('/api/admin/stats', methods=['POST'])
def admin_stats():
    """Admin endpoint to view statistics"""
    data = request.get_json()
    password = data.get('password', '')
    
    if password != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401
    
    db = load_database()
    
    total_keys = len(db)
    used_keys = sum(1 for k in db.values() if k['used'])
    unused_keys = total_keys - used_keys
    monthly_keys = sum(1 for k in db.values() if k['type'] == 'monthly')
    lifetime_keys = sum(1 for k in db.values() if k['type'] == 'lifetime')
    
    active_licenses = []
    for key, data in db.items():
        if data['used']:
            active_licenses.append({
                "key": key,
                "type": data['type'],
                "hwid": data['hwid'][:16] + "...",
                "activated": data['activated_date']
            })
    
    return jsonify({
        "total_keys": total_keys,
        "used_keys": used_keys,
        "unused_keys": unused_keys,
        "monthly_keys": monthly_keys,
        "lifetime_keys": lifetime_keys,
        "active_licenses": active_licenses
    }), 200

@app.route('/api/admin/revoke', methods=['POST'])
def admin_revoke():
    """Admin endpoint to revoke a license"""
    data = request.get_json()
    password = data.get('password', '')
    key = data.get('key', '').strip().upper()
    
    if password != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401
    
    if not key:
        return jsonify({"error": "No key provided"}), 400
    
    db = load_database()
    
    if key not in db:
        return jsonify({"error": "Key not found"}), 404
    
    db[key]['used'] = False
    db[key]['hwid'] = None
    db[key]['activated_date'] = None
    save_database(db)
    
    return jsonify({"success": True, "message": f"Key {key} revoked"}), 200

if __name__ == '__main__':
    # For local testing
    app.run(debug=True, host='0.0.0.0', port=5000)