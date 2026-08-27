import time
import re
import asyncio
from crawl4ai import AsyncWebCrawler

from core.schemas import SiteAuditData

async def _crawl(website_url: str):
    async with AsyncWebCrawler() as crawler:
        start = time.time()
        result = await crawler.arun(url=website_url)
        load_time = round(time.time() - start, 2)
        return result, load_time

def audit_site(website_url: str) -> SiteAuditData:
    result, load_time = asyncio.run(_crawl(website_url))
    html = result.html or ""
    html_lower = html.lower()

    audit = SiteAuditData(
        website_url=website_url,

        # performance
        load_time_seconds=load_time,
        largest_contentful_paint=None,
        has_uncompressed_assets=_check_uncompressed_assets(html_lower),

        # Tech stack
        detected_framework=_detect_framework(html_lower),
        is_legacy_stack=_is_legacy_stack(html_lower),

        # conversion/CRO
        has_click_to_call=("tel:" in html_lower),
        has_watsapp_link=("wa.me" in html_lower),
        has_clear_cta=_has_clear_cta(html_lower),

        # SEO and metadata
        has_opengraph_tags=("og:title" in html_lower or "og:description" in html_lower),
        has_meta_description=('name="description"' in html_lower or "name='description'" in html_lower),
        has_json_Id_schema=("application/ld+json" in html_lower),

        # AI and Automation readiness
        has_chatbot_or_ai_widget=_has_chatbot(html_lower),
        has_after_hours_booking=_has_booking_widget(html_lower),
        is_static_form_only=_is_static_form_only(html_lower),
        
        # Business Profile
        industry=None,
        service_description=None,
        headline_copy=_extract_headline(html),
        
        # contact
        public_email=_extract_email(html),
        social_links=_extract_social_links(html_lower),
    )        
    return audit

# Helper Functions

def _check_uncompressed_assets(html_lower: str) -> bool:
    jpg_png_count = html_lower.count(".jpg") + html_lower.count(".png")
    uses_webp_or_cdn = ("webp" in html_lower) or ("cloudinary" in html_lower) or ("imagekit" in html_lower)
    return jpg_png_count > 5 and not uses_webp_or_cdn


def _detect_framework(html_lower: str) -> str:
    if "wp-content" in html_lower or "wordpress" in html_lower:
        return "WordPress"

    if "_next/static" in html_lower:
        return "Next.js"
    
    if "react" in html_lower and "_next" not in html_lower:
        return "React.js"
    
    if "vue" in html_lower:
        return "Vue.js"
    
    if "jquery" in html_lower:
        return "jQuery"

    if ".php" in html_lower:
        return "raw PHP"
    
    return "Unknown"

def _is_legacy_stack(html_lower: str) -> bool:
    legacy_signals = ["jquery", "wp-content", "table cellpadding", "font face="]
    return any(signal in html_lower for signal in legacy_signals)

def _has_clear_cta(html_lower: str) -> bool:
    cta_keywords = ["book now", "call now", "get started", "contact us", "book appointment", "order now"]
    return any(keyword in html_lower for keyword in cta_keywords)

def _has_chatbot(html_lower: str) -> bool:
    chatbot_signals = ["intercom", "tawk.to", "drift.com", "crisp.chat", "chatwoot", "widget.js"]
    return any(signal in html_lower for signal in chatbot_signals)

def _has_booking_widget(html_lower: str) -> bool:
    booking_signals = ["booking", "appointment", "reserve", "schedule", "calendar", "tockify", "acuity", "calendly"]
    return any(signal in html_lower for signal in booking_signals)

def _is_static_form_only(html_lower: str) -> bool:
    has_form = "<form" in html_lower
    has_dynamic_intake = _has_chatbot(html_lower) or _has_booking_widget(html_lower)
    return has_form and not has_dynamic_intake


def _extract_headline(html: str) -> str | None:
    match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
    if match:
        text = re.sub(r"<[^>]+>", "", match.group(1)).strip()
        return text[:200] if text else None
    return None

def _extract_email(html: str) -> str | None:
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", html)
    return match.group(0) if match else None

def _extract_social_links(html_lower: str) -> list[str]:
    platforms = [
        "linkedin.com",
        "instagram.com",
        "twitter.com",
        "x.com",
        "facebook.com",
    ]
    
    found = []
    for platform in platforms:
        if platform in html_lower:
            found.append(platform)
    return found

if __name__ == "__main__":
    test_url = "https://stores.nothingbeforecoffee.com/nothing-before-coffee-in-karnataka-bengaluru-richmond-town-17649"
    audit = audit_site(test_url)
    print(audit)