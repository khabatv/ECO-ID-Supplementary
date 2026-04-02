# ECO-ID Supplementary Materials

This repository contains the benchmarking scripts, intentional error-prone test lists, and raw results for the manuscript: 
**"ECO-ID: An AI-driven approach for error-correction and ID conversion in multi-omics"**

## Authors & Affiliations
* **Khabat Vahabi¹**, **Matheus Fernandes Alves¹'²**, **Monica Barman¹**, **Nicole M. van Dam¹'²**, **Katja Witzel¹**, **Paula Bueno¹***
* ¹ Leibniz Institute of Vegetable and Ornamental Crops (IGZ), Großbeeren, Germany 
* ² Institute of Biodiversity, Ecology, and Evolution (IBEE), Friedrich Schiller University Jena, Germany 
* *Correspondence: bueno@igzev.de 

## Overview
ECO-ID is an interactive application designed to resolve, annotate, and cross-validate identifiers (IDs) across multiple omics domains, specifically excelling at processing human-compiled lists prone to misspellings and inconsistent naming. This repository provides the data used to validate ECO-ID’s 92-96% accuracy rate compared to traditional tools.

## Repository Structure
### scripts
* `Supplementary_Platforms_Script.py`: Python script used to benchmark ECO-ID against DAVID, bioDBnet, and g:Profiler.
* `Supplementary_biological_database_Script.py`: Logic for batch retrieval from NCBI, UniProt, Ensembl, and HGNC.
* `Supplementary_chemical_database_Script.py`: Logic for batch retrieval from PubChem, ChEMBL, KEGG, and ChemSpider.

### data
* `Supplementary_Table_S1.csv`: 100 chemical entities with human-generated errors and ECO-ID results.
* `Supplementary_Table_S2.csv`: 100 protein and gene entities with intentional errors and ECO-ID results.
* `Supplementary_Table_S3.csv`: results for 100 chemical entities with human-generated errors using ID-handling databases.
* `Supplementary_Table_S4.csv`: results for 100 protein and gene entities with human-generated errors using ID-handling databases.
* `Supplementary_Table_S4.csv`: results for 100 chemical, 100 protein and gene entities with intentional errors ID-handling platforms.

## Requirements
To run the scripts, ensure you have Python 3.8+ installed along with the libraries listed in `requirements.txt`.
pandas>=1.3.0
requests>=2.25.1
numpy>=1.21.0

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
