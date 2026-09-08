from core.graph.nodes.scoring import score_lead
from core.schemas import SiteAuditData, CriticEvaluation

# Simulates what a totally failed crawl looks like - everything empty
empty_audit = SiteAuditData(website_url="http://ankithrealtors.online/")
empty_critic = CriticEvaluation(
    is_email_valid_format=False,
    data_completeness_score=0.0,
    flagged_issues=["No data retrieved"],
    needs_recrawl=True,
)

result = score_lead(empty_audit, empty_critic)
print(result)