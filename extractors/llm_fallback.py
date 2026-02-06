"""
LLM Fallback Extractor using OpenAI.

Uses OpenAI's GPT-4o-mini to extract AD rules when rule-based extraction fails.
"""

import os
import json
from typing import List, Optional
from openai import OpenAI
from dotenv import load_dotenv

from models import (
    AirworthinessDirective,
    ApplicabilityRule,
    MSNConstraint,
    ModificationReference
)

# Load environment variables
load_dotenv()

class LLMFallbackExtractor:
    """
    Extractor that uses OpenAI's API to parse difficult ADs.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize with API key.
        
        Args:
            api_key: OpenAI API key. If None, tries to get from env var OPENAI_API_KEY.
        """
        self.api_key = api_key or os.getenv("OPEN_AI_API") # Based on user's .env file name
        
        if not self.api_key:
            print("Warning: No OpenAI API key found. LLM fallback will not work.")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)
    
    def extract(self, markdown_text: str, ad_id: str) -> AirworthinessDirective:
        """
        Extract AD rules using LLM.
        
        Args:
            markdown_text: Markdown content of the AD
            ad_id: AD identifier
            
        Returns:
            AirworthinessDirective object
        """
        if not self.client:
            raise ValueError("OpenAI API key not configured")
            
        # Define the system prompt with extraction instructions
        system_prompt = """
        You are an aviation safety expert. Extract Applicability Rules from the provided Airworthiness Directive (AD) text.
        
        Output must be a valid JSON object matching this structure:
        {
            "issuing_authority": "FAA" or "EASA",
            "effective_date": "string",
            "manufacturer": "string",
            "applicability_rules": [
                {
                    "aircraft_models": ["model1", "model2"],
                    "msn_constraint": {
                        "type": "all" or "range" or "specific",
                        "min_msn": integer or null,
                        "max_msn": integer or null,
                        "specific_msns": [list of ints] or null
                    },
                    "excluded_if_modifications": [
                        {
                            "type": "mod" or "sb",
                            "identifier": "string",
                            "revision": "string" or null,
                            "phase": "production" or "service" or null
                        }
                    ],
                    "required_modifications": []
                }
            ]
        }
        
        RULES:
        1. "aircraft_models" must match the AD text exactly.
        2. Handle "except those on which..." as exclusions.
        3. Distinguish between modifications (mod) and Service Bulletins (SB).
        4. If phase (production/service) is not specified, use null.
        """
        
        # Call OpenAI API
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract rules from this AD:\n\n{markdown_text[:15000]}"} # Truncate if too long
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            
            # Map JSON data to Pydantic models
            rules = []
            for rule_data in data.get("applicability_rules", []):
                
                # Parse MSN constraint
                msn_data = rule_data.get("msn_constraint", {})
                msn_constraint = MSNConstraint(
                    type=msn_data.get("type", "all"),
                    min_msn=msn_data.get("min_msn"),
                    max_msn=msn_data.get("max_msn"),
                    specific_msns=msn_data.get("specific_msns")
                )
                
                # Parse exclusions
                exclusions = []
                for mod_data in rule_data.get("excluded_if_modifications", []):
                    exclusions.append(ModificationReference(
                        type=mod_data.get("type"),
                        identifier=mod_data.get("identifier"),
                        revision=mod_data.get("revision"),
                        phase=mod_data.get("phase")
                    ))
                
                # Parse requirements
                requirements = []
                for mod_data in rule_data.get("required_modifications", []):
                    requirements.append(ModificationReference(
                        type=mod_data.get("type"),
                        identifier=mod_data.get("identifier"),
                        revision=mod_data.get("revision"),
                        phase=mod_data.get("phase")
                    ))
                
                rules.append(ApplicabilityRule(
                    aircraft_models=rule_data.get("aircraft_models", []),
                    msn_constraint=msn_constraint,
                    excluded_if_modifications=exclusions,
                    required_modifications=requirements
                ))
            
            return AirworthinessDirective(
                ad_id=ad_id,
                issuing_authority=data.get("issuing_authority", "Unknown"),
                effective_date=data.get("effective_date", "Unknown"),
                manufacturer=data.get("manufacturer", "Unknown"),
                applicability_rules=rules,
                raw_applicability_text="Extracted by AI"
            )
            
        except Exception as e:
            print(f"LLM Extraction failed: {e}")
            raise e
