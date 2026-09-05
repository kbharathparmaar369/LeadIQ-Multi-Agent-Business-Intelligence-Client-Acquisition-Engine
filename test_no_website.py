import uuid
from core.graph.workflow import app_graph
from core.schemas import DiscoveredBusiness

config = {"configurable": {"thread_id": str(uuid.uuid4())}}

initial_state = {
    "niche": "dental clinic",
    "location": "Bangalore",
    "batch_size": 1,
    "retry_count": 0,
    "error_log": [],
    "discovered_business": DiscoveredBusiness(
        business_name="Dr. Chahal Aesthetic Clinic",
        website_url=None,
        location="Bangalore",
        niche="dental clinic",
    ),
}

print("Running graph for business without website...")
for event in app_graph.stream(initial_state, config=config):
    print(event)

state = app_graph.get_state(config)
print("\nGenerated Proposal Draft:")
print(state.values.get("proposal_draft"))
