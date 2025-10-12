import pandas as pd
from sklearn.metrics import cohen_kappa_score
from pathlib import Path

MAP = {"valido":2, "revision":1, "incorrecto":0}

def main():
    df = pd.read_csv("docs/hitl_reviews.csv")
    # κ par-a-par y media simple
    pairs = [("rev1","rev2"),("rev1","rev3"),("rev2","rev3")]
    kappas = {}
    for a,b in pairs:
        ka = cohen_kappa_score(df[a].map(MAP), df[b].map(MAP))
        kappas[f"{a}-{b}"] = round(ka, 3)
    mean_k = round(sum(kappas.values())/len(kappas), 3)
    out = {"kappas": kappas, "kappa_mean": mean_k, "n": len(df)}
    Path("ops/hitl_kappa.json").write_text(json.dumps(out, indent=2))
    print(out)

if __name__ == "__main__"

if __name__ == "__main__":
    main()
