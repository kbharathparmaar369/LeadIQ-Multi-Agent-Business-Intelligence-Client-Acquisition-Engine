from core.schemas import DiscoveredBusiness, compute_lead_status, LeadStatus

# Test 1: basic model creation
b = DiscoveredBusiness(business_name="Smile Dental", location="Bangalore", niche="dental clinic")
print(b)

# Test 2: status boundaries
assert compute_lead_status(75) == LeadStatus.QUALIFIED
assert compute_lead_status(67) == LeadStatus.NEEDS_REVIEW
assert compute_lead_status(50) == LeadStatus.DISQUALIFIED
print("All status boundary checks passed")