import os
import time
import logging
import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns
from Bio import Entrez

# === CONFIGURATION ===
input_file = r"C:\Users\vahabi\Downloads\BioidFigs\gene_list100.txt"
output_dir = r"C:\Users\vahabi\Downloads"
Entrez.email = "khabat.v@gmail.com"  # Set your NCBI email here

# Output paths
result_csv = os.path.join(output_dir, "gene_search_results.csv")
log_file = os.path.join(output_dir, "gene_search_log.txt")
plot_file_hits = os.path.join(output_dir, "gene_search_plot_hits.png")
plot_file_percent = os.path.join(output_dir, "gene_search_plot_percent.png")
table_file_hits = os.path.join(output_dir, "gene_search_table_hits.csv")
table_file_percent = os.path.join(output_dir, "gene_search_table_percent.csv")
os.makedirs(output_dir, exist_ok=True)

# === LOGGING SETUP ===
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", force=True)
def log(msg):
    print(msg, flush=True)
    logging.info(msg)

log("=== Starting Gene/Protein ID Search ===")

# === READ INPUT GENES ===
with open(input_file, "r", encoding="utf-8") as f:
    genes = [line.strip() for line in f if line.strip()]
log(f"Loaded {len(genes)} gene names")

# === EXPECTED OUTPUT COLUMNS ===
expected_columns = ["Gene", "NCBI_Gene_ID", "UniProt_ID", "Ensembl_ID", "HGNC_ID"]

# === API FUNCTIONS ===
def search_ncbi(name):
    try:
        log(f"[NCBI] Searching for: {name}")
        handle = Entrez.esearch(db="gene", term=f"{name}[Gene Name] AND Homo sapiens[Organism]", retmode="xml")
        record = Entrez.read(handle)
        handle.close()
        ids = record.get("IdList", [])
        if ids:
            return {"NCBI_Gene_ID": ids[0]}
    except Exception as e:
        log(f"[NCBI] {name}: {e}")
    return {}

def search_uniprot(name):
    try:
        log(f"[UniProt] Searching for: {name}")
        url = f"https://rest.uniprot.org/uniprotkb/search?query=gene:{name}+AND+organism_id:9606&fields=accession&format=tsv"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            lines = r.text.strip().splitlines()
            if len(lines) > 1:
                return {"UniProt_ID": lines[1].split("\t")[0]}
    except Exception as e:
        log(f"[UniProt] {name}: {e}")
    return {}

def search_ensembl(name):
    try:
        log(f"[Ensembl] Searching for: {name}")
        url = f"https://rest.ensembl.org/lookup/symbol/homo_sapiens/{name}?content-type=application/json"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return {"Ensembl_ID": r.json().get("id")}
    except Exception as e:
        log(f"[Ensembl] {name}: {e}")
    return {}

def search_hgnc(name):
    try:
        log(f"[HGNC] Searching for: {name}")
        url = f"https://rest.genenames.org/fetch/symbol/{name}"
        r = requests.get(url, headers={"Accept": "application/json"}, timeout=10)
        if r.status_code == 200:
            docs = r.json().get("response", {}).get("docs", [])
            if docs:
                return {"HGNC_ID": docs[0].get("hgnc_id")}
    except Exception as e:
        log(f"[HGNC] {name}: {e}")
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
for i, gene in enumerate(genes):
    if gene in df["Gene"].values:
        log(f"[{i+1}/{len(genes)}] Skipping: {gene}")
        continue

    log(f"[{i+1}/{len(genes)}] Searching: {gene}")
    result = {"Gene": gene}
    result.update(search_ncbi(gene))
    result.update(search_uniprot(gene))
    result.update(search_ensembl(gene))
    result.update(search_hgnc(gene))

    for col in expected_columns:
        result.setdefault(col, None)

    df = pd.concat([df, pd.DataFrame([result])], ignore_index=True)
    df.to_csv(result_csv, index=False)
    log(f"✔ Saved: {gene}")
    time.sleep(1)

# === SUMMARY + PLOTS ===
log("Generating summary plots and tables...")
try:
    total = len(df)
    stats_hits = {
        "NCBI": df["NCBI_Gene_ID"].notna().sum(),
        "UniProt": df["UniProt_ID"].notna().sum(),
        "Ensembl": df["Ensembl_ID"].notna().sum(),
        "HGNC": df["HGNC_ID"].notna().sum()
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
