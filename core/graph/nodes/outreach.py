import json
import re

from core.config import smart_llm
from core.schemas import DiscoveredBusiness, SiteAuditData, LeadQualification, ProposalDraft
from core.rag.vector_store import find_similar_case_studies

def draft_proposal(
    business: DiscoveredBusiness,
    audit: SiteAuditData,
    qualification: LeadQualification,
) -> ProposalDraft:
    flaws = _list_flaws(audit)
    flaws_text = ", ".join(flaws) if flaws else "general modernization opportunities."

    case_studies = find_similar_case_studies(flaws_text, top_k=2)

    prompt = _build_prompt(business, flaws, case_studies)

    response = smart_llm.invoke(prompt)
    raw_text = response.content.strip()
    
    # Clean reasoning tags (e.g. from Qwen models) and markdown blocks
    raw_text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw_text)
        subject = parsed.get("email_subject", f"Quick note about {business.business_name}'s website")
        body = parsed.get("email_body_markdown", raw_text)

    except Exception as e:
        print(f"Could not parse LLM output as JSON, using fallback: {e}")
        subject = f"Quick note about {business.business_name}'s website"
        body = raw_text

    return ProposalDraft(
        email_subject=subject,
        email_body_markdown=body,
        matched_case_study_ids=[str(c.get("id", "")) for c in case_studies],
        flaws_highlighted=flaws
    )


def _list_flaws(audit: SiteAuditData) -> list[str]:
    # turns the boolean audit signals into plain language
    flaws = []

    if audit.load_time_seconds and audit.load_time_seconds > 3:
        flaws.append(f"page takes {audit.load_time_seconds}s to load")

    if audit.is_legacy_stack:
        flaws.append(f"Site runs on an outdated stack ({audit.detected_framework})")

    if not audit.has_click_to_call:
        flaws.append("No click-to-call button for mobile visitors.")
    
    if not audit.has_watsapp_link:
        flaws.append("No WhatsApp contact option.")

    if not audit.has_opengraph_tags:
        flaws.append("Missing OpenGraph tags, so shared links look broken on social media.")

    if not audit.has_meta_description:
        flaws.append("Missing meta description, hurting Google search visibility.")

    if not audit.has_chatbot_or_ai_widget and not audit.has_after_hours_booking:
        flaws.append("No after-hours booking or chat option for late inquiries.")
    
    return flaws[:3]

def _build_prompt(business: DiscoveredBusiness, flaws: list[str], case_studies: list[dict]) -> str:
    flaws_list = "\n".join(f"- {f}" for f in flaws) if flaws else "- general modernization opportunities"

    case_study_text = ""
    if case_studies:
        top_case = case_studies[0]
        case_study_text = f"We previously worked on a similar project: {top_case.get('result_summary', '')}"

    return f"""You are writing a short, friendly cold email for a web engineering agency.
The email is to the owner of "{business.business_name}", a {business.niche} business in {business.location}.

Here are 2-3 specific issues we found on their website:
{flaws_list}

Proof point to reference naturally (don't just paste it, weave it in):
{case_study_text}

Write a short cold email that:
1. Opens with a specific, genuine observation (not generic flattery)
2. Mentions the flaws found in plain, non-technical language
3. References the proof point briefly
4. Invites them to a free mini-audit call, low pressure
5. Signs off simply, no fake name - use "The Team" as the sign-off

Keep the email under 150 words. Do not use hype words like "revolutionary" or "game-changing".

Reply with ONLY a JSON object in this exact format, nothing else:
{{
  "email_subject": "short subject line under 8 words",
  "email_body_markdown": "the full email body"
}}"""


if __name__ == "__main__":
    test_business = DiscoveredBusiness(
        business_name="The Bangalore Cafe",
        website_url="https://wyxsite.wixstudio.com/thebangalorecafe",
        location="Bangalore",
        niche="restaurant",
    )

    test_audit = SiteAuditData(
        website_url=test_business.website_url,
        load_time_seconds=3.8,
        detected_framework="WordPress",
        is_legacy_stack=True,
        has_click_to_call=False,
        has_watsapp_link=False,
        has_opengraph_tags=False,
        has_meta_description=False,
        has_chatbot_or_ai_widget=False,
        has_after_hours_booking=False,
    )

    from core.schemas import LeadQualification, LeadStatus
    test_qualification = LeadQualification(
        tech_pain_score=85,
        commercial_intent_score=90,
        contact_quality_score=75,
        final_score=84,
        status=LeadStatus.QUALIFIED,
    )

    proposal = draft_proposal(test_business, test_audit, test_qualification)
    print(proposal)
