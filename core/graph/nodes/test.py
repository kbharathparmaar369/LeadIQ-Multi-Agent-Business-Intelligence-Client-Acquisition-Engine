from core.graph.workflow import app_graph
from core.schemas import DiscoveredBusiness
import uuid

config2 = {"configurable": {"thread_id": str(uuid.uuid4())}}

initial_state2 = {
    "niche": "dental clinic",
    "location": "Bangalore",
    "batch_size": 1,
    "retry_count": 0,
    "error_log": [],
    "discovered_business": DiscoveredBusiness(
        business_name="VK Dental Care",
        website_url="https://vkdentalcare.co.in/",
        location="Bangalore",
        niche="dental clinic",
    ),
}

for event in app_graph.stream(initial_state2, config=config2):
    print(event)

state2 = app_graph.get_state(config2)
print("\nProposal 2:", state2.values.get("proposal_draft"))