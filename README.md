# ECO-ID Supplementary Materials

This repository contains the benchmarking scripts, intentional error-prone test lists, and raw results for the manuscript: 
**"ECO-ID: An AI-driven approach for error-correction and ID conversion in multi-omics"**

## Authors & Affiliations
* **Khabat Vahabi¹**, **Matheus Fernandes Alves¹'²**, **Monica Barman¹**, **Nicole M. van Dam¹'²**, **Katja Witzel¹**, **Paula Bueno¹***
* [cite_start]¹ Leibniz Institute of Vegetable and Ornamental Crops (IGZ), Großbeeren, Germany [cite: 1, 2]
* [cite_start]² Institute of Biodiversity, Ecology, and Evolution (IBEE), Friedrich Schiller University Jena, Germany [cite: 3]
* [cite_start]*Correspondence: bueno@igzev.de [cite: 4]

## Overview
[cite_start]ECO-ID is an interactive application designed to resolve, annotate, and cross-validate identifiers (IDs) across multiple omics domains, specifically excelling at processing human-compiled lists prone to misspellings and inconsistent naming[cite: 11, 12]. [cite_start]This repository provides the data used to validate ECO-ID’s 92-96% accuracy rate compared to traditional tools[cite: 14].

## Repository Structure
### /scripts
* [cite_start]`Supplementary_Platforms_Script.py`: Python script used to benchmark ECO-ID against DAVID, bioDBnet, and g:Profiler[cite: 80].
* [cite_start]`Supplementary_biological_database_Script.py`: Logic for batch retrieval from NCBI, UniProt, Ensembl, and HGNC[cite: 84].
* [cite_start]`Supplementary_chemical_database_Script.py`: Logic for batch retrieval from PubChem, ChEMBL, KEGG, and ChemSpider[cite: 84].

### /data
* [cite_start]`Supplementary_Table_S1.csv`: 100 chemical entities with human-generated errors and ECO-ID results[cite: 81].
* [cite_start]`Supplementary_Table_S2.csv`: 100 protein and gene entities with intentional errors and ECO-ID results[cite: 83].
* [cite_start]`Supplementary_Table_S3.csv`: Comparative results for chemical ID-handling tools (MetaboAnalyst, CTS)[cite: 80].
* [cite_start]`Supplementary_Table_S4.csv`: Comparative results for biological ID-handling tools[cite: 80].

## Requirements
To run the scripts, ensure you have Python 3.8+ installed along with the libraries listed in `requirements.txt`.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
