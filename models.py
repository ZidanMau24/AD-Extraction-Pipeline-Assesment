"""
Data models for Airworthiness Directive extraction and evaluation.

This module defines Pydantic models for representing:
- Aircraft configurations
- Modification references
- MSN constraints
- Applicability rules
- Airworthiness Directives
- Evaluation results
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum


class ModificationReference(BaseModel):
    """
    Reference to a modification or service bulletin.
    
    Examples:
    - Production modification: ModificationReference(type="mod", identifier="24591", phase="production")
    - Service bulletin: ModificationReference(type="sb", identifier="A320-57-1089", revision="04", phase="service")
    """
    type: Literal["mod", "sb"]  # modification or service bulletin
    identifier: str  # e.g., "24591", "A320-57-1089"
    revision: Optional[str] = None  # e.g., "04"
    phase: Optional[Literal["production", "service"]] = None
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        parts = [self.type.upper(), self.identifier]
        if self.revision:
            parts.append(f"Rev {self.revision}")
        if self.phase:
            parts.append(f"({self.phase})")
        return " ".join(parts)
    
    def matches(self, other: "ModificationReference") -> bool:
        """
        Check if this modification matches another.
        
        Matching rules:
        - Type must match
        - Identifier must match
        - If revision is specified in both, they must match
        - Phase is optional for matching
        """
        if self.type != other.type or self.identifier != other.identifier:
            return False
        
        # If both have revisions, they must match
        if self.revision and other.revision:
            return self.revision == other.revision
        
        # If only one has revision, still consider it a match
        return True


class MSNConstraint(BaseModel):
    """
    Manufacturer Serial Number constraints.
    
    Types:
    - "all": All MSNs (no constraint)
    - "range": MSN must be within [min_msn, max_msn]
    - "specific": MSN must be in specific_msns list
    """
    type: Literal["all", "range", "specific"]
    min_msn: Optional[int] = None
    max_msn: Optional[int] = None
    specific_msns: Optional[List[int]] = None
    
    def matches(self, msn: int) -> bool:
        """Check if a given MSN satisfies this constraint"""
        if self.type == "all":
            return True
        elif self.type == "range":
            if self.min_msn is not None and msn < self.min_msn:
                return False
            if self.max_msn is not None and msn > self.max_msn:
                return False
            return True
        elif self.type == "specific":
            return msn in (self.specific_msns or [])
        return False


class ApplicabilityRule(BaseModel):
    """
    Applicability rule for a group of aircraft.
    
    An aircraft is affected by this rule if:
    1. Its model matches one of aircraft_models
    2. Its MSN satisfies msn_constraint
    3. It does NOT have any of the excluded_if_modifications
    4. It HAS all of the required_modifications (if any)
    """
    aircraft_models: List[str]  # e.g., ["MD-11", "MD-11F"]
    msn_constraint: MSNConstraint
    excluded_if_modifications: List[ModificationReference] = Field(default_factory=list)
    required_modifications: List[ModificationReference] = Field(default_factory=list)
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        models = ", ".join(self.aircraft_models)
        parts = [f"Models: {models}"]
        
        if self.msn_constraint.type != "all":
            parts.append(f"MSN: {self.msn_constraint.type}")
        
        if self.excluded_if_modifications:
            exclusions = ", ".join(str(m) for m in self.excluded_if_modifications)
            parts.append(f"Excluded if: {exclusions}")
        
        if self.required_modifications:
            required = ", ".join(str(m) for m in self.required_modifications)
            parts.append(f"Required: {required}")
        
        return " | ".join(parts)


class AirworthinessDirective(BaseModel):
    """
    Complete Airworthiness Directive with metadata and applicability rules.
    """
    ad_id: str  # e.g., "FAA-2025-23-53"
    issuing_authority: Literal["FAA", "EASA"]
    effective_date: str
    manufacturer: str
    applicability_rules: List[ApplicabilityRule]
    raw_applicability_text: str  # Keep original for reference
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        return f"{self.ad_id} ({self.issuing_authority}) - {self.manufacturer} - {len(self.applicability_rules)} rule(s)"


class AircraftConfiguration(BaseModel):
    """
    Aircraft configuration to evaluate against ADs.
    
    Example:
    AircraftConfiguration(
        model="A320-214",
        msn=4500,
        modifications_applied=[
            ModificationReference(type="mod", identifier="24591", phase="production")
        ]
    )
    """
    model: str
    msn: int
    modifications_applied: List[ModificationReference] = Field(default_factory=list)
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        mods = f" with {len(self.modifications_applied)} mod(s)" if self.modifications_applied else ""
        return f"{self.model} MSN {self.msn}{mods}"
    
    def has_modification(self, mod: ModificationReference) -> bool:
        """Check if this aircraft has a specific modification"""
        return any(applied_mod.matches(mod) for applied_mod in self.modifications_applied)


class EvaluationResult(BaseModel):
    """
    Result of evaluating an aircraft configuration against an AD.
    """
    aircraft: AircraftConfiguration
    ad_id: str
    is_affected: bool
    reason: str  # Explanation of why affected or not
    matched_rule_index: Optional[int] = None  # Index of the rule that matched
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        status = "✅ AFFECTED" if self.is_affected else "❌ NOT AFFECTED"
        return f"{self.aircraft} | {self.ad_id}: {status} - {self.reason}"
