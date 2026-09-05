import uuid

from core.graph.workflow import app_graph

def simulate_search_request(niche: str, location: str):
    print(f"[Backed] Recieved search request : niche = '{niche}'| location = '{location}'")
    thread_id = str(uuid.uuid4())
    config={"configurable" : {"thread_id": thread_id}}

    initial_state={
        "niche":niche,
        "location": location,
        "batch_size": 1,
        "retry_count": 0,
        "error_log": [],
    }
    print("[BACKED] starting graph run")

    for event in app_graph.stream(initial_state,config=config):
        node_name=list(event.keys())[0]
        print(f"[BACKEND] graph reached node : {node_name}")

    return config

def simulate_frontend_polling(config: dict):
    print("\n [BACKEND] Checking graph state for pending approval")
    state=app_graph.get_state(config)

    qualification=state.values.get("lead_qualification")
    proposal=state.values.get("proposal_draft")
    business=state.values.get("discovered_business")

    if business is None:
        print("[BACKEND] No business was discovered . Nothing to show")
        return None
    print(f"[BACKEND] Business :{business.business_name}")

    if qualification is not None:
        print(f"[BACKEND] Score : {qualification.final_score} | Status : {qualification.status.value}")

    if proposal is None:
        print("[BACKED] No proposal drafted (likely disqualified). Nothing Pending for approval")
        return None
    
    print("\n [FRONTEND] Showing approval modal to human reviewer:")
    print(f"Subject : {proposal.email_subject}")
    print(f"Body: \n {proposal.email_body_markdown}")
    print(f"Flaw highlighted : {proposal.flaws_highlighted}")

    return proposal


def simulate_human_approval(config: dict, approved: bool):
    if not approved:
        print(f"\n [BACKEND] Human rejected the proposal. Graph stays paused, nothing sent. ")
        return

    print("\n [BACKEND] Human clicked Approve. resuming Graph")
    for event in app_graph.stream(None, config=config):
        node_name=list(event.keys())[0]
        print(f"[BACKEND] Graph reached node : {node_name}")


def simulate_n8n_handoff(config: dict):
    state=app_graph.get_state(config)
    proposal=state.values.get("proposal_draft")
    business=state.values.get("discovered_business")

    if proposal is None or business is None:
        print("\n [n8n] nothing to dispatch")
        return
    
    payload={
        "to_business_name": business.business_name,
        "to_email": proposal.recipient_email,
        "subject" : proposal.email_subject,
        "body": proposal.email_body_markdown,
    }

    print(f"\n [n8n] would recieve this payload for email dispatch")
    print(payload)


if __name__ == "__main__":
    config = simulate_search_request(niche="dental clinic", location="Bangalore")
    proposal = simulate_frontend_polling(config)

    if proposal is not None:
        simulate_human_approval(config, approved=True)
        simulate_n8n_handoff(config)
    else:
        print("\n[TEST COMPLETE] No proposal to approve - lead was disqualified or errored.")

