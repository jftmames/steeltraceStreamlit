# utils/mcp.py
import re
from datetime import datetime

# Reglas simples hardcodeadas para el MVP (adaptado de tu dq_rules.yaml)
RULES = {
    "energy": [
        {"field": "kwh", "rule": ">=0"},
        {"field": "period_start", "rule": "is_date"}
    ],
    "hr": [
        {"field": "employees_start", "rule": ">=0"},
        {"field": "exits", "rule": ">=0"}
    ]
}

def check_dq(data_list, domain):
    """Recibe una lista de dicts y devuelve el % de calidad"""
    if not data_list: return 0.0, []
    
    domain_rules = RULES.get(domain, [])
    passed_count = 0
    total_checks = 0
    
    for row in data_list:
        for r in domain_rules:
            total_checks += 1
            field = r["field"]
            val = row.get(field)
            
            # Lógica simplificada de tu apply_rule
            passed = False
            if r["rule"] == ">=0":
                try: passed = float(val) >= 0
                except: passed = False
            elif r["rule"] == "is_date":
                try: 
                    datetime.strptime(val, "%Y-%m-%d")
                    passed = True
                except: passed = False
            # ... puedes añadir más reglas aquí
            
            if passed: passed_count += 1
            
    score = (passed_count / total_checks) if total_checks > 0 else 1.0
    return round(score * 100, 1)
