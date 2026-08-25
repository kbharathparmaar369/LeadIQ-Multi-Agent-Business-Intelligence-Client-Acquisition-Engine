from typing import Optional, List, TypedDict
from enum import Enum
from pydantic import BaseModel, Field

# Discover the node output

class DiscoveredBusiness(BaseModel):
    business_name: str
    website_url: Optional[str]=None
    phone_number: Optional[str]=None
    location:str
    rating:Optional[float]=None
    niche: str       


# Research Agent output

class SiteAuditData(BaseModel):
    website_url:str

    load_time_seconds:Optional[float]=None
    largest_contentful_paint:Optional[float]=None
    has_uncompressed_assets: bool=False

    # tech stack

    detected_framework: Optional[str]=None
    is_legacy_stack: bool= False

    #conversion

    has_click_to_call : bool = False
    has_watsapp_link: bool=False
    has_clear_cta: bool=False

    #SEO and metadata
    has_opengraph_tags: bool=False
    has_meta_description: bool=False
    has_json_Id_schema: bool=False

    #AI and Automation readinesss
    has_chatbot_or_ai_widget:bool=False
    has_after_hours_booking: bool=False
    is_static_form_only: bool=False

    #business profile

    industry: Optional[str]=None
    service_description:Optional[str]=None
    headline_copy:Optional[str]=None

    # contact

    public_email:Optional[str]=None
    social_links:List[str]=Field(default_factory=list)


# Critic Agent output

class criticEvaluation(BaseModel):
    is_email_valid:bool
    data_completeness_score:float
    flagged_issues: List[str] = Field(default_factory=list)
    needs_recrawl: bool=False

# scoring Agent output

class  LeadStatus(str,Enum):
    QUALIFIED="QUALIFIED"
    NEEDS_REVIEW="NEEDS_REVIEW"
    DISQUALIFIED="DISQUALIFIED"


class LeadQualification(BaseModel):
    tech_pain_score: float
    commercial_intent_score: float
    contact_quality_score: float
    final_score:float
    status:LeadStatus
    disqualify_reason:Optional[str]=None



def compute_lead_status(final_score : float) -> LeadStatus:
    if final_score>= 70:
        return LeadStatus.QUALIFIED
    elif final_score >=65:
        return LeadStatus.NEEDS_REVIEW
    else:
        return LeadStatus.DISQUALIFIED

#Agentstate - flows through the entire LangGraph graph


# Outreach Agent output
class ProposalDraft(BaseModel):
    email_subject:str
    email_body_markdown: str
    matched_case_study_ids: List[str]=Field(default_factory=list)
    flaws_highlighted:List[str]=Field(default_factory=list)



class AgentState(TypedDict,total=False):
    niche:str
    location: str
    batch_size: int

    discovered_business:DiscoveredBusiness
    site_audit:SiteAuditData
    critic_evaluation: criticEvaluation
    lead_qualification :LeadQualification
    proposal_draft: ProposalDraft

    retry_count:int
    error_log: List[str]

