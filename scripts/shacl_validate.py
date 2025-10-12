import json
from pathlib import Path
from datetime import datetime
from rdflib import Graph, Namespace, Literal, RDF, XSD, URIRef
from pyshacl import validate

# --- Paths
ROOT = Path(".")
ONTOLOGY_FILE = ROOT / "ontology" / "esrs.owl"
SHACL_E1 = ROOT / "contracts" / "shacl_e1.ttl"
OUT_VALIDATION = ROOT / "ontology" / "validation.log"
OUT_LINEAGE = ROOT / "ontology" / "linaje.ttl"

# --- Namespaces
EX = Namespace("http://example.com/esrs#")

def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def _add_evidence(g: Graph, subj: URIRef, ev_path: str):
    ev = URIRef(str(subj) + "/evidence/1")
    g.add((subj, EX.hasEvidence, ev))
    g.add((ev, RDF.type, EX.Evidencia))
    g.add((ev, EX.evidencePath, Literal(ev_path, datatype=XSD.string)))
    g.add((ev, EX.sha256, Literal("stub", datatype=XSD.string)))

def _materialize_e1(g: Graph, data_path: Path):
    """
    Crea triples para E1Record desde data/normalized/energy_*.json
    """
    records = _load_json(data_path)
    for i, r in enumerate(records, start=1):
        subj = URIRef(f"http://example.com/esrs#E1Record/{i}")
        g.add((subj, RDF.type, EX.E1Record))
        if "company_id" in r:
            g.add((subj, EX.companyId, Literal(r["company_id"], datatype=XSD.string)))
        if "period_start" in r:
            g.add((subj, EX.periodStart, Literal(r["period_start"], datatype=XSD.date)))
        if "period_end" in r:
            g.add((subj, EX.periodEnd, Literal(r["period_end"], datatype=XSD.date)))
        if "kwh" in r:
            g.add((subj, EX.kwh, Literal(r["kwh"], datatype=XSD.decimal)))
        if "emission_factor_co2e" in r:
            g.add((subj, EX.emissionFactor, Literal(r["emission_factor_co2e"], datatype=XSD.decimal)))

        # Añade evidencia mínima (enlázala si ya tienes manifest/hashes)
        _add_evidence(g, subj, ev_path=f"data/normalized/{data_path.name}")

def main():
    # Crear carpeta
    OUT_VALIDATION.parent.mkdir(parents=True, exist_ok=True)

    # 1) Cargar ontología base
    g = Graph()
    if ONTOLOGY_FILE.exists():
        g.parse(ONTOLOGY_FILE, format="turtle")

    # 2) Materializar dominios (por ahora E1)
    norm_energy = ROOT / "data" / "normalized" / "energy_2024-01.json"
    if not norm_energy.exists():
        raise SystemExit("No existe data/normalized/energy_2024-01.json. Ejecuta primero mcp_ingest.py")

    _materialize_e1(g, norm_energy)

    # 3) Ejecutar validación SHACL (E1)
    shacl_graph = Graph()
    shacl_graph.parse(SHACL_E1, format="turtle")

    conforms, results_graph, results_text = validate(
        data_graph=g,
        shacl_graph=shacl_graph,
        inference="rdfs",
        abort_on_first=False,
        allow_infos=True,
        allow_warnings=True
    )

    # 4) Guardar outputs
    ts = datetime.utcnow().isoformat() + "Z"
    OUT_VALIDATION.write_text(
        f"[{ts}] SHACL conforms = {conforms}\n\n{results_text}",
        encoding="utf-8"
    )
    g.serialize(destination=OUT_LINEAGE, format="turtle")

    print("SHACL:", "OK" if conforms else "CONSTRAINTS FAILED")
    print(f"- Reporte: {OUT_VALIDATION}")
    print(f"- Linaje RDF: {OUT_LINEAGE}")

if __name__ == "__main__":
    main()
