SYSTEM_PROMPT = (
    "You are an expert B2B sales email writer. "
    "Return ONLY valid JSON. Do not include markdown or extra commentary."
)

USER_PROMPT_TEMPLATE = """
Create a personalized follow-up email.

<transcript>
{transcript}
</transcript>

<crm>
{crm}
</crm>

<opportunities>
{opportunities}
</opportunities>

Return JSON with exactly these fields:
- subject: string
- body: string
""".strip()
