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
    {
        "title": "Salon booked from scratch with a new website",
        "description": "A hair and beauty salon had no website at all, relying only on a Google Maps listing and walk-ins.",
        "result_summary": "Built a simple booking site from the ground up with service listings and an online scheduler - online bookings made up 35% of total appointments within two months.",
    },
    {
        "title": "Real estate agent launched from zero online presence",
        "description": "An independent real estate agent had no website, sharing listings only through WhatsApp broadcasts to past clients.",
        "result_summary": "Built a lightweight listings site from scratch with photo galleries and an inquiry form - inbound inquiries from new clients tripled in the first month.",
    },
    {
        "title": "Salon SEO and outdated design refresh",
        "description": "A beauty salon's old WordPress site ran on jQuery, had no meta descriptions, and looked outdated on mobile.",
        "result_summary": "Rebuilt with a modern responsive design and full SEO metadata, moving the salon onto the first page of local Google search results within three weeks.",
    },
     {
        "title": "Real estate listings site performance fix",
        "description": "A real estate firm's listings page took over 5 seconds to load due to uncompressed property photos.",
        "result_summary": "Compressed and optimized all property images and added lazy loading, cutting load time to 1.5s and reducing bounce rate by 45%.",
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