"""5 comprehensive sales call scenarios for testing all pipeline stages."""

from datetime import date

from models.schemas import (
    CRMRecord,
    CoachingReport,
    EmailDraft,
    OpportunityReport,
    TranscriptOutput,
    TranscriptSegment,
)

# ─────────────────────────────────────────────────────────
# Scenario 1: Discovery Call — Acme Corp
# ─────────────────────────────────────────────────────────

DISCOVERY_SEGMENTS = [
    TranscriptSegment(speaker="Rep", timestamp_start=0.0, timestamp_end=7.0, text="Hi Sarah, thanks for the time today. I understand you've been looking into analytics solutions?"),
    TranscriptSegment(speaker="Customer", timestamp_start=7.0, timestamp_end=15.0, text="Yes, we're evaluating options. Our team spends 20+ hours a week on manual reporting."),
    TranscriptSegment(speaker="Rep", timestamp_start=15.0, timestamp_end=25.0, text="That's significant. What are the main pain points driving this evaluation?"),
    TranscriptSegment(speaker="Customer", timestamp_start=25.0, timestamp_end=36.0, text="Data silos between departments, no real-time dashboards, and our execs want better visibility into sales metrics."),
    TranscriptSegment(speaker="Rep", timestamp_start=36.0, timestamp_end=44.0, text="We've solved this for similar companies. Do you have a budget allocated for this initiative?"),
    TranscriptSegment(speaker="Customer", timestamp_start=44.0, timestamp_end=52.0, text="Roughly $50k approved for Q3. We need to see a demo before committing."),
    TranscriptSegment(speaker="Rep", timestamp_start=52.0, timestamp_end=60.0, text="Perfect. I'll set up a demo for next week and send over some case studies in the meantime."),
]

DISCOVERY_CRM = CRMRecord(
    contact_name="Sarah Chen",
    contact_email="sarah.chen@acmecorp.com",
    company="Acme Corp",
    deal_stage="Discovery",
    pain_points=["manual reporting", "data silos", "no real-time dashboards", "lack of exec visibility"],
    next_steps="Send case studies, schedule demo for next week, share pricing overview.",
    call_date=date.today().isoformat(),
)

DISCOVERY_OPPORTUNITY = OpportunityReport.model_validate({
    "buying_signals": [
        {"quote": "$50k approved for Q3", "signal_type": "budget_confirmed", "confidence": 0.92},
        {"quote": "We need to see a demo before committing", "signal_type": "decision_timeline", "confidence": 0.78},
        {"quote": "Our execs want better visibility", "signal_type": "executive_involvement", "confidence": 0.85},
    ],
    "opportunity_flags": [
        {"opportunity_type": "upsell", "product_suggestion": "Enterprise Analytics Suite", "evidence": "Multiple departments need cross-functional dashboards.", "confidence": 0.88},
        {"opportunity_type": "cross-sell", "product_suggestion": "Real-time Reporting Add-on", "evidence": "Customer explicitly mentioned real-time dashboards as a need.", "confidence": 0.76},
    ],
})

DISCOVERY_EMAIL = EmailDraft(
    subject="Next Steps — Analytics Evaluation at Acme Corp",
    body="Hi Sarah,\n\nThanks again for the call today. I really appreciate you walking me through Acme Corp's reporting challenges.\n\nKey takeaways:\n- 20+ hours/week lost to manual reporting\n- Data silos across departments\n- $50k budget approved for Q3\n\nAs discussed, I'll send over a few case studies from similar companies and set up a demo for next week.\n\nBest regards,\nSales Rep",
)

DISCOVERY_COACH = CoachingReport.model_validate({
    "rubric_scores": [
        {"dimension": "Opening & Rapport Building", "score": 8, "comment": "Warm opening, established context quickly."},
        {"dimension": "Discovery & Needs Analysis", "score": 9, "comment": "Excellent probing on pain points and budget."},
        {"dimension": "Objection Handling", "score": 6, "comment": "Could have addressed timeline concerns more directly."},
        {"dimension": "Closing & Next Steps", "score": 8, "comment": "Clear demo commitment and follow-up plan."},
        {"dimension": "Active Listening", "score": 7, "comment": "Good paraphrasing of customer needs."},
    ],
    "talk_ratio_rep": 48.0,
    "talk_ratio_customer": 52.0,
    "strengths": ["Structured discovery process", "Budget qualification was strong", "Clear next steps defined"],
    "areas_to_improve": ["Probe deeper on decision criteria", "Address competitor positioning"],
    "recommended_actions": ["Prepare a competitive comparison for demo", "Share relevant case studies before next call"],
})

# ─────────────────────────────────────────────────────────
# Scenario 2: Demo Call — BetaTech Solutions
# ─────────────────────────────────────────────────────────

DEMO_SEGMENTS = [
    TranscriptSegment(speaker="Rep", timestamp_start=0.0, timestamp_end=8.0, text="Welcome to the demo, Mark. I'll walk you through the Analytics Dashboard and Reporting Suite."),
    TranscriptSegment(speaker="Customer", timestamp_start=8.0, timestamp_end=16.0, text="Great, our team is particularly interested in the real-time collaboration features."),
    TranscriptSegment(speaker="Rep", timestamp_start=16.0, timestamp_end=30.0, text="Let me show you the live dashboard. You can see here how data refreshes automatically every 30 seconds across all departments."),
    TranscriptSegment(speaker="Customer", timestamp_start=30.0, timestamp_end=40.0, text="That's impressive. Can we integrate this with our existing Salesforce instance?"),
    TranscriptSegment(speaker="Rep", timestamp_start=40.0, timestamp_end=52.0, text="Absolutely. We have a native Salesforce connector. Let me show you the integration setup."),
    TranscriptSegment(speaker="Customer", timestamp_start=52.0, timestamp_end=63.0, text="This is exactly what we need. Can we start a 30-day trial for our sales team of 50?"),
    TranscriptSegment(speaker="Rep", timestamp_start=63.0, timestamp_end=72.0, text="Of course. I'll set up the trial today and schedule training for your team next week."),
]

DEMO_CRM = CRMRecord(
    contact_name="Mark Johnson",
    contact_email="mark.j@betatech.io",
    company="BetaTech Solutions",
    deal_stage="Demo",
    pain_points=["no real-time collaboration", "manual Salesforce reporting", "limited visibility for sales leadership"],
    next_steps="Activate 30-day trial, schedule team training, provide Salesforce integration guide.",
    call_date=date.today().isoformat(),
)

DEMO_OPPORTUNITY = OpportunityReport.model_validate({
    "buying_signals": [
        {"quote": "This is exactly what we need", "signal_type": "positive_reaction", "confidence": 0.95},
        {"quote": "Can we start a 30-day trial for our sales team of 50", "signal_type": "commitment_request", "confidence": 0.91},
        {"quote": "Can we integrate with Salesforce", "signal_type": "technical_validation", "confidence": 0.72},
    ],
    "opportunity_flags": [
        {"opportunity_type": "upsell", "product_suggestion": "Premium Support Package", "evidence": "50-person team deployment will need dedicated support.", "confidence": 0.84},
        {"opportunity_type": "cross-sell", "product_suggestion": "Advanced Analytics AI Module", "evidence": "Customer is tech-forward and interested in automation.", "confidence": 0.69},
    ],
})

DEMO_EMAIL = EmailDraft(
    subject="Your BetaTech Demo Recap & Trial Access",
    body="Hi Mark,\n\nThanks for joining the demo today. I'm glad the Analytics Dashboard resonated with your team.\n\nHere's what's next:\n1. 30-day trial activated for 50 users\n2. Salesforce integration guide attached\n3. Training session scheduled for next Tuesday\n\nLet me know if you have any questions getting started.\n\nBest,\nSales Rep",
)

DEMO_COACH = CoachingReport.model_validate({
    "rubric_scores": [
        {"dimension": "Opening & Rapport Building", "score": 7, "comment": "Good demo setup, could have been more personalized."},
        {"dimension": "Discovery & Needs Analysis", "score": 7, "comment": "Addressed key requirements but missed some stakeholder details."},
        {"dimension": "Objection Handling", "score": 9, "comment": "Handled Salesforce integration question smoothly with live demo."},
        {"dimension": "Closing & Next Steps", "score": 9, "comment": "Excellent trial activation and training commitment."},
        {"dimension": "Active Listening", "score": 8, "comment": "Adapted demo flow based on customer reactions."},
    ],
    "talk_ratio_rep": 55.0,
    "talk_ratio_customer": 45.0,
    "strengths": ["Live demo skills excellent", "Smooth integration objection handling", "Proactive trial setup"],
    "areas_to_improve": ["Slow down during demo walkthrough", "Ask more qualifying questions before diving in"],
    "recommended_actions": ["Prepare a shorter demo option", "Create a competitive battle card for features"],
})

# ─────────────────────────────────────────────────────────
# Scenario 3: Negotiation Call — GlobalTech Industries
# ─────────────────────────────────────────────────────────

NEGOTIATION_SEGMENTS = [
    TranscriptSegment(speaker="Rep", timestamp_start=0.0, timestamp_end=8.0, text="Thanks for circling back, Priya. I understand you've reviewed the proposal with your procurement team."),
    TranscriptSegment(speaker="Customer", timestamp_start=8.0, timestamp_end=18.0, text="Yes, we're interested but the pricing is higher than expected. We have a competing offer 20% lower."),
    TranscriptSegment(speaker="Rep", timestamp_start=18.0, timestamp_end=30.0, text="I appreciate the transparency. Let me walk through the value drivers that justify our pricing before we discuss adjustments."),
    TranscriptSegment(speaker="Customer", timestamp_start=30.0, timestamp_end=42.0, text="We do see the value in the analytics features, but we need to stay within budget. Can you do 15% off the annual plan?"),
    TranscriptSegment(speaker="Rep", timestamp_start=42.0, timestamp_end=55.0, text="I can offer 10% off for an annual commitment plus two free training sessions. That's $18k savings versus month-to-month."),
    TranscriptSegment(speaker="Customer", timestamp_start=55.0, timestamp_end=65.0, text="That works if you add the premium support package at no extra cost for the first quarter."),
    TranscriptSegment(speaker="Rep", timestamp_start=65.0, timestamp_end=74.0, text="Deal. I'll draft the revised contract and send it over today for e-signature."),
]

NEGOTIATION_CRM = CRMRecord(
    contact_name="Priya Patel",
    contact_email="priya.p@globaltech.com",
    company="GlobalTech Industries",
    deal_stage="Negotiation",
    pain_points=["budget constraints", "competitive pressure", "need for premium support"],
    next_steps="Send revised contract with 10% annual discount, include premium support Q1 trial, schedule legal review.",
    call_date=date.today().isoformat(),
)

NEGOTIATION_OPPORTUNITY = OpportunityReport.model_validate({
    "buying_signals": [
        {"quote": "We do see the value in the analytics features", "signal_type": "value_acknowledgment", "confidence": 0.88},
        {"quote": "Can you do 15% off the annual plan", "signal_type": "negotiation_engagement", "confidence": 0.93},
        {"quote": "That works if you add premium support", "signal_type": "conditional_agreement", "confidence": 0.96},
    ],
    "opportunity_flags": [
        {"opportunity_type": "upsell", "product_suggestion": "Premium Support Package", "evidence": "Customer explicitly requested premium support in negotiation.", "confidence": 0.97},
        {"opportunity_type": "cross-sell", "product_suggestion": "Implementation Consulting", "evidence": "Enterprise deployment at GlobalTech will need implementation support.", "confidence": 0.74},
    ],
})

NEGOTIATION_EMAIL = EmailDraft(
    subject="Revised Proposal — GlobalTech Industries",
    body="Hi Priya,\n\nThank you for the productive discussion today. As agreed, here's the revised proposal:\n\n- Annual Analytics Suite license: 10% discount\n- Premium Support Package: complimentary for Q1\n- Two free training sessions\n- Total savings vs. month-to-month: $18,000\n\nI've attached the revised contract for e-signature. Please let me know if legal has any questions.\n\nLooking forward to partnering with GlobalTech.\n\nBest,\nSales Rep",
)

NEGOTIATION_COACH = CoachingReport.model_validate({
    "rubric_scores": [
        {"dimension": "Opening & Rapport Building", "score": 8, "comment": "Professional opening, acknowledged procurement process."},
        {"dimension": "Discovery & Needs Analysis", "score": 7, "comment": "Understood competing offer but didn't explore full decision criteria."},
        {"dimension": "Objection Handling", "score": 9, "comment": "Excellent value justification before discussing price. Used 'feel-felt-found' framework."},
        {"dimension": "Closing & Next Steps", "score": 10, "comment": "Perfect close — tied concessions to commitment, clear next steps."},
        {"dimension": "Active Listening", "score": 8, "comment": "Addressed specific concerns and countered with tailored offer."},
    ],
    "talk_ratio_rep": 53.0,
    "talk_ratio_customer": 47.0,
    "strengths": ["Strong objection handling skills", "Creative deal structuring", "Excellent closing technique"],
    "areas_to_improve": ["Qualify competing offers earlier in the process", "Prepare discount authority limits in advance"],
    "recommended_actions": ["Create a negotiation playbook for common objections", "Role-play discount scenarios with the team"],
})

# ─────────────────────────────────────────────────────────
# Scenario 4: Follow-up Call — GreenLeaf Analytics
# ─────────────────────────────────────────────────────────

FOLLOWUP_SEGMENTS = [
    TranscriptSegment(speaker="Rep", timestamp_start=0.0, timestamp_end=7.0, text="Hi James, just checking in. It's been two weeks since you started the trial — how's everything going?"),
    TranscriptSegment(speaker="Customer", timestamp_start=7.0, timestamp_end=16.0, text="Really well, actually. My team has been using the dashboards daily. The onboarding was smooth."),
    TranscriptSegment(speaker="Rep", timestamp_start=16.0, timestamp_end=27.0, text="Great to hear. Have you had a chance to explore the advanced reporting features? There are some powerful templates."),
    TranscriptSegment(speaker="Customer", timestamp_start=27.0, timestamp_end=37.0, text="Not yet, we've been focused on the basics. But I'd like to see what else is possible. Can we schedule a deeper walkthrough?"),
    TranscriptSegment(speaker="Rep", timestamp_start=37.0, timestamp_end=46.0, text="Absolutely. Also, I noticed your usage stats are strong. Would your leadership team benefit from an exec dashboard?"),
    TranscriptSegment(speaker="Customer", timestamp_start=46.0, timestamp_end=58.0, text="Great idea. Our VP of Sales has been asking for better visibility. If you can show that, it'll help justify full rollout."),
    TranscriptSegment(speaker="Rep", timestamp_start=58.0, timestamp_end=68.0, text="Perfect. I'll prepare an executive summary dashboard demo for next week and include ROI projections for full deployment."),
]

FOLLOWUP_CRM = CRMRecord(
    contact_name="James Wilson",
    contact_email="j.wilson@greenleaf.io",
    company="GreenLeaf Analytics",
    deal_stage="Follow-up",
    pain_points=["need for executive dashboards", "limited feature utilization", "justification for full rollout"],
    next_steps="Schedule advanced features walkthrough, prepare exec dashboard demo with ROI projections, share usage analytics report.",
    call_date=date.today().isoformat(),
)

FOLLOWUP_OPPORTUNITY = OpportunityReport.model_validate({
    "buying_signals": [
        {"quote": "My team has been using the dashboards daily", "signal_type": "strong_adoption", "confidence": 0.94},
        {"quote": "It'll help justify full rollout", "signal_type": "expansion_intent", "confidence": 0.89},
        {"quote": "Our VP of Sales has been asking for better visibility", "signal_type": "executive_sponsorship", "confidence": 0.82},
    ],
    "opportunity_flags": [
        {"opportunity_type": "upsell", "product_suggestion": "Executive Dashboard Suite", "evidence": "VP of Sales needs visibility — exec dashboard is a natural upsell.", "confidence": 0.91},
        {"opportunity_type": "cross-sell", "product_suggestion": "Advanced Reporting Templates", "evidence": "Customer hasn't explored advanced features yet, represents expansion opportunity.", "confidence": 0.77},
    ],
})

FOLLOWUP_EMAIL = EmailDraft(
    subject="GreenLeaf Trial Check-in & Next Steps",
    body="Hi James,\n\nGreat catching up today. I'm thrilled to hear the team is finding value in the dashboards.\n\nHere's our plan:\n1. Advanced features walkthrough — let's find a time next week\n2. Executive dashboard demo with ROI projections for your VP of Sales\n3. Usage analytics report attached — your team's adoption is in the top 10% of trial users\n\nLet me know what works for the walkthrough.\n\nBest,\nSales Rep",
)

FOLLOWUP_COACH = CoachingReport.model_validate({
    "rubric_scores": [
        {"dimension": "Opening & Rapport Building", "score": 9, "comment": "Warm, personalized check-in referencing trial start."},
        {"dimension": "Discovery & Needs Analysis", "score": 8, "comment": "Identified expansion opportunity through feature usage conversation."},
        {"dimension": "Objection Handling", "score": 7, "comment": "No objections raised but proactively addressed potential value concerns."},
        {"dimension": "Closing & Next Steps", "score": 9, "comment": "Brilliant — tied usage data to exec dashboard need and ROI justification."},
        {"dimension": "Active Listening", "score": 8, "comment": "Picked up on the VP of Sales mention and turned it into an opportunity."},
    ],
    "talk_ratio_rep": 45.0,
    "talk_ratio_customer": 55.0,
    "strengths": ["Great relationship building", "Proactive account expansion", "Data-driven conversation"],
    "areas_to_improve": ["Introduce advanced features earlier in trials", "Share usage stats earlier to build momentum"],
    "recommended_actions": ["Create a trial engagement playbook with milestone checkpoints", "Prepare executive summary templates for champions"],
})

# ─────────────────────────────────────────────────────────
# Scenario 5: Objection Handling Call — NovaTech Systems
# ─────────────────────────────────────────────────────────

OBJECTION_SEGMENTS = [
    TranscriptSegment(speaker="Rep", timestamp_start=0.0, timestamp_end=8.0, text="Thanks for being upfront, David. You mentioned concerns about the implementation timeline."),
    TranscriptSegment(speaker="Customer", timestamp_start=8.0, timestamp_end=18.0, text="Right. Our last vendor took 6 months to deploy and it was a nightmare. We can't afford that again."),
    TranscriptSegment(speaker="Rep", timestamp_start=18.0, timestamp_end=30.0, text="I completely understand. Our average deployment is 3 weeks, not months. We have a dedicated onboarding team and a proven implementation playbook."),
    TranscriptSegment(speaker="Customer", timestamp_start=30.0, timestamp_end=42.0, text="3 weeks? That's hard to believe. What about data migration? We have 5 years of historical data."),
    TranscriptSegment(speaker="Rep", timestamp_start=42.0, timestamp_end=55.0, text="We handle migration as part of onboarding. Our automated migration tool has moved 10+ PB of data. I can share case studies from companies your size."),
    TranscriptSegment(speaker="Customer", timestamp_start=55.0, timestamp_end=65.0, text="Alright, that addresses my main concern. If you can guarantee the 3-week timeline in the contract, I'll move forward."),
    TranscriptSegment(speaker="Rep", timestamp_start=65.0, timestamp_end=74.0, text="We can include timeline guarantees with service credits if we miss it. Let me draft that SLA language for the contract."),
]

OBJECTION_CRM = CRMRecord(
    contact_name="David Kim",
    contact_email="d.kim@novatech.io",
    company="NovaTech Systems",
    deal_stage="Objection Handling",
    pain_points=["past vendor trauma", "implementation timeline fears", "data migration concerns", "trust rebuilding"],
    next_steps="Draft SLA with 3-week deployment guarantee, share migration case studies, include service credit terms.",
    call_date=date.today().isoformat(),
)

OBJECTION_OPPORTUNITY = OpportunityReport.model_validate({
    "buying_signals": [
        {"quote": "If you can guarantee the 3-week timeline, I'll move forward", "signal_type": "conditional_commitment", "confidence": 0.97},
        {"quote": "3 weeks? That's hard to believe", "signal_type": "skepticism_with_interest", "confidence": 0.68},
        {"quote": "Our last vendor took 6 months", "signal_type": "pain_sharing", "confidence": 0.85},
    ],
    "opportunity_flags": [
        {"opportunity_type": "upsell", "product_suggestion": "Premium Onboarding Package", "evidence": "Customer has deployment anxiety — premium onboarding with dedicated PM would add value.", "confidence": 0.81},
        {"opportunity_type": "cross-sell", "product_suggestion": "Data Migration Service", "evidence": "5 years of historical data requires careful migration planning.", "confidence": 0.93},
    ],
})

OBJECTION_EMAIL = EmailDraft(
    subject="Implementation Timeline & SLA Terms for NovaTech",
    body="Hi David,\n\nThanks for the honest conversation today. I completely understand your caution given past experiences.\n\nHere's what I'm preparing:\n1. Contract amendment with 3-week deployment SLA\n2. Service credit terms if we miss the timeline\n3. Case studies showing successful migrations for companies your size\n4. Data migration plan overview for your 5 years of historical data\n\nI'll have the revised documents ready by Thursday for your review.\n\nBest,\nSales Rep",
)

OBJECTION_COACH = CoachingReport.model_validate({
    "rubric_scores": [
        {"dimension": "Opening & Rapport Building", "score": 7, "comment": "Directly addressed the elephant in the room. Good, but could have been warmer."},
        {"dimension": "Discovery & Needs Analysis", "score": 8, "comment": "Quickly identified the root cause — past vendor trauma vs. real concerns."},
        {"dimension": "Objection Handling", "score": 10, "comment": "Masterful. Used specific data (3 weeks, 10+ PB) and offered guarantees."},
        {"dimension": "Closing & Next Steps", "score": 9, "comment": "Excellent — used SLA guarantees to overcome final objection and secure commitment."},
        {"dimension": "Active Listening", "score": 9, "comment": "Picked up on emotional cues about past experience and addressed them directly."},
    ],
    "talk_ratio_rep": 58.0,
    "talk_ratio_customer": 42.0,
    "strengths": ["Exceptional objection handling", "Used data and case studies effectively", "Creative use of SLA guarantees"],
    "areas_to_improve": ["Build more rapport before diving into objections", "Ask about positive past vendor experiences too"],
    "recommended_actions": ["Document this objection handling framework for team training", "Pre-prepare migration case studies by company size"],
})

# ─────────────────────────────────────────────────────────
# Registry of all scenarios
# ─────────────────────────────────────────────────────────

ScenarioData = dict[str, object]

SCENARIOS: dict[str, ScenarioData] = {
    "discovery": {
        "name": "Discovery Call",
        "description": "Initial discovery call identifying pain points and qualifying budget",
        "company": "Acme Corp",
        "contact": "Sarah Chen",
        "segments": DISCOVERY_SEGMENTS,
        "crm": DISCOVERY_CRM,
        "opportunity": DISCOVERY_OPPORTUNITY,
        "email": DISCOVERY_EMAIL,
        "coach": DISCOVERY_COACH,
    },
    "demo": {
        "name": "Demo Call",
        "description": "Product demonstration with live walkthrough and trial commitment",
        "company": "BetaTech Solutions",
        "contact": "Mark Johnson",
        "segments": DEMO_SEGMENTS,
        "crm": DEMO_CRM,
        "opportunity": DEMO_OPPORTUNITY,
        "email": DEMO_EMAIL,
        "coach": DEMO_COACH,
    },
    "negotiation": {
        "name": "Negotiation Call",
        "description": "Price negotiation with concessions and deal closing",
        "company": "GlobalTech Industries",
        "contact": "Priya Patel",
        "segments": NEGOTIATION_SEGMENTS,
        "crm": NEGOTIATION_CRM,
        "opportunity": NEGOTIATION_OPPORTUNITY,
        "email": NEGOTIATION_EMAIL,
        "coach": NEGOTIATION_COACH,
    },
    "followup": {
        "name": "Follow-up Call",
        "description": "Post-trial check-in with expansion opportunity discovery",
        "company": "GreenLeaf Analytics",
        "contact": "James Wilson",
        "segments": FOLLOWUP_SEGMENTS,
        "crm": FOLLOWUP_CRM,
        "opportunity": FOLLOWUP_OPPORTUNITY,
        "email": FOLLOWUP_EMAIL,
        "coach": FOLLOWUP_COACH,
    },
    "objection": {
        "name": "Objection Handling Call",
        "description": "Overcoming implementation timeline concerns with SLA guarantees",
        "company": "NovaTech Systems",
        "contact": "David Kim",
        "segments": OBJECTION_SEGMENTS,
        "crm": OBJECTION_CRM,
        "opportunity": OBJECTION_OPPORTUNITY,
        "email": OBJECTION_EMAIL,
        "coach": OBJECTION_COACH,
    },
}
