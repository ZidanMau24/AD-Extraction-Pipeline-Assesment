# AD Extraction Pipeline

Automated pipeline for extracting applicability rules from Airworthiness Directive (AD) PDFs and evaluating aircraft configurations.

## Overview

This project implements an automated system to:
1. Extract applicability rules from AD PDFs (FAA and EASA formats)
2. Structure rules in machine-readable format (Pydantic models)
3. Evaluate whether specific aircraft configurations are affected by ADs

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Usage

```bash
# Run the complete pipeline
python main.py
```

This will:
- Extract rules from both ADs
- Evaluate all 10 test aircraft
- Verify the 3 validation examples
- Save results to `results/evaluation_results.json`

## Project Structure

```
aviation/
├── README.md                    # This file
├── report.md                    # Technical report
├── requirements.txt             # Python dependencies
├── models.py                    # Pydantic data models
├── evaluator.py                 # Evaluation engine
├── main.py                      # Main execution script
├── test_data.py                 # Test aircraft configurations
├── extractors/
│   ├── faa_extractor.py        # FAA AD parser
│   └── easa_extractor.py       # EASA AD parser
├── extracted/
│   ├── FAA_AD_2025-23-53.md    # Extracted markdown
│   └── EASA_AD_2025-0254.md    # Extracted markdown
├── results/
│   └── evaluation_results.json  # Evaluation results
└── data/
    ├── EASA_AD_2025-0254R1_1.pdf
    └── EASA_AD_US-2025-23-53_1.pdf
```

## Architecture

### 1. PDF Extraction (Docling)
- Converts PDF to markdown
- Preserves structure and formatting
- Already implemented in `extract_all_ads.py`

### 2. Data Models (Pydantic)
- `AircraftConfiguration`: Aircraft model, MSN, modifications
- `ModificationReference`: Mod/SB with revision and phase
- `ApplicabilityRule`: Models, MSN constraints, exclusions
- `AirworthinessDirective`: Complete AD with metadata
- `EvaluationResult`: Evaluation outcome with explanation

### 3. Rule Extraction
- **FAA Extractor**: Parses simple model lists
- **EASA Extractor**: Handles complex modification exclusions
- Regex-based parsing with fallback patterns

### 4. Evaluation Engine
- Model matching (exact + variant matching)
- MSN constraint checking
- Modification exclusion logic
- Batch evaluation support

## Example Results

### FAA AD 2025-23-53
**Applicability**: All Boeing MD-11, MD-10, and DC-10 variants

| Aircraft | MSN | Affected? |
|----------|-----|-----------|
| MD-11 | 48123 | ✅ Yes |
| DC-10-30F | 47890 | ✅ Yes |
| A320-214 | 5234 | ❌ No |

### EASA AD 2025-0254
**Applicability**: Airbus A320/A321 variants, EXCEPT those with specific modifications

| Aircraft | MSN | Modifications | Affected? |
|----------|-----|---------------|-----------|
| A320-214 | 5234 | None | ✅ Yes |
| A320-232 | 6789 | mod 24591 (production) | ❌ No (excluded) |
| A321-111 | 8123 | None | ✅ Yes |

## Verification Examples

All 3 verification examples from the assignment pass:

1. **MD-11F MSN 48400**: FAA ✅, EASA ❌
2. **A320-214 MSN 4500 with mod 24591**: FAA ❌, EASA ❌ (excluded)
3. **A320-214 MSN 4500 without mods**: FAA ❌, EASA ✅

## Key Features

✅ **Automated extraction** - Works on new, unseen ADs  
✅ **Structured output** - JSON with Pydantic validation  
✅ **Complex rules** - Handles modification exclusions  
✅ **Hybrid extraction** - Rule-based speed + AI fallback for edge cases  
✅ **Variant matching** - A320-214 matches A320  
✅ **Batch evaluation** - Process multiple aircraft efficiently  
✅ **Explainable** - Clear reasons for each decision  

## Limitations & Future Work

See `report.md` for detailed discussion of:
- Approach rationale
- Challenges encountered
- Known limitations (e.g., table extraction)
- Future improvements

## Author

Created for Data Science/AI Engineer Takehome Assignment
