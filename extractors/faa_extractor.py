"""
FAA Airworthiness Directive extractor.

Parses FAA AD documents to extract applicability rules.
"""

import re
from typing import List
from models import (
    AirworthinessDirective,
    ApplicabilityRule,
    MSNConstraint,
    ModificationReference
)


class FAAExtractor:
    """
    Extractor for FAA Airworthiness Directives.
    
    FAA ADs typically have a simple structure:
    - List of aircraft models
    - Usually "all" MSNs
    - Rarely have modification exclusions
    """
    
    def extract(self, markdown_text: str, ad_id: str) -> AirworthinessDirective:
        """
        Extract AD rules from FAA markdown text.
        
        Args:
            markdown_text: Markdown content of the AD
            ad_id: AD identifier (e.g., "FAA-2025-23-53")
            
        Returns:
            AirworthinessDirective object
        """
        # Extract applicability section
        applicability_text = self._extract_applicability_section(markdown_text)
        
        # Extract effective date
        effective_date = self._extract_effective_date(markdown_text)
        
        # Extract manufacturer
        manufacturer = self._extract_manufacturer(markdown_text)
        
        # Parse applicability rules
        rules = self._parse_applicability_rules(applicability_text)
        
        return AirworthinessDirective(
            ad_id=ad_id,
            issuing_authority="FAA",
            effective_date=effective_date,
            manufacturer=manufacturer,
            applicability_rules=rules,
            raw_applicability_text=applicability_text
        )
    
    def _extract_applicability_section(self, text: str) -> str:
        """Extract the applicability section from the markdown"""
        # Look for "(c) Applicability" section
        pattern = r'\(c\)\s*Applicability\s*\n+(.*?)(?=\n+##|\n+\([a-z]\)|$)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        # Fallback: look for "## Applicability" or "Applicability:"
        pattern = r'##?\s*Applicability:?\s*\n+(.*?)(?=\n+##|$)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        return ""
    
    def _extract_effective_date(self, text: str) -> str:
        """Extract effective date from the AD"""
        # Look for "effective on <date>" or "Effective Date: <date>"
        patterns = [
            r'effective on\s+([A-Za-z]+ \d+, \d{4})',
            r'Effective Date:?\s*\n+([A-Za-z]+ \d+, \d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "Unknown"
    
    def _extract_manufacturer(self, text: str) -> str:
        """Extract manufacturer from the AD"""
        # Look for "The Boeing Company" or similar
        if "Boeing" in text:
            return "Boeing"
        elif "Airbus" in text:
            return "Airbus"
        else:
            return "Unknown"
    
    def _parse_applicability_rules(self, applicability_text: str) -> List[ApplicabilityRule]:
        """
        Parse applicability rules from the applicability section.
        
        FAA AD 2025-23-53 format:
        (1) Model MD-11 and MD-11F airplanes.
        (2) Model MD-10-10F and MD-10-30F airplanes.
        (3) Model DC-10-10, DC-10-10F, DC-10-15, DC-10-30, DC-10-30F (KC-10A and KDC-10), DC-10-40, and DC-10-40F airplanes.
        """
        rules = []
        
        # Find all numbered paragraphs
        paragraph_pattern = r'\((\d+)\)\s*Model\s+(.*?)\s+airplanes?\.?'
        matches = re.finditer(paragraph_pattern, applicability_text, re.IGNORECASE)
        
        for match in matches:
            models_text = match.group(2)
            
            # Parse model list
            models = self._parse_model_list(models_text)
            
            if models:
                rule = ApplicabilityRule(
                    aircraft_models=models,
                    msn_constraint=MSNConstraint(type="all"),  # FAA typically applies to all MSNs
                    excluded_if_modifications=[],
                    required_modifications=[]
                )
                rules.append(rule)
        
        return rules
    
    def _parse_model_list(self, models_text: str) -> List[str]:
        """
        Parse a comma-separated list of aircraft models.
        
        Examples:
        - "MD-11 and MD-11F" -> ["MD-11", "MD-11F"]
        - "DC-10-10, DC-10-10F, DC-10-15, DC-10-30, DC-10-30F (KC-10A and KDC-10), DC-10-40, and DC-10-40F"
          -> ["DC-10-10", "DC-10-10F", "DC-10-15", "DC-10-30", "DC-10-30F", "KC-10A", "KDC-10", "DC-10-40", "DC-10-40F"]
        """
        # Remove parenthetical content but keep what's inside
        # "(KC-10A and KDC-10)" -> "KC-10A and KDC-10"
        models_text = re.sub(r'\(([^)]+)\)', r'\1', models_text)
        
        # Split by commas and "and"
        models_text = models_text.replace(' and ', ', ')
        
        # Split and clean
        models = [m.strip() for m in models_text.split(',')]
        models = [m for m in models if m and not m.lower() in ['airplanes', 'airplane']]
        
        return models
