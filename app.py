"""
Gradio web interface for AD extraction pipeline.

Allows users to:
1. Upload AD PDF files
2. Extract applicability rules
3. View structured output
"""

import gradio as gr
import json
import tempfile
import os
from pathlib import Path
from docling.document_converter import DocumentConverter
from extractors import FAAExtractor, EASAExtractor
from models import AirworthinessDirective


def extract_ad_from_pdf(pdf_file, authority):
    """
    Extract AD rules from uploaded PDF file.
    
    Args:
        pdf_file: Uploaded PDF file
        authority: "FAA" or "EASA"
        
    Returns:
        JSON string with extracted rules
    """
    if pdf_file is None:
        return json.dumps({"error": "No file uploaded"}, indent=2)
    
    try:
        # Save uploaded file to temp location
        temp_path = pdf_file.name
        
        # Convert PDF to markdown using Docling
        converter = DocumentConverter()
        result = converter.convert(temp_path)
        markdown_text = result.document.export_to_markdown()
        
        # Extract AD ID from filename or use default
        filename = Path(temp_path).stem
        ad_id = filename.replace("_", "-")
        
        # Choose appropriate extractor
        if authority == "FAA":
            extractor = FAAExtractor()
        else:
            extractor = EASAExtractor()
        
        # Extract rules
        try:
            ad = extractor.extract(markdown_text, ad_id)
            
            # Check if rules were found. If not, try LLM fallback
            if not ad.applicability_rules:
                print("No rules found with rule-based extractor. Attempting LLM fallback...")
                from extractors import LLMFallbackExtractor
                llm_extractor = LLMFallbackExtractor()
                
                if llm_extractor.client:
                    ad = llm_extractor.extract(markdown_text, ad_id)
                else:
                    return json.dumps({
                        "warning": "No rules found and OpenAI API key not configured for fallback.",
                        "partial_result": {
                            "ad_id": ad.ad_id,
                            "raw_text_snippet": markdown_text[:500] + "..."
                        }
                    }, indent=2)
                    
        except Exception as e:
            print(f"Rule-based extraction failed: {e}. Attempting LLM fallback...")
            from extractors import LLMFallbackExtractor
            llm_extractor = LLMFallbackExtractor()
            
            if llm_extractor.client:
                ad = llm_extractor.extract(markdown_text, ad_id)
            else:
                raise e
        
        # Convert to dict for JSON output
        output = {
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
        
        return json.dumps(output, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# Create Gradio interface
with gr.Blocks(title="AD Extraction Pipeline", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 🛩️ Airworthiness Directive Extraction Pipeline
        
        Upload an AD PDF to automatically extract applicability rules and structured data.
        """
    )
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📄 Upload Document")
            
            pdf_upload = gr.File(
                label="Upload AD PDF",
                file_types=[".pdf"],
                type="filepath"
            )
            
            authority_dropdown = gr.Dropdown(
                choices=["FAA", "EASA"],
                value="FAA",
                label="Issuing Authority",
                info="Select the authority that issued this AD"
            )
            
            extract_btn = gr.Button(
                "🔍 Extract Document",
                variant="primary",
                size="lg"
            )
            
            gr.Markdown(
                """
                ### 📋 Instructions
                1. Upload an AD PDF file
                2. Select the issuing authority (FAA or EASA)
                3. Click "Extract Document"
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
        inputs=[pdf_upload, authority_dropdown],
        outputs=output_json
    )
    
    # Example button handlers
    def load_faa_example():
        pdf_path = r"G:\aviation\Final-aviation\data\EASA_AD_US-2025-23-53_1.pdf"
        return pdf_path, "FAA"
    
    def load_easa_example():
        pdf_path = r"G:\aviation\Final-aviation\data\EASA_AD_2025-0254R1_1.pdf"
        return pdf_path, "EASA"
    
    example_faa.click(
        fn=load_faa_example,
        outputs=[pdf_upload, authority_dropdown]
    )
    
    example_easa.click(
        fn=load_easa_example,
        outputs=[pdf_upload, authority_dropdown]
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
