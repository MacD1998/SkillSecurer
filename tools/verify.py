from langchain_core.tools import tool

@tool
def verify_quotes(quotes: list, content: str) -> dict:
    """Verifies that exact quotes exist in the file content.
    Call this ALWAYS before reporting findings — pass all quotes at once.
    Returns VERIFIED, PARTIALLY VERIFIED, or NOT FOUND for each quote."""
    results = {}
    c = content.lower()
    for quote in quotes:
        q = quote.strip().lower()
        if q in c:
            results[quote] = "VERIFIED"
        elif q[:40] in c:
            results[quote] = "PARTIALLY VERIFIED"
        else:
            results[quote] = "NOT FOUND — do not report this finding"
    return results
