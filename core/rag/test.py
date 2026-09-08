from core.rag.vector_store import find_similar_case_studies

print("--- No website query ---")
for r in find_similar_case_studies("no website at all, needs one built from scratch", top_k=2):
    print(r["title"], "-", round(r["similarity"], 3))

print("\n--- Real estate query ---")
for r in find_similar_case_studies("real estate firm slow listings page", top_k=2):
    print(r["title"], "-", round(r["similarity"], 3))

print("\n--- Salon query ---")
for r in find_similar_case_studies("salon outdated design no bookings", top_k=2):
    print(r["title"], "-", round(r["similarity"], 3))