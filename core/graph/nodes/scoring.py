from core.schemas import SiteAuditData, criticEvaluation, LeadQualification, compute_lead_status

def score_lead(audit: SiteAuditData, critic : criticEvaluation)-> LeadQualification:
    tech_pain=_calculate_tech_pain(audit)
    commercial_intent=_calculate_commercial_intent(audit)
    contact_quality=_calculate_contact_quality(audit,critic)

    final_score=round(
        (0.40 * tech_pain) + (0.30 * commercial_intent) + (0.30 * contact_quality),
        2,
    )

    status = compute_lead_status(final_score)
    disqualify_reason = None
    if status.value == "DISQUALIFIED":
        disqualify_reason = _build_disqualify_reason(audit, tech_pain, commercial_intent, contact_quality)

    
    return LeadQualification(
        tech_pain_score=tech_pain,
        commercial_intent_score=commercial_intent,
        contact_quality_score=contact_quality,
        final_score=final_score,
        status=status,
        disqualify_reason=disqualify_reason,
    )

def _calculate_tech_pain(audit: SiteAuditData) -> float:
    score=0

    if audit.load_time_seconds is not None:
        if audit.load_time_seconds > 3:
            score += 30
        elif audit.load_time_seconds <= 2:
            score += 15

    if audit.is_legacy_stack:
        score += 20
    
    if not audit.has_click_to_call:
        score += 10

    if not audit.has_watsapp_link:
        score += 5
    
    if not audit.has_opengraph_tags:
        score += 10
    
    if not audit.has_meta_description:
        score += 10

    if not audit.has_json_ld_schema:
        score += 5

    if audit.has_uncompressed_assets:
        score += 10
    
    return min(score,100)

def _calculate_commercial_intent(audit: SiteAuditData) -> float:

    score =100

    if audit.headline_copy and "coming soon" in audit.headline_copy.lower():

        score -=50

    if not audit.service_description and not audit.headline_copy:
        score -=20

    if not audit.has_clear_cta:
        score -=10
    
    if audit.is_static_form_only and not audit.has_after_hours_booking:
        score -=20

    return max(score,0)

def _calculate_contact_quality(audit:SiteAuditData, critic: criticEvaluation) -> float:

    score=0

    if audit.public_email and critic.is_email_valid_format:
        score +=40

    if audit.public_email and "Email looks like a template/placeholder default" not in critic.flagged_issues:
        score +=20
    
    if audit.public_email and "Email is a personal address, not a business domain" not in critic.flagged_issues:
        score += 20

    if audit.social_links:
        score +=20
    return min(score,100)

def _build_disqualify_reason(audit: SiteAuditData, tech_pain: float, commercial: float , contact: float) -> str:
    if commercial < 50:
        return "Site shows low commercial activity (e.g. placeholder/coming soon content); low sales probability."
    if tech_pain < 30:
         return "Site already uses modern practices and loads reasonably fast; low sales probability."
    if contact < 40:
        return "No reliable business contact channel found; cannot verify outreach quality."
    return "Overall score below qualification threshold."

if __name__ =="__main__":
    from core.schemas import DiscoveredBusiness
    from core.graph.nodes.critic import evaluate_data

    test_audit = SiteAuditData(
        website_url="https://wyxsite.wixstudio.com/thebangalorecafe",
        load_time_seconds=1.31,
        detected_framework="React.js",
        has_click_to_call=False,
        has_whatsapp_link=False,
        has_opengraph_tags=True,
        has_meta_description=False,
        has_json_ld_schema=False,
        has_clear_cta=True,
        headline_copy="A New Experience is Coming Soon",
        public_email="info@mysite.com",
        social_links=["instagram.com", "x.com", "facebook.com"],
    )

    test_business = DiscoveredBusiness(
        business_name="The Bangalore Cafe",
        website_url=test_audit.website_url,
        location="Bangalore",
        niche="restaurants",
    )

    test_critic = evaluate_data(test_business, test_audit)
    result = score_lead(test_audit, test_critic)
    print(result) 
        

   