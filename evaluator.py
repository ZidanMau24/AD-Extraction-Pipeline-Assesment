"""
Evaluation engine for determining if aircraft are affected by Airworthiness Directives.

This module implements the core logic for matching aircraft configurations
against AD applicability rules.
"""

from typing import List
from models import (
    AircraftConfiguration,
    AirworthinessDirective,
    ApplicabilityRule,
    EvaluationResult,
    ModificationReference,
    MSNConstraint
)


class ADEvaluator:
    """
    Evaluates whether aircraft configurations are affected by Airworthiness Directives.
    """
    
    def evaluate(
        self, 
        aircraft: AircraftConfiguration, 
        ad: AirworthinessDirective
    ) -> EvaluationResult:
        """
        Evaluate if an aircraft is affected by an AD.
        
        Logic:
        1. Iterate through all applicability rules in the AD
        2. For each rule, check if aircraft matches:
           a. Model must match
           b. MSN must satisfy constraints
           c. Must NOT have excluded modifications
           d. Must HAVE required modifications (if any)
        3. If any rule matches, aircraft is affected
        
        Args:
            aircraft: Aircraft configuration to evaluate
            ad: Airworthiness Directive to check against
            
        Returns:
            EvaluationResult with is_affected flag and explanation
        """
        for idx, rule in enumerate(ad.applicability_rules):
            # Check model match
            if not self._matches_model(aircraft.model, rule.aircraft_models):
                continue
            
            # Check MSN constraint
            if not rule.msn_constraint.matches(aircraft.msn):
                reason = f"MSN {aircraft.msn} does not satisfy constraint: {rule.msn_constraint.type}"
                continue
            
            # Check if excluded by modifications
            if self._is_excluded(aircraft.modifications_applied, rule.excluded_if_modifications):
                excluded_mods = [str(m) for m in rule.excluded_if_modifications 
                                if any(am.matches(m) for am in aircraft.modifications_applied)]
                reason = f"Excluded due to modification(s): {', '.join(excluded_mods)}"
                return EvaluationResult(
                    aircraft=aircraft,
                    ad_id=ad.ad_id,
                    is_affected=False,
                    reason=reason,
                    matched_rule_index=idx
                )
            
            # Check if has required modifications
            if not self._has_required_modifications(
                aircraft.modifications_applied, 
                rule.required_modifications
            ):
                missing_mods = [str(m) for m in rule.required_modifications 
                               if not any(am.matches(m) for am in aircraft.modifications_applied)]
                reason = f"Missing required modification(s): {', '.join(missing_mods)}"
                continue
            
            # All checks passed - aircraft is affected
            reason = f"Matches rule {idx + 1}: {', '.join(rule.aircraft_models)}"
            return EvaluationResult(
                aircraft=aircraft,
                ad_id=ad.ad_id,
                is_affected=True,
                reason=reason,
                matched_rule_index=idx
            )
        
        # No rules matched
        reason = f"Model {aircraft.model} not in applicability or constraints not met"
        return EvaluationResult(
            aircraft=aircraft,
            ad_id=ad.ad_id,
            is_affected=False,
            reason=reason,
            matched_rule_index=None
        )
    
    def _matches_model(self, aircraft_model: str, rule_models: List[str]) -> bool:
        """
        Check if aircraft model matches any of the rule models.
        
        Handles both exact matches and variant matching:
        - "MD-11" matches "MD-11"
        - "A320-214" matches "A320-214"
        - "A320-214" matches "A320" (variant matching)
        - "DC-10-30F" matches "DC-10-30F"
        
        Args:
            aircraft_model: Aircraft model to check (e.g., "A320-214")
            rule_models: List of models in the rule (e.g., ["A320-211", "A320-214"])
            
        Returns:
            True if model matches, False otherwise
        """
        # Normalize models (uppercase, strip whitespace)
        aircraft_model_norm = aircraft_model.upper().strip()
        rule_models_norm = [m.upper().strip() for m in rule_models]
        
        # Check exact match first
        if aircraft_model_norm in rule_models_norm:
            return True
        
        # Check variant matching (e.g., A320-214 should match A320)
        # Extract base model (before first dash)
        aircraft_base = aircraft_model_norm.split('-')[0]
        
        for rule_model in rule_models_norm:
            rule_base = rule_model.split('-')[0]
            
            # If bases match, check if rule model is a prefix of aircraft model
            if aircraft_base == rule_base:
                # A320-214 matches A320
                if aircraft_model_norm.startswith(rule_model):
                    return True
                # A320 matches A320-214 (if rule is more general)
                if rule_model.startswith(aircraft_model_norm):
                    return True
        
        return False
    
    def _is_excluded(
        self, 
        aircraft_mods: List[ModificationReference],
        exclusion_mods: List[ModificationReference]
    ) -> bool:
        """
        Check if aircraft is excluded due to having any of the exclusion modifications.
        
        Args:
            aircraft_mods: Modifications applied to the aircraft
            exclusion_mods: Modifications that exclude the aircraft from the AD
            
        Returns:
            True if aircraft has any exclusion modification, False otherwise
        """
        for exclusion_mod in exclusion_mods:
            for aircraft_mod in aircraft_mods:
                if aircraft_mod.matches(exclusion_mod):
                    return True
        return False
    
    def _has_required_modifications(
        self,
        aircraft_mods: List[ModificationReference],
        required_mods: List[ModificationReference]
    ) -> bool:
        """
        Check if aircraft has all required modifications.
        
        Args:
            aircraft_mods: Modifications applied to the aircraft
            required_mods: Modifications required by the rule
            
        Returns:
            True if aircraft has all required modifications, False otherwise
        """
        # If no required modifications, return True
        if not required_mods:
            return True
        
        # Check that all required mods are present
        for required_mod in required_mods:
            has_mod = any(aircraft_mod.matches(required_mod) for aircraft_mod in aircraft_mods)
            if not has_mod:
                return False
        
        return True
    
    def evaluate_batch(
        self,
        aircraft_list: List[AircraftConfiguration],
        ads: List[AirworthinessDirective]
    ) -> List[EvaluationResult]:
        """
        Evaluate multiple aircraft against multiple ADs.
        
        Args:
            aircraft_list: List of aircraft configurations
            ads: List of Airworthiness Directives
            
        Returns:
            List of evaluation results (one per aircraft-AD pair)
        """
        results = []
        for aircraft in aircraft_list:
            for ad in ads:
                result = self.evaluate(aircraft, ad)
                results.append(result)
        return results
