"""
EASA Airworthiness Directive extractor.

Parses EASA AD documents to extract applicability rules with modification exclusions.
"""

import re
from typing import List, Tuple
from models import (
    AirworthinessDirective,
    ApplicabilityRule,
    MSNConstraint,
    ModificationReference
)


class EASAExtractor:
    """
    Extractor for EASA Airworthiness Directives.
    
    EASA ADs often have complex applicability with:
    - Multiple aircraft model variants
    - Modification exclusions
    - Production vs service modifications
    """
    
    def extract(self, markdown_text: str, ad_id: str) -> AirworthinessDirective:
        """
        Extract AD rules from EASA markdown text.
        
        Args:
            markdown_text: Markdown content of the AD
            ad_id: AD identifier (e.g., "EASA-2025-0254")
            
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
            issuing_authority="EASA",
            effective_date=effective_date,
            manufacturer=manufacturer,
            applicability_rules=rules,
            raw_applicability_text=applicability_text
        )
    
    def _extract_applicability_section(self, text: str) -> str:
        """Extract the applicability section from the markdown"""
        # Look for "## Applicability:" section
        pattern = r'##\s*Applicability:?\s*\n+(.*?)(?=\n+##|$)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        return ""
    
    def _extract_effective_date(self, text: str) -> str:
        """Extract effective date from the AD"""
        # Look for "Effective Date:" or "Issued:"
        patterns = [
            r'Effective Date:?\s*\n+.*?(\d{2} [A-Za-z]+ \d{4})',
            r'Issued:?\s*\n+(\d{2} [A-Za-z]+ \d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "Unknown"
    
    def _extract_manufacturer(self, text: str) -> str:
        """Extract manufacturer from the AD"""
        if "AIRBUS" in text.upper():
            return "Airbus"
        elif "BOEING" in text.upper():
            return "Boeing"
        else:
            return "Unknown"
    
    def _parse_applicability_rules(self, applicability_text: str) -> List[ApplicabilityRule]:
        """
        Parse applicability rules from the applicability section.
        
        EASA AD 2025-0254 format:
        Airbus A320-211, A320-212, A320-214, ..., all manufacturer serial numbers (MSN), 
        except those on which Airbus modification (mod) 24591 has been embodied in production 
        and except those on which have Airbus Service Bulletin (SB) A320-57-1089 at Revision 04 
        has been embodied in service;
        
        and
        
        Airbus A321-111, A321-112 and A321-131, all MSN, 
        except those on which Airbus mod 24977 has been embodied in production.
        """
        rules = []
        
        # Split by "and" at the beginning of lines (separates different aircraft families)
        sections = re.split(r'\n+and\s*\n+', applicability_text)
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # Parse this section
            rule = self._parse_applicability_section(section)
            if rule:
                rules.append(rule)
        
        return rules
    
    def _parse_applicability_section(self, section: str) -> ApplicabilityRule:
        """
        Parse a single applicability section.
        
        Format:
        Airbus A320-211, A320-212, ..., all MSN, except those on which mod X ... and except those on which SB Y ...
        """
        # Extract aircraft models
        models = self._extract_models(section)
        
        # Extract MSN constraint
        msn_constraint = self._extract_msn_constraint(section)
        
        # Extract exclusions
        exclusions = self._extract_exclusions(section)
        
        return ApplicabilityRule(
            aircraft_models=models,
            msn_constraint=msn_constraint,
            excluded_if_modifications=exclusions,
            required_modifications=[]
        )
    
    def _extract_models(self, section: str) -> List[str]:
        """
        Extract aircraft models from a section.
        
        Example: "Airbus A320-211, A320-212, A320-214" -> ["A320-211", "A320-212", "A320-214"]
        """
        # Find text before "all manufacturer serial numbers" or "all MSN"
        match = re.search(r'Airbus\s+(.*?),?\s+all\s+(?:manufacturer serial numbers|MSN)', section, re.IGNORECASE)
        
        if not match:
            return []
        
        models_text = match.group(1)
        
        # Split by commas and "and"
        models_text = models_text.replace(' and ', ', ')
        models = [m.strip() for m in models_text.split(',')]
        models = [m for m in models if m and not m.lower() in ['aeroplanes', 'aeroplane', 'airplanes', 'airplane']]
        
        return models
    
    def _extract_msn_constraint(self, section: str) -> MSNConstraint:
        """
        Extract MSN constraint from a section.
        
        Currently only handles "all MSN" - could be extended for ranges.
        """
        if re.search(r'all\s+(?:manufacturer serial numbers|MSN)', section, re.IGNORECASE):
            return MSNConstraint(type="all")
        
        # Could add range parsing here if needed
        return MSNConstraint(type="all")
    
    def _extract_exclusions(self, section: str) -> List[ModificationReference]:
        """
        Extract modification exclusions from a section.
        
        Examples:
        - "except those on which Airbus modification (mod) 24591 has been embodied in production"
        - "except those on which have Airbus Service Bulletin (SB) A320-57-1089 at Revision 04 has been embodied in service"
        """
        exclusions = []
        
        # Pattern for modifications: "mod XXXXX" or "modification XXXXX"
        mod_pattern = r'(?:modification|mod)\s+(?:\(mod\)\s+)?(\d+)\s+has been embodied in (production|service)'
        for match in re.finditer(mod_pattern, section, re.IGNORECASE):
            mod_id = match.group(1)
            phase = match.group(2).lower()
            
            exclusions.append(ModificationReference(
                type="mod",
                identifier=mod_id,
                phase=phase
            ))
        
        # Pattern for service bulletins: "SB A320-57-1089 at Revision 04"
        sb_pattern = r'Service Bulletin\s+\(SB\)\s+([\w-]+)(?:\s+at\s+Revision\s+(\d+))?\s+has been embodied in (production|service)'
        for match in re.finditer(sb_pattern, section, re.IGNORECASE):
            sb_id = match.group(1)
            revision = match.group(2)
            phase = match.group(3).lower()
            
            exclusions.append(ModificationReference(
                type="sb",
                identifier=sb_id,
                revision=revision,
                phase=phase
            ))
        
        return exclusions
