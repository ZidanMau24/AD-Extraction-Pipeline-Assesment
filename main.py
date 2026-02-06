"""
Main execution script for AD extraction pipeline.

This script:
1. Loads extracted markdown files
2. Extracts rules from both ADs
3. Evaluates all test aircraft
4. Saves results to JSON
5. Generates summary report
"""

import json
from pathlib import Path
from extractors import FAAExtractor, EASAExtractor
from evaluator import ADEvaluator
from test_data import TEST_AIRCRAFT, VERIFICATION_EXAMPLES
from models import AirworthinessDirective, EvaluationResult


def load_markdown(filepath: str) -> str:
    """Load markdown content from file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def save_results(results: list, filepath: str):
    """Save evaluation results to JSON file"""
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
    
    all_passed = True
    
    for idx, example in enumerate(VERIFICATION_EXAMPLES, 1):
        aircraft = example["aircraft"]
        expected = example["expected"]
        
        print(f"\nExample {idx}: {aircraft}")
        
        for result in results:
            if (result.aircraft.model == aircraft.model and 
                result.aircraft.msn == aircraft.msn):
                
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
    if all_passed:
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
    
    # Initialize extractors and evaluator
    faa_extractor = FAAExtractor()
    easa_extractor = EASAExtractor()
    evaluator = ADEvaluator()
    
    # Load and extract FAA AD
    print("\n[1/5] Loading FAA AD 2025-23-53...")
    faa_markdown = load_markdown(r"G:\aviation\extracted\FAA_AD_2025-23-53.md")
    faa_ad = faa_extractor.extract(faa_markdown, "FAA-2025-23-53")
    print(f"  ✅ Extracted {len(faa_ad.applicability_rules)} rule(s)")
    for idx, rule in enumerate(faa_ad.applicability_rules, 1):
        print(f"     Rule {idx}: {rule}")
    
    # Load and extract EASA AD
    print("\n[2/5] Loading EASA AD 2025-0254...")
    easa_markdown = load_markdown(r"G:\aviation\extracted\EASA_AD_2025-0254.md")
    easa_ad = easa_extractor.extract(easa_markdown, "EASA-2025-0254")
    print(f"  ✅ Extracted {len(easa_ad.applicability_rules)} rule(s)")
    for idx, rule in enumerate(easa_ad.applicability_rules, 1):
        print(f"     Rule {idx}: {rule}")
    
    # Evaluate test aircraft
    print("\n[3/5] Evaluating test aircraft...")
    ads = [faa_ad, easa_ad]
    all_results = evaluator.evaluate_batch(TEST_AIRCRAFT, ads)
    print(f"  ✅ Evaluated {len(TEST_AIRCRAFT)} aircraft against {len(ads)} ADs")
    
    # Evaluate verification examples
    print("\n[4/5] Evaluating verification examples...")
    verification_aircraft = [ex["aircraft"] for ex in VERIFICATION_EXAMPLES]
    verification_results = evaluator.evaluate_batch(verification_aircraft, ads)
    all_results.extend(verification_results)
    print(f"  ✅ Evaluated {len(VERIFICATION_EXAMPLES)} verification examples")
    
    # Save results
    print("\n[5/5] Saving results...")
    results_dir = Path(r"G:\aviation\results")
    results_dir.mkdir(exist_ok=True)
    
    results_file = results_dir / "evaluation_results.json"
    save_results(all_results, str(results_file))
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
