import json, pathlib
n = json.loads(pathlib.Path("data/normalized/energy_2024-01.json").read_text())
val = sum(r["kwh"]*r.get("emission_factor_co2e",0.23) for r in n)/1000.0
pathlib.Path("raga").mkdir(exist_ok=True)
pathlib.Path("raga/kpis.json").write_text(json.dumps({"E1-1.total_co2e": round(val,3)}, indent=2))
pathlib.Path("raga/explain.json").write_text(json.dumps({"dp":"E1-1.total_co2e","hypothesis":"sum(kwh*factor)","evidence":["ontology/validation.log"]}, indent=2))
print("RAGA OK")
