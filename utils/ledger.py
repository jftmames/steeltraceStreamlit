# utils/ledger.py
import hashlib
import json
from datetime import datetime

def create_entry(action, details, prev_hash):
    """Crea una entrada inmutable para el ledger"""
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    data = {
        "timestamp": timestamp,
        "action": action,
        "details": details,
        "prev_hash": prev_hash
    }
    
    # Serialización determinista para el hash
    payload_str = json.dumps(data, sort_keys=True)
    current_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
    
    return {
        **data,
        "hash": current_hash
    }
