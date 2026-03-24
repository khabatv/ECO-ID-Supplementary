import os
import time
import logging
import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns
from chembl_webresource_client.new_client import new_client
from chemspipy import ChemSpider

# === CONFIGURATION ===
compound_file = r"C:\Users\vahabi\Downloads\BioidFigs\chemicalList101.txt"
#compound_file = r"C:\Users\vahabi\Downloads\chemicalList3.txt"
output_dir = r"C:\Users\vahabi\Downloads"
chemspider_api_key = "kWWAly3PDq5TGlmnLBhi24qTqDfQL7dA6UOMWtFu"

# Output paths
result_csv = os.path.join(output_dir, "compound_search_results.csv")
log_file = os.path.join(output_dir, "compound_search_log.txt")
plot_file_hits = os.path.join(output_dir, "search_success_plot_hits.png")
plot_file_percent = os.path.join(output_dir, "search_success_plot_percent.png")
table_file_hits = os.path.join(output_dir, "search_success_table_hits.csv")
table_file_percent = os.path.join(output_dir, "search_success_table_percent.csv")
os.makedirs(output_dir, exist_ok=True)

# === LOGGING SETUP ===
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", force=True)
def log(msg):
    print(msg, flush=True)
    logging.info(msg)

log("=== Starting Compound ID Search with ChemSpider ===")
# === INIT ChemSpider CLIENT ===
cs = ChemSpider(chemspider_api_key)
# === READ INPUT COMPOUNDS ===
with open(compound_file, "r", encoding="utf-8") as f:
    compounds = [line.strip() for line in f if line.strip()]
log(f"Loaded {len(compounds)} compound names")

# === EXPECTED OUTPUT COLUMNS ===
expected_columns = [
    "Compound", "PubChem_CID", "PubChem_InChIKey", "PubChem_SMILES",
    "ChEMBL_ID", "ChEMBL_SMILES", "ChEMBL_InChIKey",
    "KEGG_ID", "ChemSpider_ID", "ChemSpider_SMILES", "ChemSpider_InChIKey", "ChemSpider_InChI", "ChemSpider_Formula", "ChemSpider_Mass"
]

# === PubChem ===
def search_pubchem(name):
    try:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/property/CanonicalSMILES,InChIKey/JSON"
        log(f"[PubChem] GET {url}")
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        props = r.json()['PropertyTable']['Properties'][0]
        return {
            "PubChem_InChIKey": props.get("InChIKey"),
            "PubChem_SMILES": props.get("CanonicalSMILES"),
            "PubChem_CID": props.get("CID")
        }
    except Exception as e:
        log(f"[PubChem] {name}: {e}")
        return {}

# === KEGG ===
def search_kegg(name):
    try:
        url = f"http://rest.kegg.jp/find/compound/{name}"
        log(f"[KEGG] GET {url}")
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        if r.text.strip():
            line = r.text.strip().split("\n")[0]
            return {"KEGG_ID": line.split("\t")[0].replace("cpd:", "")}
        else:
            log(f"[KEGG] No match found for: {name}")
    except Exception as e:
        log(f"[KEGG] {name}: {e}")
    return {}

# === ChEMBL ===
def search_chembl(name):
    try:
        log(f"[ChEMBL] Searching ChEMBL for: {name}")
        mols = new_client.molecule.filter(pref_name__icontains=name)
        for m in mols:
            return {
                "ChEMBL_ID": m.get("molecule_chembl_id"),
                "ChEMBL_SMILES": m.get("molecule_structures", {}).get("canonical_smiles"),
                "ChEMBL_InChIKey": m.get("molecule_structures", {}).get("standard_inchi_key")
            }
        log(f"[ChEMBL] No match found for: {name}")
    except Exception as e:
        log(f"[ChEMBL] {name}: {e}")
    return {}

# === ChemSpider search with ChemSpiPy ===
def search_chemspider(name):
    try:
        log(f"[ChemSpider] Searching ChemSpider for: {name}")
        results = cs.search(name)
        if not results:
            log(f"[ChemSpider] No results for: {name}")
            return {}
        c = results[0]  # take first hit
        return {
            "ChemSpider_ID": c.csid,
            "ChemSpider_SMILES": c.smiles,
            "ChemSpider_InChI": c.inchi,
            "ChemSpider_InChIKey": c.inchikey,
            "ChemSpider_Formula": c.molecular_formula,
            "ChemSpider_Mass": c.molecular_weight
        }
    except Exception as e:
        log(f"[ChemSpider] {name}: {e}")
        return {}

# === LOAD OR INIT RESULT FILE ===
if os.path.exists(result_csv):
    df = pd.read_csv(result_csv)
    log(f"Loaded existing results with {len(df)} entries")
else:
    df = pd.DataFrame(columns=expected_columns)
    df.to_csv(result_csv, index=False)
    log("Initialized result file")

# === MAIN SEARCH LOOP ===
for i, compound in enumerate(compounds):
    if compound in df["Compound"].values:
        log(f"[{i+1}/{len(compounds)}] Skipping: {compound}")
        continue

    log(f"[{i+1}/{len(compounds)}] Searching: {compound}")
    result = {"Compound": compound}
    result.update(search_pubchem(compound))
    result.update(search_kegg(compound))
    result.update(search_chembl(compound))
    result.update(search_chemspider(compound))

    for col in expected_columns:
        result.setdefault(col, None)

    df = pd.concat([df, pd.DataFrame([result])], ignore_index=True)
    df.to_csv(result_csv, index=False)
    log(f"✔ Saved: {compound}")
    time.sleep(1)

# === SUMMARY + BEAUTIFUL PLOTS ===
log("Generating summary plots and tables...")
try:
    total = len(df)
    stats_hits = {
        "PubChem": df["PubChem_CID"].notna().sum(),
        "ChEMBL": df["ChEMBL_ID"].notna().sum(),
        "KEGG": df["KEGG_ID"].notna().sum(),
        "ChemSpider": df["ChemSpider_ID"].notna().sum()
    }
    stats_percent = {k: (v / total) * 100 for k, v in stats_hits.items()}

    pd.DataFrame([stats_hits]).to_csv(table_file_hits, index=False)
    pd.DataFrame([stats_percent]).to_csv(table_file_percent, index=False)

    sns.set(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.barplot(x=list(stats_hits.keys()), y=list(stats_hits.values()), palette="crest", ax=ax)
    ax.set_title("Successful Hits per Database", fontsize=14)
    ax.set_ylabel("Hit Count")
    ax.set_xlabel("Database")
    plt.tight_layout()
    plt.savefig(plot_file_hits)
    plt.close()

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.barplot(x=list(stats_percent.keys()), y=list(stats_percent.values()), palette="flare", ax=ax)
    ax.set_title("Hit Percentage per Database", fontsize=14)
    ax.set_ylabel("Percentage (%)")
    ax.set_xlabel("Database")
    ax.set_ylim(0, 100)
    plt.tight_layout()
    plt.savefig(plot_file_percent)
    plt.close()

    log(f"Plots and tables saved successfully.")
except Exception as e:
    log(f"Plotting failed: {e}")

log("=== DONE ===")
logging.shutdown()
