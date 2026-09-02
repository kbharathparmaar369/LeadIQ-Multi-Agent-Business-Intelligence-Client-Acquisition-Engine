import sys
import uuid

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from core.scrapers.maps_discovery import discover_businesses
from core.graph.workflow import app_graph
from core.graph.nodes.outreach import draft_no_website_proposal

def run_batch(niche: str, location: str, batch_size: int = 5):
    print(f"Discovering up to {batch_size} businesses for '{niche}' in '{location}'...")
    businesses = discover_businesses(niche, location, batch_size=batch_size)

    if not businesses:
        print("No businesses found. Stopping.")
        return

    print(f"Found {len(businesses)} businesses. Running graph on each...")

    results = {
        "qualified": [],
        "needs_review": [],
        "disqualified": [],
        "no_website": [],
        "errored": [],
    }

    for business in businesses:
        print(f"\n--- Processing: {business.business_name}")

        if not business.website_url:
            print("No website found - drafting a 'build one' pitch instead.\n")
            try:
                proposal = draft_no_website_proposal(business)
                print(f"Subject: {proposal.email_subject}")
                print(f"Body:\n{proposal.email_body_markdown}\n")
                results["no_website"].append(business.business_name)
            except Exception as e:
                print(f"Error drafting no-website proposal: {e}\n")
                results["errored"].append(business.business_name)
            continue

        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {
            "niche": niche,
            "location": location,
            "batch_size": 1,
            "retry_count": 0,
            "error_log": [],
            "discovered_business": business,
        }

        try:
            for event in app_graph.stream(initial_state, config=config):
                pass
                
            state = app_graph.get_state(config)
            qualification = state.values.get("lead_qualification")

            if qualification is None:
                print("No qualification result - likely a research/audit failure.\n")
                results["errored"].append(business.business_name)
                continue

            status = qualification.status.value
            print(f"Score: {qualification.final_score} | Status: {status}\n")

            if status == "QUALIFIED":
                results["qualified"].append(business.business_name)
            elif status == "NEEDS_REVIEW":
                results["needs_review"].append(business.business_name)
            else:
                results["disqualified"].append(business.business_name)
        
        except Exception as e:
            print(f"Error processing {business.business_name}: {e}\n")
            results["errored"].append(business.business_name)

    _print_summary(results)

def _print_summary(results: dict):
    print("\n================ Batch Summary ================")
    print(f"Qualified    : {len(results['qualified'])} - {results['qualified']}")
    print(f"Needs Review : {len(results['needs_review'])} - {results['needs_review']}")
    print(f"Disqualified : {len(results['disqualified'])} - {results['disqualified']}")
    print(f"No Website   : {len(results['no_website'])} - {results['no_website']}")
    print(f"Errored      : {len(results['errored'])} - {results['errored']}")
    print("===============================================\n")


if __name__ == "__main__":
    run_batch(niche="dental clinic", location="Banglore", batch_size=3)

