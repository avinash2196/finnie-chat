def run(text: str, risk: str):
    """
    Appends disclaimer only when risk is MED or HIGH.
    Avoids duplicate disclaimers.
    """
    disclaimer = "(Note: This is educational information, not financial advice.)"
    
    # Don't add if already present
    if disclaimer in text:
        return text

    if risk in ["MED", "HIGH"]:
        return text + "\n\n" + disclaimer

    return text
