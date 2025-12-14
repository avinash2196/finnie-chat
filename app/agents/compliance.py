def run(text: str, risk: str):
    """
    Appends disclaimer only when risk is MED or HIGH.
    """

    if risk in ["MED", "HIGH"]:
        return (
            text
            + "\n\n(Note: This is educational information, not financial advice.)"
        )

    return text
