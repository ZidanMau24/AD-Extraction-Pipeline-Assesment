# AD Extraction Pipeline

Automated pipeline for extracting applicability rules from Airworthiness Directive (AD) PDFs and evaluating aircraft configurations.

## Overview

This project implements an automated system to:
1. **Extract** applicability rules from AD PDFs (FAA and EASA formats)
2. **Structure** rules in machine-readable format (Pydantic models)
3. **Evaluate** whether specific aircraft configurations are affected by ADs

Key Features:
- **Automatic Authority Detection**: Identifies whether an AD is FAA or EASA.
- **Hybrid Extraction**: Uses regex-based parsing for standard formats and falls back to **LLM (OpenAI)** for novel or complex formats.
- **Batch Processing**: Automatically processes all PDFs in the `data/` directory.
- **Interactive UI**: Includes a Gradio web interface for easy testing.

## Quick Start

### Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd AD-Extraction-Pipeline-Assesment
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure API Key** (Required for LLM Fallback):
    - Create a `.env` file in the root directory.
    - Add your OpenAI API key:
      ```env
      OPENAI_API_KEY=your-api-key-here
      ```

### Usage

**Option 1: Complete Batch Pipeline**
Process all PDFs in the `data/` folder and generate a full evaluation report:
```bash
python main.py
```
This will:
- Convert all PDFs in `data/` to Markdown (saved to `extracted/`)
- Detect the authority (FAA/EASA) for each AD
- Extract rules (using regex or LLM fallback)
- Evaluate all 10 against test aircraft
- Verify the 3 validation examples
- Save results to `results/evaluation_results.json`

**Option 2: Interactive Web UI**
Launch a web interface to upload PDFs and see results instantly:
```bash
python app.py
```
Open your browser at `http://localhost:7860`.

## Project Structure

```
aviation/
├── README.md                    # This file
├── report.md                    # Technical report
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (API keys)
├── models.py                    # Pydantic data models
├── evaluator.py                 # Evaluation engine
├── main.py                      # Main batch execution script
├── app.py                       # Gradio web interface
├── utils.py                     # Helper utilities (Authority Detection)
├── test_data.py                 # Test aircraft configurations
├── extractors/
│   ├── faa_extractor.py        # FAA AD parser
│   ├── easa_extractor.py       # EASA AD parser
│   └── llm_fallback.py         # LLM Fallback Extractor (OpenAI)
├── extracted/                   # Generated markdown files
├── results/                     # Generated JSON results
└── data/                        # Input PDF files
    ├── EASA_AD_2025-0254R1_1.pdf
    └── EASA_AD_US-2025-23-53_1.pdf
```

## Architecture

1.  **PDF Ingestion**:
    - **Docling** converts PDFs to structural Markdown.
    - `main.py` handles batch processing of the `data/` directory.

2.  **Authority Detection**:
    - `utils.detect_authority()` analyzes the text to determine if the AD is from FAA, EASA, or Unknown.

3.  **Rule Extraction**:
    - **FAA Extractor**: Regex-based parsing for standard FAA formats.
    - **EASA Extractor**: Regex-based parsing for EASA formats (handling complex exclusions).
    - **LLM Fallback**: If regex fails or authority is unknown, the system uses **GPT-4o-mini** (via `LLMFallbackExtractor`) to intelligently parse the AD.

4.  **Evaluation Engine**:
    - Matches aircraft configurations against extracted Pydantic models.
    - Handles model variants (e.g., A320-214 matches A320) and modification exclusions.

## Example Results

### FAA AD 2025-23-53
**Applicability**: All Boeing MD-11, MD-10, and DC-10 variants

| Aircraft | MSN | Affected? |
|----------|-----|-----------|
| MD-11 | 48123 | ✅ Yes |
| DC-10-30F | 47890 | ✅ Yes |
| A320-214 | 5234 | ❌ No |

### Test Aircraft (10/10 Evaluated ✅)

- **FAA AD 2025-23-53**: Affects 4/10 aircraft (Boeing MD/DC-10 variants)
- **EASA AD 2025-0254**: Affects 2/10 aircraft (Airbus A320/A321 without specific mods)

### LLM Fallback Verification ✅

Tested on **FAA AD 2022-03-06** (Airbus Canada A220):
- **File**: `2022-02753 (1).pdf`
- **Models Extracted**: BD-500-1A10, BD-500-1A11
- **Authority Detected**: FAA
- **Manufacturer**: Airbus Canada Limited Partnership
- **Result**: Successfully extracted despite novel format not matching regex patterns

This confirms the AI safety net works on unseen AD formats.

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
### Zidan Maulana
Created for Data Science/AI Engineer Takehome Assignment
