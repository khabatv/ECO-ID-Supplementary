#!/usr/bin/env python3
"""
=============================================================================
 Bioinformatics Annotation Pipeline  (v2.3 – FIXED APIs & RESTORED bioDBnet)
=============================================================================
 Purpose  : Evaluate how well online tools resolve names containing errors.
 Databases: g:Profiler, bioDBnet (Restored), DAVID, MetaboAnalyst, CTS
 Outputs  : results_wide_all.csv, summary_report.csv, annotation_pipeline.log
=============================================================================
"""

import requests
import time
import sys
import os
import json
import pandas as pd
from urllib.parse import quote
import logging
from io import StringIO

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
ORGANISM  = "hsapiens"
TAXON_ID  = 9606
CHUNK     = 10
SLEEP     = 0.5  # Increased slightly to be polite to APIs
TIMEOUT   = 60

logging.basicConfig(
    filename="annotation_pipeline.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logging.info("=== Pipeline v2.3 Evaluation Mode Started ===")

# ─────────────────────────────────────────────────────────────────────────────
# CORE UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def load_list(path: str) -> list[str]:
    if not os.path.exists(path):
        logging.error(f"File not found: {path}")
        return []
    with open(path, encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip()]

def _get(url, params=None, label="") -> requests.Response | None:
    try:
        r = requests.get(url, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        logging.info(f"SUCCESS {label}")
        return r
    except Exception as e:
        logging.error(f"FAILED {label}: {e}")
        return None

def _post(url, payload=None, headers=None, is_json=True, label="") -> requests.Response | None:
    try:
        if is_json:
            r = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
        else:
            r = requests.post(url, data=payload, headers=headers, timeout=TIMEOUT)
        r.raise_for_status()
        logging.info(f"SUCCESS {label}")
        return r
    except Exception as e:
        logging.error(f"FAILED {label}: {e}")
        return None

def build_wide_table(entities: list[str], results: dict) -> pd.DataFrame:
    """Combines various tool outputs into a single broad comparison table."""
    wide = pd.DataFrame({"entity": entities})
    for db_name, df in results.items():
        if df is None or df.empty:
            wide[f"{db_name}_status"] = "failed/no_data"
            continue
        
        df = df.copy()
        if "input" not in df.columns:
            df.rename(columns={df.columns[0]: "input"}, inplace=True)
            
        # Standardizing the status column
        status_col = f"{db_name}_status"
        id_col_name = f"{db_name}_ID"
        
        # Determine the ID column (the one that isn't 'input' or 'status')
        other_cols = [c for c in df.columns if c not in ["input", "status"]]
        
        temp_df = df[["input", "status"] + ([other_cols[0]] if other_cols else [])].copy()
        temp_df.columns = ["input", status_col] + ([id_col_name] if other_cols else [])
        
        wide = wide.merge(temp_df.drop_duplicates("input"), left_on="entity", right_on="input", how="left")
        wide.drop(columns=["input"], errors="ignore", inplace=True)
        
    for col in [c for c in wide.columns if c.endswith("_status")]:
        wide[col] = wide[col].fillna("not_found")
    return wide

# ─────────────────────────────────────────────────────────────────────────────
# 1. g:Profiler
# ─────────────────────────────────────────────────────────────────────────────
def query_gprofiler(gene_list: list[str]) -> pd.DataFrame:
    url = "https://biit.cs.ut.ee/gprofiler/api/convert/convert/"
    payload = {"organism": ORGANISM, "query": gene_list, "target": "ENSG", "numeric_ns": "ENTREZGENE_ACC"}
    r = _post(url, payload=payload, label="g:Profiler")
    if r is None: return pd.DataFrame()
    
    rows = []
    for item in r.json().get("result", []):
        conv = item.get("converted")
        rows.append({
            "input": item.get("incoming"),
            "status": "mapped" if conv and conv != "None" else "not_mapped",
            "ensg": conv if conv != "None" else None
        })
    return pd.DataFrame(rows)

# ─────────────────────────────────────────────────────────────────────────────
# 2. bioDBnet (FIXED for 2026)
# ─────────────────────────────────────────────────────────────────────────────
def query_biodbnet(input_list: list[str], input_type: str, output_type: str) -> pd.DataFrame:
    """
    input_type examples: 'Gene Symbol', 'Chemical Name'
    output_type examples: 'Gene ID', 'PubChem Substance ID'
    """
    url = "https://biodbnet-abcc.ncifcrf.gov/webServices/rest.php/helper/db2db"
    params = {
        "input": input_type,
        "outputs": output_type,
        "idList": ",".join(input_list),
        "format": "row"
    }
    r = _get(url, params=params, label=f"bioDBnet ({input_type})")
    if r is None: return pd.DataFrame()
    
    try:
        data = r.json()
        rows = []
        for entry in data:
            val = entry.get(output_type)
            rows.append({
                "input": entry.get("InputValue"),
                "status": "mapped" if val and val != "-" else "not_mapped",
                "id": val if val != "-" else None
            })
        return pd.DataFrame(rows)
    except:
        return pd.DataFrame()

# ─────────────────────────────────────────────────────────────────────────────
# 3. DAVID
# ─────────────────────────────────────────────────────────────────────────────
def query_david(gene_list: list[str]) -> pd.DataFrame:
    url = "https://davidbioinformatics.nih.gov/api.jsp"
    params = {
        "type": "GENE_SYMBOL",
        "ids": ",".join(gene_list),
        "tool": "annotationReport",
        "annot": "GOTERM_BP_FAT"
    }
    r = _get(url, params=params, label="DAVID")
    if r is None: return pd.DataFrame()

    if r.text.strip().lower().startswith(('<html', '<!doctype')):
        return pd.DataFrame()

    try:
        df = pd.read_csv(StringIO(r.text), sep="\t")
        if df.empty: return df
        df.rename(columns={df.columns[0]: "input"}, inplace=True)
        df["status"] = "mapped"
        return df
    except:
        return pd.DataFrame()

# ─────────────────────────────────────────────────────────────────────────────
# 4. MetaboAnalyst (FIXED API CALL)
# ─────────────────────────────────────────────────────────────────────────────
def query_metaboanalyst(chem_list: list[str]) -> pd.DataFrame:
    url = "https://rest.xialab.ca/api/mapcompounds"
    # Documented requirement: queryList must be semicolon separated
    query_str = ";".join(chem_list) + ";"
    payload = json.dumps({"queryList": query_str, "inputType": "name"})
    headers = {'Content-Type': "application/json", 'cache-control': "no-cache"}
    
    r = _post(url, payload=payload, headers=headers, is_json=False, label="MetaboAnalyst")
    if r is None: return pd.DataFrame()

    try:
        data = r.json()
        rows = []
        # The API returns a list of dictionaries
        for entry in data:
            query = entry.get("query")
            hmdb = entry.get("hmdb")
            status = "mapped" if hmdb and hmdb != "NA" else "not_mapped"
            rows.append({"input": query, "status": status, "hmdb": hmdb})
        return pd.DataFrame(rows)
    except Exception as e:
        logging.error(f"MetaboAnalyst Parse Error: {e}")
        return pd.DataFrame()

# ─────────────────────────────────────────────────────────────────────────────
# 5. CTS
# ─────────────────────────────────────────────────────────────────────────────
def query_cts(chem_list: list[str]) -> pd.DataFrame:
    rows = []
    base = "https://cts.fiehnlab.ucdavis.edu/rest/convert/Chemical%20Name/InChIKey/"
    for name in chem_list:
        r = _get(base + quote(name), label=f"CTS ({name})")
        ik = None
        if r and r.json():
            try:
                ik = r.json()[0]["results"][0]
            except: pass
        rows.append({"input": name, "status": "mapped" if ik else "not_mapped", "inchikey": ik})
        time.sleep(0.3)
    return pd.DataFrame(rows)

# ─────────────────────────────────────────────────────────────────────────────
# EXECUTION
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("=" * 75)
    print("  Bioinformatics Annotation Evaluation Pipeline v2.3")
    print("  Testing tool resilience against name errors...")
    print("=" * 75)

    genes = load_list("gene_list100.txt")
    chems = load_list("chemicalList100.txt")
    
    if not genes or not chems:
        print("Error: Input files missing or empty.")
        return

    # Gene Section
    print(f"\n[1/2] Processing {len(genes)} Genes...")
    gp_res  = query_gprofiler(genes)
    bdb_g   = query_biodbnet(genes, "Gene Symbol", "Gene ID")
    dv_res  = query_david(genes)

    # Chemical Section
    print(f"[2/2] Processing {len(chems)} Chemicals...")
    ma_res  = query_metaboanalyst(chems)
    bdb_c   = query_biodbnet(chems, "Chemical Name", "PubChem Substance ID")
    cts_res = query_cts(chems)

    # Merging
    gene_table = build_wide_table(genes, {"gProfiler": gp_res, "bioDBnet": bdb_g, "DAVID": dv_res})
    chem_table = build_wide_table(chems, {"MetaboAnalyst": ma_res, "bioDBnet": bdb_c, "CTS": cts_res})
    
    gene_table['category'] = 'gene'
    chem_table['category'] = 'chemical'
    
    final_df = pd.concat([gene_table, chem_table], ignore_index=True, sort=False)
    final_df.to_csv("results_wide_all.csv", index=False)

    # Generate Stats
    stats = []
    results_map = {
        ("g:Profiler", "genes"): gp_res,
        ("bioDBnet", "genes"): bdb_g,
        ("DAVID", "genes"): dv_res,
        ("MetaboAnalyst", "chemicals"): ma_res,
        ("bioDBnet", "chemicals"): bdb_c,
        ("CTS", "chemicals"): cts_res
    }

    for (db, cat), df in results_map.items():
        total = len(genes) if cat == "genes" else len(chems)
        mapped = (df["status"] == "mapped").sum() if not df.empty else 0
        stats.append({"Database": db, "Type": cat, "Total": total, "Mapped": mapped, "Success_Rate": f"{(mapped/total)*100:.1f}%"})

    summary_df = pd.DataFrame(stats)
    summary_df.to_csv("summary_report.csv", index=False)
    
    print("\n" + "="*35 + " SUMMARY " + "="*35)
    print(summary_df.to_string(index=False))
    print("="*79)
    print(f"\nDetailed results saved to: results_wide_all.csv")
    print(f"Log details saved to: annotation_pipeline.log")

if __name__ == "__main__":
    main()