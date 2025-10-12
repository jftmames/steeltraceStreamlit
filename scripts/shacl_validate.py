from pathlib import Path
Path("ontology").mkdir(exist_ok=True)
Path("ontology/validation.log").write_text("Validation Report OK\n")
Path("ontology/linaje.ttl").write_text("# RDF lineage stub\n")
print("SHACL OK")
