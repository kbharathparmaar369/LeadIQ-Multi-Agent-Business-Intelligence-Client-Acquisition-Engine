import json
import re
import time

from core.config import fast_llm
from core.schemas import DiscoveredBusiness, SiteAuditData, criticEvaluation

# common placeholders
KNOWN_PLACEHOLDER_EMAILS = [
    "info@mysite.com",
    "example@example.com",
    "test@test.com",
    "your@email.com",
    "name@email.com",
]

PERSONAL_EMAIL_DOMAINS = [
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "aol.com",
    "msn.com",
    "live.com",
]

def _invoke_with_retry(llm,prompt: str, max_attempts: int =2):
    last_error=None
    for attempt in range(1,max_attempts + 1):
        try:
            return llm.invoke(prompt)
        except Exception as e:
            last_error=e
            print(f"LLM call failed (attempt {attempt} / {max_attempts}): {e}")
            if attempt < max_attempts:
                time.sleep(2)     
    raise last_error

def evaluate_data(business: DiscoveredBusiness, audit: SiteAuditData) -> criticEvaluation:
    flagged_issues: list[str] = []
    
    # Local email check 
    is_email_valid_format = _is_valid_email_format(audit.public_email)
    if audit.public_email:
        if audit.public_email.lower() in KNOWN_PLACEHOLDER_EMAILS:
            flagged_issues.append("Email looks like a template/placeholder default")

        domain = audit.public_email.split("@")[-1].lower()
        if domain in PERSONAL_EMAIL_DOMAINS:
            flagged_issues.append("Email is a personal address, not a business domain")

    # completeness_score
    completeness_score = _calculate_completeness(business, audit)

    # LLM sanity check on the cleaned summary
    llm_flags = _ask_llm_for_sanity_check(business, audit)
    flagged_issues.extend(llm_flags)

    needs_recrawl = completeness_score < 0.6

    return criticEvaluation(
        is_email_valid_format=is_email_valid_format,
        data_completeness_score=completeness_score,
        flagged_issues=flagged_issues,
        needs_recrawl=needs_recrawl,
    )


def _is_valid_email_format(email: str | None) -> bool:
    if not email:
        return False
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def _calculate_completeness(business: DiscoveredBusiness, audit: SiteAuditData) -> float:
    important_fields = [
        business.business_name,
        business.niche,
        audit.load_time_seconds,
        audit.detected_framework,
        audit.public_email,
        audit.headline_copy,
        audit.industry,
        audit.service_description,
    ]

    filled = sum(1 for field in important_fields if field not in (None, "", "Unknown"))
    return round(filled / len(important_fields), 2)


def _ask_llm_for_sanity_check(business: DiscoveredBusiness, audit: SiteAuditData) -> list[str]:
    summary = f"""
        Business name: {business.business_name}
        Niche: {business.niche}
        Headline copy found on site: {audit.headline_copy}
        Detected framework: {audit.detected_framework}
        Public email: {audit.public_email}
    """

    prompt = f"""
        You are checking scraped business data for obvious problems.
Here is the data:
{summary}

        Reply with a JSON list of short strings, each describing ONE issue you notice.
        If nothing looks wrong, reply with an empty JSON list: []
        Only flag real problems - do not invent issues. Keep each issue under 12 words.
        Reply with ONLY the JSON list, nothing else.
    """

    try:
        response = _invoke_with_retry(fast_llm,prompt)
        raw_text = response.content.strip()

        raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        issues = json.loads(raw_text)
        if isinstance(issues, list):
            return [str(i) for i in issues if isinstance(i, str)]
        return []
    
    except Exception as e:
        print(f"LLM sanity check failed, skipping: {e}")
        return []


if __name__ == "__main__":
    test_business = DiscoveredBusiness(
        business_name="The Bangalore Cafe",
        website_url="https://wyxsite.wixstudio.com/thebangalorecafe",
        phone_number="095359 64043",
        location="Bangalore",
        rating=None,
        niche="restaurants",
    )

    test_audit = SiteAuditData(
        website_url="https://wyxsite.wixstudio.com/thebangalorecafe",
        load_time_seconds=1.31,
        detected_framework="React.js",
        has_click_to_call=False,
        has_opengraph_tags=True,
        headline_copy="A New Experience is Coming Soon",
        public_email="info@mysite.com",
        social_links=["instagram.com", "x.com", "facebook.com"],
    )
    evaluation = evaluate_data(test_business, test_audit)
    print(evaluation)
