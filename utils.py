
def detect_authority(text: str) -> str:
    """
    Detect the issuing authority from the AD text.
    
    Args:
        text: The full text content of the AD.
        
    Returns:
        Detected authority string (e.g., "FAA", "EASA", "TCCA") or "Unknown".
    """
    text_upper = text.upper()
    
    # Check for specific authorities
    if "FEDERAL AVIATION ADMINISTRATION" in text_upper or "FAA" in text_upper:
        return "FAA"
    if "EUROPEAN UNION AVIATION SAFETY AGENCY" in text_upper or "EASA" in text_upper:
        return "EASA"
    if "TRANSPORT CANADA" in text_upper or "TCCA" in text_upper:
        return "TCCA"
    if "CIVIL AVIATION AUTHORITY" in text_upper and ("UK" in text_upper or "UNITED KINGDOM" in text_upper):
        return "CAA_UK"
    if "ANAC" in text_upper:
        return "ANAC"
    if "CIVIL AVIATION SAFETY AUTHORITY" in text_upper or "CASA" in text_upper:
        return "CASA"
    if "CIVIL AVIATION ADMINISTRATION OF CHINA" in text_upper or "CAAC" in text_upper:
        return "CAAC"
    if "CIVIL AVIATION AUTHORITY OF SINGAPORE" in text_upper or "CAAS" in text_upper:
        return "CAAS"
    if "JAPAN CIVIL AVIATION BUREAU" in text_upper or "JCAB" in text_upper:
        return "JCAB"
    if "DIRECTORATE GENERAL OF CIVIL AVIATION" in text_upper and "INDIA" in text_upper:
        return "DGCA_INDIA"
        
    return "Unknown"
