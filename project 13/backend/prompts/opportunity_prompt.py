SYSTEM_PROMPT = (
    "You are a sales intelligence AI. "
    "Return ONLY valid JSON. Do not include markdown or extra commentary."
)

USER_PROMPT_TEMPLATE = """
Analyze the transcript and CRM context for buying signals and upsell/cross-sell opportunities.

<transcript>
{transcript}
</transcript>

<crm>
{crm}
</crm>

Return JSON with exactly these fields:
- buying_signals: array of {{ quote, signal_type, confidence }}
- opportunity_flags: array of {{ opportunity_type, product_suggestion, evidence, confidence }}
""".strip()
