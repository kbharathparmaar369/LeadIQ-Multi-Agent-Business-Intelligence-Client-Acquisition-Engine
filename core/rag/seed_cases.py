from core.config import supabase
from core.rag.vector_store import embed_text

SEED_CASE_STUDIES=[
    {
        "title": "Dental clinic mobile speed overhaul",
        "description": "A dental clinic's site had a 4.5s load time and no mobile-friendly layout, losing walk-in bookings.",
        "result_summary": "Rebuilt on Next.js, cut load time to under 1.2s, added click-to-call - booking form submissions increased 60%.",
    },
    {
        "title": "Gym website SEO and CTA fix",
        "description": "A local gym's WordPress site had no OpenGraph tags and buried its signup CTA below the fold.",
        "result_summary": "Added SEO metadata and a sticky signup CTA, resulting in a 40% increase in trial signups within a month.",
    },
    {
        "title": "Real estate firm AI chatbot integration",
        "description": "A real estate firm relied on a static contact form with no after-hours lead capture.",
        "result_summary": "Added an AI chat widget for instant inquiries, capturing 25% more leads outside business hours.",
    },
    {
        "title": "Restaurant WhatsApp ordering integration",
        "description": "A restaurant had no WhatsApp or click-to-call links, forcing customers to call during busy hours.",
        "result_summary": "Added WhatsApp ordering and click-to-call buttons, reducing missed orders and improving customer response time.",
    },
]


def seed_case_studies():
    for case in SEED_CASE_STUDIES:
        text_to_embed=f"{case['description']} {case['result_summary']}"
        embedding=embed_text(text_to_embed)

        supabase.table("case_studies").insert({
            "title": case["title"],
            "description": case["description"],
            "result_summary": case["result_summary"],
            "embedding": embedding,
        }).execute()

        print(f"seeded : {case['title']}")
        
if __name__ == "__main__":
    seed_case_studies()
    print("Done seeding case studies.")