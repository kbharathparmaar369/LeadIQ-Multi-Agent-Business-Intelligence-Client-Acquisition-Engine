# we will now compile all agents into a single 

from core.scrapers.site_crawler import audit_site
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from core.schemas import AgentState, LeadStatus
from core.scrapers.maps_discovery import discover_businesses
from core.graph.nodes.critic import evaluate_data
from core.graph.nodes.scoring import score_lead
from core.graph.nodes.outreach import draft_proposal

import langgraph.checkpoint.serde.jsonplus as jsonplus

jsonplus._msgpack_ext_hook_allowed_modules = jsonplus._msgpack_ext_hook_allowed_modules | {
    ("core.schemas", "DiscoveredBusiness"),
    ("core.schemas", "SiteAuditData"),
    ("core.schemas", "CriticEvaluation"),
    ("core.schemas", "LeadQualification"),
    ("core.schemas", "LeadStatus"),
    ("core.schemas", "ProposalDraft"),
}

def discovery_node(state: AgentState) -> dict:
    businesses = discover_businesses(
        niche=state["niche"],
        location=state["location"],
        batch_size=1,
    )

    if not businesses:
        return {"error_log": state.get("error_log", []) + ["No businesses found in discovery"]}

    return {"discovered_business": businesses[0]}
   

def research_node(state: AgentState) -> dict:
    business=state["discovered_business"]

    if not business.website_url:
        return {"error_log": state.get("error_log", []) + ["No website URL to audit"]}
    
    audit=audit_site(business.website_url)
    return {"site_audit": audit}

def critic_node(state: AgentState) -> dict:
    business=state["discovered_business"]
    audit=state["site_audit"]

    evaluation=evaluate_data(business, audit)
    current_retries=state.get("retry_count",0)

    return {
        "critic_evaluation": evaluation,
        "retry_count": current_retries + 1 if evaluation.needs_recrawl else current_retries,
    }

def scoring_node(state: AgentState) -> dict:
    audit=state["site_audit"]
    critic = state["critic_evaluation"]

    qualification=score_lead(audit, critic)
    return {"lead_qualification" : qualification}

def outreach_node(state: AgentState) -> dict:
    business=state["discovered_business"]
    audit=state["site_audit"]
    qualification=state["lead_qualification"]

    proposal=draft_proposal(business, audit, qualification)
    return {"proposal_draft" : proposal}

def dispatch_node(state: AgentState) -> dict:
    # this works via person B
    return {}


# conditional routing

def route_after_critic(state: AgentState)-> str:

    evaluation=state["critic_evaluation"]
    retries_so_far=state.get("retry_count",0)

    if evaluation.needs_recrawl and retries_so_far <= 1:
        return "research"
    return "scoring"

def route_after_scoring(state: AgentState) -> str:
    # only qualified or borderline leads move to outreach.

    qualification=state["lead_qualification"]

    if qualification.status in (LeadStatus.QUALIFIED, LeadStatus.NEEDS_REVIEW):
        return "outreach"
    return END

# Building and compiling the graph


def build_graph():
    graph=StateGraph(AgentState)

    graph.add_node("discovery", discovery_node)
    graph.add_node("research", research_node)
    graph.add_node("critic", critic_node)
    graph.add_node("scoring", scoring_node)
    graph.add_node("outreach", outreach_node)
    graph.add_node("dispatch", dispatch_node)

    graph.set_entry_point("discovery")

    graph.add_edge("discovery","research")
    graph.add_edge("research","critic")

    graph.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "research": "research",
            "scoring" : "scoring",
        },
    )

    graph.add_conditional_edges(
        "scoring",
        route_after_scoring,
        {
            "outreach": "outreach",
            END : END,
        },
    )

    graph.add_edge("outreach","dispatch")
    graph.add_edge("dispatch",END)

    checkpointer=MemorySaver()
    compiled=graph.compile(checkpointer=checkpointer, interrupt_before=["dispatch"])
    return compiled

app_graph = build_graph()

if __name__ == "__main__":
    config = {"configurable": {"thread_id": "test-run-1"}}

    initial_state = {
        "niche": "restaurant",
        "location": "Bangalore",
        "batch_size": 1,
        "retry_count": 0,
        "error_log": [],
    }

    print("Running graph until HITL interrupt...")
    for event in app_graph.stream(initial_state, config=config):
        print(event)

    print("\n--- Graph paused before dispatch (HITL checkpoint) ---")
    state = app_graph.get_state(config)
    print("Current proposal draft:", state.values.get("proposal_draft"))

    print("\nSimulating human approval, resuming graph...")
    for event in app_graph.stream(None, config=config):
        print(event)

    print("\n--- Graph finished ---")