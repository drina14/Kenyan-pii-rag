# Design and Evaluation of a Privacy-Aware RAG Prototype with Kenyan Identifier Masking and Role-Based Document Retrieval. - DAI034 Capstone

## What this repo does
Detects and masks Kenyan national ID numbers, Kenyan phone numbers and names in synthetic clinic text, using Presidio with custom recognisers.

## Setup
Python 3.12, then:
    python -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    python -m spacy download en_core_web_lg

## Run
    python src/01_default_presidio.py
    python src/02_baseline.py            (default Presidio)
    python src/02_baseline.py --ke       (with Kenyan recognisers)
    python src/03_mask.py                (before/after masking)

## Data
All data is synthetic. No real person, ID or phone number is used.

## Status (update before each review)
Working:
- 10-record synthetic dataset with labelled entities
- Baseline: default Presidio finds 0/8 Kenyan national IDs
- Kenyan ID recogniser: 8/8, no decoy false positives (context window 3)
- Kenyan phone recogniser; masking: 24/24 labelled identifiers masked

Incomplete:
- Dataset is small and was used to tune the rules, the larger dataset is still being prepared.
- Role-based retrieval and RAG started but not completed
- Query masking not started

Problems met:
- Context window of 5 flagged a decoy next to a real ID; narrowed to 3
- Default Presidio read a local phone number as a date