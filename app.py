"""
Gradio web interface for AD extraction pipeline.

Allows users to:
1. Upload AD PDF files (multiple)
2. Automatically detect authority (FAA, EASA, etc.)
3. Extract applicability rules with fallback
4. View structured output
"""

import gradio as gr
import json
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Any, Union
from docling.document_converter import DocumentConverter
from extractors import FAAExtractor, EASAExtractor, LLMFallbackExtractor
from utils import detect_authority


def extract_ad_from_pdf(pdf_files: Union[List[str], List[Any]]) -> str:
    """
    Extract AD rules from uploaded PDF files.
    
    Args:
        pdf_files: List of paths to uploaded PDF files (or file objects depending on Gradio version)
        
    Returns:
        JSON string with extracted rules for all files
    """
    if not pdf_files:
        return json.dumps({"error": "No files uploaded"}, indent=2)
    
    results = []
    
    # Ensure pdf_files is a list
    if not isinstance(pdf_files, list):
        pdf_files = [pdf_files]
        
    for pdf_file in pdf_files:
        try:
            # Handle different Gradio file object structures
            # Later versions return just the path string
            if isinstance(pdf_file, str):
                pdf_path = pdf_file
            elif hasattr(pdf_file, 'name'):
                pdf_path = pdf_file.name
            else:
                results.append({"error": f"Unknown file object type: {type(pdf_file)}"})
                continue

            # Convert PDF to markdown using Docling
            converter = DocumentConverter()
            result = converter.convert(pdf_path)
            markdown_text = result.document.export_to_markdown()
            
            # Extract AD ID from filename
            filename = Path(pdf_path).stem
            ad_id = filename.replace("_", "-")
            
            # Detect authority
            authority = detect_authority(markdown_text)
            print(f"Detected authority for {filename}: {authority}")
            
            # Choose extractor
            extractor = None
            if authority == "FAA":
                extractor = FAAExtractor()
            elif authority == "EASA":
                extractor = EASAExtractor()
            else:
                print(f"Unknown or fallback authority ({authority}). Using LLM Fallback.")
                extractor = LLMFallbackExtractor()
            
            ad = None
            
            # Try primary extraction
            if not isinstance(extractor, LLMFallbackExtractor):
                try:
                    ad = extractor.extract(markdown_text, ad_id)
                except Exception as e:
                    print(f"Primary extraction failed for {authority}: {e}")
            
            # Fallback logic
            # Use LLM if:
            # 1. Primary extractor was skipped (LLM Fallback chosen initially)
            # 2. Primary extractor failed (ad is None)
            # 3. Primary extractor returned empty rules
            if isinstance(extractor, LLMFallbackExtractor):
                # Using LLM as primary
                if extractor.client:
                    ad = extractor.extract(markdown_text, ad_id)
                else:
                    results.append({
                        "file": filename, 
                        "error": "Authority unknown and no OpenAI key for fallback"
                    })
                    continue
            elif ad is None or not ad.applicability_rules:
                print(f"Attempting LLM fallback for {ad_id}...")
                llm_extractor = LLMFallbackExtractor()
                if llm_extractor.client:
                    try:
                        ad = llm_extractor.extract(markdown_text, ad_id)
                    except Exception as e:
                        results.append({
                            "file": filename,
                            "error": f"LLM fallback failed: {str(e)}"
                        })
                        continue
                else:
                    # Return partial result if available, else error
                    if ad:
                        results.append({
                            "file": filename,
                            "warning": "No rules found by rule-based extractor and OpenAI key missing",
                            "partial_data": {
                                "ad_id": ad.ad_id,
                                "authority": ad.issuing_authority
                            }
                        })
                    else:
                        results.append({
                            "file": filename,
                            "error": "Extraction failed and no OpenAI key for fallback"
                        })
                    continue
            
            if ad:
                # Convert to dict for JSON output
                ad_data = {
                    "ad_id": ad.ad_id,
                    "issuing_authority": ad.issuing_authority,
                    "effective_date": ad.effective_date,
                    "manufacturer": ad.manufacturer,
                    "applicability_rules": [
                        {
                            "aircraft_models": rule.aircraft_models,
                            "msn_constraint": {
                                "type": rule.msn_constraint.type,
                                "min_msn": rule.msn_constraint.min_msn,
                                "max_msn": rule.msn_constraint.max_msn,
                                "specific_msns": rule.msn_constraint.specific_msns
                            },
                            "excluded_if_modifications": [
                                {
                                    "type": mod.type,
                                    "identifier": mod.identifier,
                                    "revision": mod.revision,
                                    "phase": mod.phase
                                }
                                for mod in rule.excluded_if_modifications
                            ],
                            "required_modifications": [
                                {
                                    "type": mod.type,
                                    "identifier": mod.identifier,
                                    "revision": mod.revision,
                                    "phase": mod.phase
                                }
                                for mod in rule.required_modifications
                            ]
                        }
                        for rule in ad.applicability_rules
                    ],
                    "raw_applicability_text": ad.raw_applicability_text
                }
                results.append(ad_data)
                
        except Exception as e:
             results.append({
                "file": Path(pdf_path).name if 'pdf_path' in locals() else "unknown",
                "error": str(e)
            })

    return json.dumps(results, indent=2)


# Create Gradio interface
with gr.Blocks(title="AD Extraction Pipeline", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 🛩️ Airworthiness Directive Extraction Pipeline
        
        Upload AD PDF files to automatically extract applicability rules and structured data.
        The system automatically detects the issuing authority (FAA, EASA, etc.) and extracts rules.
        """
    )
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📄 Upload Document(s)")
            
            pdf_upload = gr.File(
                label="Upload AD PDFs",
                file_types=[".pdf"],
                file_count="multiple",
                type="filepath"
            )
            
            extract_btn = gr.Button(
                "🔍 Extract Documents",
                variant="primary",
                size="lg"
            )
            
            gr.Markdown(
                """
                ### 📋 Instructions
                1. Upload one or more AD PDF files
                2. Click "Extract Documents"
                3. The system will detect the authority and extract rules
                4. View the structured output →
                """
            )
        
        with gr.Column(scale=2):
            gr.Markdown("### 📊 Extraction Output")
            
            output_json = gr.JSON(
                label="Extracted AD Rules",
                show_label=False
            )
    
    # Example section
    gr.Markdown("### 💡 Example ADs")
    
    with gr.Row():
        example_faa = gr.Button("Load FAA AD 2025-23-53", size="sm")
        example_easa = gr.Button("Load EASA AD 2025-0254", size="sm")
    
    # Event handlers
    extract_btn.click(
        fn=extract_ad_from_pdf,
        inputs=[pdf_upload],
        outputs=output_json
    )
    
    # Example button handlers
    def load_faa_example():
        # Use relative path compatible with user's environment
        pdf_path = os.path.join(os.getcwd(), "data", "EASA_AD_US-2025-23-53_1.pdf")
        if not os.path.exists(pdf_path):
             return None 
        return [pdf_path]
    
    def load_easa_example():
        # Use relative path compatible with user's environment
        pdf_path = os.path.join(os.getcwd(), "data", "EASA_AD_2025-0254R1_1.pdf")
        if not os.path.exists(pdf_path):
             return None
        return [pdf_path]
    
    example_faa.click(
        fn=load_faa_example,
        outputs=[pdf_upload]
    )
    
    example_easa.click(
        fn=load_easa_example,
        outputs=[pdf_upload]
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
