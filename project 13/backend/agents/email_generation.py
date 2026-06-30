from __future__ import annotations

import logging
import os
import smtplib
import ssl
from email.mime.text import MIMEText

from agents.client import call_llm_json_with_retry, get_litellm_client, get_llm_model
from models.schemas import CRMRecord, EmailDraft, OpportunityReport, TranscriptOutput
from prompts.email_prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


def _get_smtp_config() -> dict[str, str] | None:
    host = os.getenv("SMTP_HOST")
    port = os.getenv("SMTP_PORT", "587")
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM_EMAIL")
    if not all([host, username, password, from_email]):
        return None
    return {
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "from_email": from_email,
    }


def send_email_smtp(to_email: str, subject: str, body: str) -> bool:
    config = _get_smtp_config()
    if not config:
        logger.info("SMTP not configured — skipping send")
        return False

    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = config["from_email"]
    msg["To"] = to_email

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(config["host"], int(config["port"]), timeout=15) as server:
            server.starttls(context=context)
            server.login(config["username"], config["password"])
            server.sendmail(config["from_email"], [to_email], msg.as_string())
        logger.info("Email sent to %s — %s", to_email, subject)
        return True
    except Exception as exc:
        logger.warning("SMTP send failed: %s", exc)
        return False


async def generate_email(
    transcript: TranscriptOutput,
    crm: CRMRecord,
    opportunities: OpportunityReport,
) -> EmailDraft:
    client = get_litellm_client()

    if client:
        user_prompt = USER_PROMPT_TEMPLATE.format(
            transcript=transcript.full_text,
            crm=crm.model_dump_json(indent=2),
            opportunities=opportunities.model_dump_json(indent=2),
        )
        draft = call_llm_json_with_retry(
            client=client,
            model=get_llm_model(),
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            validator=EmailDraft.model_validate,
            temperature=0.3,
        )
    else:
        draft = EmailDraft(
            subject=f"Next Steps from Our Call — {crm.company}",
            body=(
                f"Hi {crm.contact_name},\n\n"
                "Thanks again for the call today. I appreciated your transparency around manual reporting "
                "and analytics visibility challenges.\n\n"
                f"As agreed, next steps are: {crm.next_steps}\n\n"
                "Best regards,\nSales Rep"
            ),
        )

    if crm.contact_email:
        sent = send_email_smtp(crm.contact_email, draft.subject, draft.body)
        if not sent:
            logger.warning("Email queued but SMTP delivery failed for %s", crm.contact_email)

    return draft
