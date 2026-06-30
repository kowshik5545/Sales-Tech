"""
Shared dialogue scripts for the 5 demo sales call scenarios.
Both generate_demo_audio.py and setup_db.py import from here
to ensure transcripts in Supabase match the actual audio content.
"""

from __future__ import annotations

from typing import Any

# Each dialogue is a list of (speaker, text) tuples.
# Speaker is "rep" or "customer".

DIALOGUE_1_SARAH_CHEN: list[tuple[str, str]] = [
    ("rep", "Hi Sarah, this is Alex from TechSolutions. Thank you for taking the time to chat today."),
    ("customer", "Hi Alex, thanks for reaching out. I've been meaning to look into solutions for our reporting challenges."),
    ("rep", "Absolutely. I'd love to learn more about what you're experiencing at TechCorp. Could you walk me through your current reporting process?"),
    ("customer", "Well, right now our sales team spends about twelve hours a week manually compiling reports. We pull data from three different spreadsheets, then someone has to reconcile the numbers. It's incredibly tedious and error prone."),
    ("rep", "Twelve hours a week, that's significant. What kind of impact does that have on your team's productivity?"),
    ("customer", "It means our reps are spending less time actually selling. And honestly, the reports are often late because of the manual work. By the time leadership gets the numbers, they're already a few days old."),
    ("rep", "That's a common pain point I hear. And what about data accuracy? With three separate spreadsheets, I imagine discrepancies come up frequently."),
    ("customer", "All the time. We've had situations where two reports showed different numbers for the same metric. It's embarrassing when you're presenting to the board."),
    ("rep", "I understand completely. What would an ideal solution look like for you?"),
    ("customer", "Something that automates the data collection and report generation. Real-time dashboards would be amazing, but at minimum, I want accuracy and speed."),
    ("rep", "Makes perfect sense. Our platform actually does exactly that. It connects to your existing CRM and other data sources, then generates automated reports with real-time dashboards. Most clients see an eighty percent reduction in reporting time."),
    ("customer", "That sounds promising. How long does implementation typically take?"),
    ("rep", "For a team of your size, usually two to three weeks. We handle all the data migration and provide dedicated onboarding support."),
    ("customer", "That's reasonable. Could you send me a detailed proposal with pricing?"),
    ("rep", "Absolutely. I'll also include some case studies from similar companies in your industry. Would Tuesday work for a follow-up demo to walk through the platform?"),
    ("customer", "Yes, Tuesday afternoon works well. I'll also bring our VP of Sales so she can see it firsthand."),
    ("rep", "Perfect. I'll send the proposal and calendar invite today. Thanks so much for your time, Sarah."),
    ("customer", "Thanks, Alex. Looking forward to it."),
]

DIALOGUE_2_MARCUS_JOHNSON: list[tuple[str, str]] = [
    ("rep", "Marcus, thanks for joining the call today. I understand you've been exploring some options for data unification."),
    ("customer", "Yes, Alex. We've been struggling with this for a while now. Our sales and marketing teams are using completely different data sets, and it's causing real alignment problems."),
    ("rep", "Can you give me an example of how that manifests in your day-to-day?"),
    ("customer", "Sure. Marketing runs campaigns and tracks leads in their system, but sales has no visibility into which campaigns are actually driving qualified opportunities. We're basically guessing when we allocate budget."),
    ("rep", "So there's a disconnect between marketing spend and actual pipeline outcomes. How are you currently trying to bridge that gap?"),
    ("customer", "We've tried manual exports and shared spreadsheets, but it's always out of date. By the time someone compiles the data, it's already stale."),
    ("rep", "And what's the business impact of that disconnect?"),
    ("customer", "We're wasting money on campaigns that don't generate real pipeline, and our sales team isn't getting the leads they need. It's a lose-lose situation."),
    ("rep", "I hear you. What would it mean for InnovateHub if marketing and sales had a unified view of the customer journey?"),
    ("customer", "It would be transformative. We could see exactly which campaigns drive revenue, optimize our spend, and give sales the context they need to close faster."),
    ("rep", "That's exactly what our platform delivers. We create a single source of truth that both teams can access in real-time. I'd love to show you how it works."),
    ("customer", "Yes, let's definitely do a demo. When are you available?"),
    ("rep", "How about Thursday at two PM? I can walk you through the live platform and show you a real customer dashboard."),
    ("customer", "Thursday at two works. Should I bring anyone else from the team?"),
    ("rep", "If you have a marketing operations person, that would be great. They'll appreciate the technical details. I'll also send over some case studies showing how other B2B companies have solved this exact problem."),
    ("customer", "Perfect. I'll invite our marketing ops lead. Looking forward to it."),
    ("rep", "Excellent. I'll send the calendar invite and some pre-reading materials. Talk soon, Marcus."),
]

DIALOGUE_3_PRIYA_PATEL: list[tuple[str, str]] = [
    ("rep", "Priya, it's great to connect again. I know we've had a few conversations about your customer onboarding challenges. Ready to talk specifics?"),
    ("customer", "Absolutely, Alex. As I mentioned, we're growing fast but our onboarding process hasn't scaled with us. We're bringing on more customers but we can't hire fast enough to keep up."),
    ("rep", "Right, you mentioned you were concerned about maintaining quality while scaling. Can you quantify the current bottleneck?"),
    ("customer", "Our onboarding team has five people handling about thirty new customers per month. Each customer takes roughly two weeks to fully onboard. If we double our customer base next quarter, we'd need to double our team, which isn't feasible."),
    ("rep", "And what happens to onboarding quality when the team is stretched thin?"),
    ("customer", "Customer satisfaction drops. We've seen our time to first value increase from five days to over ten days in the past quarter. Some customers are getting frustrated."),
    ("rep", "That's a critical metric. What if you could automate sixty percent of the onboarding steps without sacrificing quality?"),
    ("customer", "That would be incredible. We could handle twice the volume with the same team, or even reduce the team and focus on high-touch accounts."),
    ("rep", "Our platform does exactly that. We use AI-driven workflows that guide customers through self-serve onboarding while your team focuses on the complex accounts. Most clients see time to first value drop by forty percent."),
    ("customer", "I'm definitely interested. What's the investment look like?"),
    ("rep", "For your scale, I'd recommend the Enterprise plan at eight thousand per month. That includes full automation, analytics dashboard, and dedicated success manager."),
    ("customer", "That's within our budget range. Can you send a formal proposal?"),
    ("rep", "Absolutely. I'll have it to you by end of day Friday. It'll include the full pricing breakdown, implementation timeline, and ROI projections based on your specific numbers."),
    ("customer", "That sounds great. Let's plan to review it together next week."),
    ("rep", "Perfect. I'll schedule a call for Monday to walk through the proposal. Thanks, Priya."),
]

DIALOGUE_4_ALEX_RIVERA: list[tuple[str, str]] = [
    ("rep", "Alex, thanks for making time today. I know you've been reviewing our proposal for the data pipeline monitoring solution."),
    ("customer", "Yes, and I have to say, the demo was impressive. We really need better visibility into our pipeline health. The current situation is unacceptable."),
    ("rep", "Can you tell me more about what's happening right now?"),
    ("customer", "Our data pipelines fail silently. By the time we notice, we've got corrupted data in production. Last week we had a revenue reporting pipeline that was down for six hours before anyone caught it."),
    ("rep", "Six hours of blind spots on revenue data, that's costly. What's the root cause of the delayed detection?"),
    ("customer", "We don't have real-time monitoring. We check dashboards manually, maybe once or twice a day. But data issues can happen at any time, and we need something that alerts us immediately."),
    ("rep", "And what about the latency issues you mentioned in our earlier conversation?"),
    ("customer", "Right. Our real-time analytics pipelines are taking twenty minutes to process data that should take thirty seconds. It's killing our ability to make timely decisions."),
    ("rep", "I understand. Our platform provides real-time health monitoring with automatic alerting, plus intelligent optimization of your pipeline performance. We typically see latency improvements of ninety percent or more."),
    ("customer", "That's what we need. Now, let's talk about the contract. Your proposal shows an annual commitment. Can we do something shorter initially?"),
    ("rep", "I appreciate you being direct about that. We can offer a six-month trial period with the option to convert to annual. We can also include a thirty-day pilot phase at reduced cost so you can validate the results."),
    ("customer", "That's more reasonable. And the pricing?"),
    ("rep", "For your pipeline volume, I can offer a fifteen percent discount if we sign by end of month. That brings it to seventy-six hundred per month."),
    ("customer", "I appreciate the flexibility. One more thing - can you guarantee ninety-nine point nine percent uptime on the monitoring platform itself?"),
    ("rep", "Absolutely. That's included in our SLA. We also have a dedicated support channel for enterprise clients with response times under thirty minutes."),
    ("customer", "Okay, I'm convinced. Let me get the contract reviewed by our legal team. If everything looks good, we could sign this week."),
    ("rep", "Excellent. I'll send the updated contract with the trial terms and discount reflected. I'll also include the SLA details. Looking forward to partnering with DataFlow, Alex."),
    ("customer", "Thanks, Alex. Let's make this happen."),
]

DIALOGUE_5_EMILY_WATSON: list[tuple[str, str]] = [
    ("rep", "Emily, congratulations on making the decision to go with our omnichannel platform. We're thrilled to have RetailNext on board."),
    ("customer", "Thanks, Alex. We've been evaluating solutions for six months, and yours was clearly the best fit. The POS integration demo really sold it for our team."),
    ("rep", "I'm glad that resonated. Let's talk about next steps. We'll want to schedule a kick-off call with your technical team to map out the integration timeline."),
    ("customer", "That sounds good. Our IT lead is Mark Thompson. He'll be the primary technical contact. What's the typical implementation timeline?"),
    ("rep", "For a full omnichannel integration, usually eight to twelve weeks. We'll start with a data audit, then migrate your historical data, and finally set up the real-time sync between your POS and our platform."),
    ("customer", "We'll need to coordinate timing carefully. We have a big holiday season coming up and we can't afford any downtime."),
    ("rep", "Absolutely. We always recommend implementing during lower-traffic periods. I'd suggest we target the launch for early October, which gives us plenty of buffer before the holiday rush."),
    ("customer", "That's smart planning. What about training for our store managers?"),
    ("rep", "We provide comprehensive training - both live sessions and recorded materials. Your team will have access to our learning portal with certifications and ongoing support."),
    ("customer", "Perfect. One more thing - can we get a dedicated customer success manager?"),
    ("rep", "Of course. That's included in your plan. You'll have a named CSM who knows your business and can help with any questions or optimizations."),
    ("customer", "Excellent. I'm really excited about this. Our last vendor was unresponsive and we need a partner who's invested in our success."),
    ("rep", "You have my word on that. I'll have the kick-off meeting invite out by end of day. Welcome aboard, Emily."),
    ("customer", "Thanks, Alex. Talk soon."),
]

# ── Helpers to build transcript data ─────────────────────

SCENARIO_DURATIONS: dict[str, float] = {
    "Discovery": 185.0,
    "Demo Scheduled": 167.0,
    "Proposal": 161.0,
    "Negotiation": 198.0,
    "Closed Won": 149.0,
}

ALL_DIALOGUES: list[dict[str, Any]] = [
    {
        "name": "Sarah Chen",
        "company": "TechCorp Inc.",
        "deal_stage": "Discovery",
        "dialogue": DIALOGUE_1_SARAH_CHEN,
    },
    {
        "name": "Marcus Johnson",
        "company": "InnovateHub",
        "deal_stage": "Demo Scheduled",
        "dialogue": DIALOGUE_2_MARCUS_JOHNSON,
    },
    {
        "name": "Priya Patel",
        "company": "ScaleUp AI",
        "deal_stage": "Proposal",
        "dialogue": DIALOGUE_3_PRIYA_PATEL,
    },
    {
        "name": "Alex Rivera",
        "company": "DataFlow Inc.",
        "deal_stage": "Negotiation",
        "dialogue": DIALOGUE_4_ALEX_RIVERA,
    },
    {
        "name": "Emily Watson",
        "company": "RetailNext",
        "deal_stage": "Closed Won",
        "dialogue": DIALOGUE_5_EMILY_WATSON,
    },
]


def build_full_text(dialogue: list[tuple[str, str]]) -> str:
    """Build a full transcript text from dialogue lines."""
    return "\n".join(text for _, text in dialogue)


def build_segments(dialogue: list[tuple[str, str]]) -> list[dict[str, Any]]:
    """Build transcript segments with estimated timestamps from dialogue."""
    segments: list[dict[str, Any]] = []
    current_time = 0.0
    for speaker, text in dialogue:
        speaker_label = "Rep" if speaker == "rep" else "Customer"
        duration = max(len(text) * 0.06, 2.0)  # ~60ms per character, min 2s
        segments.append({
            "speaker": speaker_label,
            "timestamp_start": round(current_time, 1),
            "timestamp_end": round(current_time + duration, 1),
            "text": text,
        })
        current_time += duration + 0.5  # add half-second pause
    return segments
