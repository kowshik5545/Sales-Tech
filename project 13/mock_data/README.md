# mock_data/

Place your demo audio files here. The pipeline smoke test and demo script
expect at minimum:

```
mock_data/
└── sample_call.mp3   ← primary demo file (3–5 minutes, clear English)
```

## Requirements

| Property | Value |
|---|---|
| Format | MP3 or WAV |
| Language | English |
| Duration | 2–5 minutes |
| Max size | 25 MB |
| Content | A simulated B2B sales call between a Rep and a Customer |

## Suggested Script Outline

The mock call should include the following elements so every pipeline output is
populated meaningfully:

1. **Opening / Rapport** — Rep introduces themselves and builds rapport (tested by Coach node).
2. **Discovery** — Customer mentions at least 2 pain points, e.g. "manual reporting" and
   "team onboarding time" (used by CRM and Email nodes).
3. **Buying Signal** — Customer says something like "budget has been approved" or "we need
   to solve this by Q3" (used by Opportunity node).
4. **Upsell Hook** — Customer mentions an adjacent need, e.g. "better analytics" (used by
   Opportunity node for cross-sell/upsell flag).
5. **Next Steps** — Rep confirms a concrete action, e.g. "I'll send the pricing deck by
   Friday" (used by CRM `next_steps` and Email body).
6. **Close** — Rep wraps up professionally (tested by Coach rubric).

## Recording Tips

- Use a quiet environment — background noise degrades STT accuracy.
- Clearly distinguish speakers (different voices help the STT provider diarize).
- Aim for 85 %+ word accuracy with the configured `LITELLM_STT_MODEL`.

## Fallback Behaviour

If this folder is empty or `sample_call.mp3` is not present, the transcription
agent automatically returns a **mock transcript** with realistic content so that
the full pipeline can still run end-to-end without real audio. This is the
default behaviour in local development before LiteLLM credentials are configured.
