"""
Main execution script for AD extraction pipeline.

This script:
1. Scans `data/` directory for PDF files
2. Converts PDFs to Markdown using Docling (saved to `extracted/`)
3. Automatically detects authority (FAA/EASA/etc.)
4. Extracts rules using appropriate extractor (with LLM fallback)
5. Evaluates test aircraft against all extracted ADs
6. Saves results to JSON and generates summary report
"""

import json
import os
from pathlib import Path
from typing import List, Optional

from docling.document_converter import DocumentConverter
from extractors import FAAExtractor, EASAExtractor, LLMFallbackExtractor
from evaluator import ADEvaluator
from test_data import TEST_AIRCRAFT, VERIFICATION_EXAMPLES
from models import AirworthinessDirective, EvaluationResult
from utils import detect_authority


def save_markdown(content: str, filepath: Path):
    """Save markdown content to file"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  💾 Saved markdown to: {filepath}")


def process_pdf(pdf_path: Path, extracted_dir: Path) -> Optional[str]:
    """
    Convert PDF to markdown.
    Returns the markdown content.
    """
    try:
        print(f"  🔄 Converting {pdf_path.name}...")
        converter = DocumentConverter()
        result = converter.convert(str(pdf_path))
        markdown_text = result.document.export_to_markdown()
        
        # Save to extracted folder
        md_filename = pdf_path.stem + ".md"
        save_markdown(markdown_text, extracted_dir / md_filename)
        
        return markdown_text
    except Exception as e:
        print(f"  ❌ Error converting {pdf_path.name}: {e}")
        return None


def save_results(results: list, filepath: Path):
    """Save evaluation results to JSON file"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert Pydantic models to dicts
    results_dict = []
    for result in results:
        results_dict.append({
            "aircraft": {
                "model": result.aircraft.model,
                "msn": result.aircraft.msn,
                "modifications": [
                    {
                        "type": mod.type,
                        "identifier": mod.identifier,
                        "revision": mod.revision,
                        "phase": mod.phase
                    }
                    for mod in result.aircraft.modifications_applied
                ]
            },
            "ad_id": result.ad_id,
            "is_affected": result.is_affected,
            "reason": result.reason,
            "matched_rule_index": result.matched_rule_index
        })
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results_dict, f, indent=2)


def print_summary(results: list):
    """Print summary of evaluation results"""
    print("\n" + "="*80)
    print("EVALUATION RESULTS SUMMARY")
    print("="*80)
    
    # Group by aircraft
    aircraft_results = {}
    for result in results:
        aircraft_key = str(result.aircraft)
        if aircraft_key not in aircraft_results:
            aircraft_results[aircraft_key] = []
        aircraft_results[aircraft_key].append(result)
    
    for aircraft_key, aircraft_results_list in aircraft_results.items():
        print(f"\n{aircraft_key}")
        for result in aircraft_results_list:
            status = "✅ AFFECTED" if result.is_affected else "❌ NOT AFFECTED"
            print(f"  {result.ad_id}: {status}")
            print(f"    Reason: {result.reason}")


def verify_examples(results: list):
    """Verify that verification examples produce expected results"""
    print("\n" + "="*80)
    print("VERIFICATION EXAMPLES CHECK")
    print("="*80)
    
    if not results:
        print("⚠️ No results to verify.")
        return False

    all_passed = True
    examples_checked = 0
    
    for idx, example in enumerate(VERIFICATION_EXAMPLES, 1):
        aircraft = example["aircraft"]
        expected = example["expected"]
        
        # Check if we have results for this aircraft
        aircraft_results = [r for r in results 
                           if r.aircraft.model == aircraft.model and 
                              r.aircraft.msn == aircraft.msn]
        
        if not aircraft_results:
            continue
            
        examples_checked += 1
        print(f"\nExample {idx}: {aircraft}")
        
        for result in aircraft_results:
            expected_affected = expected.get(result.ad_id)
            if expected_affected is None:
                continue
            
            passed = result.is_affected == expected_affected
            status = "✅ PASS" if passed else "❌ FAIL"
            
            print(f"  {result.ad_id}: {status}")
            print(f"    Expected: {'Affected' if expected_affected else 'Not Affected'}")
            print(f"    Got: {'Affected' if result.is_affected else 'Not Affected'}")
            print(f"    Reason: {result.reason}")
            
            if not passed:
                all_passed = False
    
    print("\n" + "="*80)
    if examples_checked == 0:
        print("⚠️ No matching verification examples found for the processed ADs.")
    elif all_passed:
        print("✅ ALL VERIFICATION EXAMPLES PASSED!")
    else:
        print("❌ SOME VERIFICATION EXAMPLES FAILED!")
    print("="*80)
    
    return all_passed


def main():
    """Main execution function"""
    print("="*80)
    print("AD EXTRACTION PIPELINE")
    print("="*80)
    
    # Setup directories
    base_dir = Path.cwd()
    data_dir = base_dir / "data"
    extracted_dir = base_dir / "extracted"
    results_dir = base_dir / "results"
    
    extracted_dir.mkdir(exist_ok=True)
    results_dir.mkdir(exist_ok=True)
    
    # 1. Find all PDF files
    if not data_dir.exists():
         print(f"❌ Data directory not found: {data_dir}")
         return

    pdf_files = list(data_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"❌ No PDF files found in {data_dir}")
        return

    print(f"\n[1/3] Processing {len(pdf_files)} PDF files...")
    
    extracted_ads = []
    
    # 2. Process each PDF
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n📄 File {i}/{len(pdf_files)}: {pdf_path.name}")
        
        # Convert to markdown
        markdown_text = process_pdf(pdf_path, extracted_dir)
        if not markdown_text:
            continue
            
        # Extract AD ID from filename
        ad_id = pdf_path.stem.replace("_", "-")
        
        # Detect Authority
        authority = detect_authority(markdown_text)
        print(f"  🔍 Detected Authority: {authority}")
        
        # Choose Extractor
        extractor = None
        if authority == "FAA":
            extractor = FAAExtractor()
        elif authority == "EASA":
            extractor = EASAExtractor()
        else:
            print(f"  ⚠️ Unknown authority ({authority}). Using LLM Fallback.")
            extractor = LLMFallbackExtractor()
        
        # Initialize ad variable
        ad = None
        
        try:
            # Primary extraction attempt
            if not isinstance(extractor, LLMFallbackExtractor):
                try:
                    ad = extractor.extract(markdown_text, ad_id)
                    print(f"  ✅ Extracted {len(ad.applicability_rules)} rule(s) via rule-based extraction")
                except Exception as e:
                    print(f"  ⚠️ Rule-based extraction failed: {e}")
                    ad = None
            else:
                 # If primary IS fallback (because authority unknown), try it
                 if extractor.client:
                     print("  Attempting LLM extraction (primary)...")
                     ad = extractor.extract(markdown_text, ad_id)
                     print(f"  ✅ Extracted {len(ad.applicability_rules)} rule(s) via LLM")
                 else:
                     print("  ❌ Unknown authority and no OpenAI key. Skipping.")
                     continue

            # Fallback logic for rule-based failure
            if (ad is None or not ad.applicability_rules) and not isinstance(extractor, LLMFallbackExtractor):
                print("  ⚠️ No rules found or extraction failed. Attempting LLM fallback...")
                llm_extractor = LLMFallbackExtractor()
                if llm_extractor.client:
                    try:
                        ad = llm_extractor.extract(markdown_text, ad_id)
                        print(f"  ✅ Extracted {len(ad.applicability_rules)} rule(s) via LLM fallback")
                    except Exception as e:
                        print(f"  ❌ LLM fallback failed: {e}")
                else:
                    print("  ⚠️ No OpenAI API key for fallback. Skipping.")

            if ad:
                extracted_ads.append(ad)
                
        except Exception as e:
            print(f"  ❌ Extraction error: {e}")

    # 3. Evaluate Results
    if not extracted_ads:
        print("\n❌ No ADS successfully extracted. Exiting.")
        return
        
    print(f"\n[2/3] Evaluating {len(TEST_AIRCRAFT)} test aircraft against {len(extracted_ads)} ADs...")
    evaluator = ADEvaluator()
    all_results = evaluator.evaluate_batch(TEST_AIRCRAFT, extracted_ads)
    print(f"  ✅ Generated {len(all_results)} evaluation results")
    
    # 4. Save and Report
    print("\n[3/3] Saving results...")
    results_file = results_dir / "evaluation_results.json"
    save_results(all_results, results_file)
    print(f"  ✅ Results saved to: {results_file}")
    
    # Print summary
    print_summary(all_results)
    
    # Verify examples
    verify_examples(all_results)
    
    print("\n" + "="*80)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("="*80)


if __name__ == "__main__":
    main()
