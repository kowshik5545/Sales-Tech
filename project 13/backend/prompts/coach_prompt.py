SYSTEM_PROMPT = (
    "You are an expert sales coach. "
    "Score exactly 5 dimensions. "
    "Return ONLY valid JSON. Do not include markdown or extra commentary."
)

USER_PROMPT_TEMPLATE = """
Review the transcript and produce coaching feedback.

<transcript>
{transcript}
</transcript>

<crm>
{crm}
</crm>

<talk_ratio>
rep={talk_ratio_rep}, customer={talk_ratio_customer}
</talk_ratio>

Return JSON with exactly these fields:
- rubric_scores: array of 5 items {{ dimension, score, comment }}
- talk_ratio_rep: number
- talk_ratio_customer: number
- strengths: string[]
- areas_to_improve: string[]
- recommended_actions: string[]
""".strip()
