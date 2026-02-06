# AD Extraction Pipeline - Submission Package

## 📦 Package Contents

This folder contains the complete AD extraction pipeline implementation for the Data Science/AI Engineer takehome assignment.

### File Structure

```
Final-aviation/
├── README.md                    # Quick start guide and overview
├── report.md                    # Technical report (approach, challenges, trade-offs)
├── requirements.txt             # Python dependencies
├── models.py                    # Pydantic data models
├── evaluator.py                 # Evaluation engine
├── main.py                      # Main execution script
├── test_data.py                 # Test aircraft configurations
├── extractors/
│   ├── __init__.py             # Package init
│   ├── faa_extractor.py        # FAA AD parser
│   └── easa_extractor.py       # EASA AD parser
├── extracted/
│   ├── FAA_AD_2025-23-53.md    # Extracted FAA AD (markdown)
│   └── EASA_AD_2025-0254.md    # Extracted EASA AD (markdown)
├── data/
│   ├── EASA_AD_2025-0254R1_1.pdf    # Source EASA AD PDF
│   └── EASA_AD_US-2025-23-53_1.pdf  # Source FAA AD PDF
└── results/
    └── evaluation_results.json  # Evaluation results for all test aircraft
```

## 🚀 Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Run the Pipeline
```bash
python main.py
```

This will:
1. Extract rules from both ADs
2. Evaluate all 10 test aircraft
3. Verify the 3 validation examples
4. Save results to `results/evaluation_results.json`

## ✅ Deliverables Checklist

- [x] **Extraction Pipeline** - FAA & EASA extractors with regex parsing
- [x] **Structured Output** - Pydantic models → JSON format
- [x] **Evaluation Code** - Model matching, MSN checks, modification exclusions
- [x] **Test Results** - All 10 aircraft evaluated
- [x] **Verification Examples** - 3/3 examples PASSED (100% accuracy)
- [x] **Documentation** - README.md and report.md
- [x] **Code Quality** - Well-structured, documented, and tested

## 📊 Results Summary

### Verification Examples (3/3 Passed ✅)

| Aircraft | MSN | Modifications | FAA AD | EASA AD |
|----------|-----|---------------|--------|---------|
| MD-11F | 48400 | None | ✅ Affected | ❌ Not Affected |
| A320-214 | 4500 | mod 24591 | ❌ Not Affected | ❌ Excluded |
| A320-214 | 4500 | None | ❌ Not Affected | ✅ Affected |

### Test Aircraft (10/10 Evaluated ✅)

- **FAA AD 2025-23-53**: Affects 4/10 aircraft (Boeing MD/DC-10 variants)
- **EASA AD 2025-0254**: Affects 2/10 aircraft (Airbus A320/A321 without specific mods)

## 🔑 Key Features

✅ **Automated extraction** - Works on new, unseen ADs  
✅ **Structured output** - JSON with Pydantic validation  
✅ **Complex rules** - Handles modification exclusions  
✅ **Variant matching** - A320-214 matches A320  
✅ **Batch evaluation** - Process multiple aircraft efficiently  
✅ **Explainable** - Clear reasons for each decision  

## 📖 Documentation

- **README.md** - Quick start guide, architecture overview, example results
- **report.md** - Technical report covering:
  - Approach rationale (why Docling + rule-based + LLM fallback)
  - Challenges encountered (ambiguous language, variant matching)
  - Known limitations (MSN range parsing, LLM fallback not implemented)
  - Trade-offs (rule-based vs LLM vs VLM)
  - Future improvements

## 🛠️ Technical Stack

- **PDF Extraction**: Docling
- **Data Modeling**: Pydantic
- **Parsing**: Regex-based with structured patterns
- **Language**: Python 3.13

## 📝 Notes

- All 3 verification examples pass with 100% accuracy
- Pipeline successfully extracts 3 rules from FAA AD and 2 rules from EASA AD
- Modification exclusion logic correctly handles both production and service phases
- Results saved in structured JSON format for easy integration

---

**Ready for GitHub submission!** 🚀
