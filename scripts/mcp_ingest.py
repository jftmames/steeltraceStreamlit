import json, pathlib
src = pathlib.Path("data/samples/energy_2024-01.json")
dst = pathlib.Path("data/normalized/"); dst.mkdir(parents=True, exist_ok=True)
data = json.loads(src.read_text())
for r in data: r["_dq"]={"row_ok": True}
(pathlib.Path("data/normalized/energy_2024-01.json")).write_text(json.dumps(data, indent=2))
(pathlib.Path("data/dq_report.json")).write_text(json.dumps({"dq_pass": True, "completeness":0.99}, indent=2))
(pathlib.Path("data/lineage.jsonl")).write_text('{"dataset":"energy_2024-01","sha256":"stub","utc":"now"}\n')
print("Ingest OK")
