# LeadIQ: Multi-Agent Business Intelligence & Client Acquisition Engine

LeadIQ is an autonomous multi-agent pipeline built on LangGraph. It discovers local businesses on Google Maps, performs technical audits on their websites, scores them using a deterministic rubric, and drafts personalized, flaw-targeted outreach emails with human-in-the-loop approval.

---

## Directory Layout

```text
core/
├── config.py              # Environment variables, LLM clients (Groq), Supabase client
├── schemas.py             # Pydantic data models across all pipeline stages
├── scrapers/
│   ├── maps_discovery.py  # Google Maps scraper (Playwright)
│   └── site_crawler.py    # Local website auditor (Crawl4AI)
├── rag/
│   ├── vector_store.py    # Embeddings & case study lookup (Supabase pgvector)
│   └── seed_cases.py      # Database seeder for past client case studies
├── graph/
│   ├── nodes/
│   │   ├── critic.py      # Quality check on scraped data (filters bad leads early)
│   │   ├── scoring.py     # Deterministic 0–100 scoring math (no LLM calls)
│   │   └── outreach.py    # Personalized email drafter (website & no-website branches)
│   └── workflow.py        # Compiles the full pipeline into app_graph
├── run_batch.py           # CLI script to test the graph over multiple queries
└── test_integration.py    # End-to-end simulation of the backend handoff
```

---

## How the Pipeline Works

1. **Discovery (`core/scrapers/maps_discovery.py`)**  
   Searches Google Maps for a target niche and location (e.g., `"dental clinic"` in `"Bangalore"`). Emits structured `DiscoveredBusiness` records.

2. **Research (`core/scrapers/site_crawler.py`)**  
   Visits the business website and inspects performance (load time), tech stack, mobile readiness (click-to-call, WhatsApp buttons), SEO meta tags, and AI widgets. This is purely local parsing—no LLMs are called here.

3. **Critic (`core/graph/nodes/critic.py`)**  
   Sanity-checks the scraped data (filters junk emails like `test@gmail.com` and catches placeholder or parking pages). If the website crawl failed or lacked data, it retries once before proceeding.

4. **Scoring (`core/graph/nodes/scoring.py`)**  
   Pure deterministic math (0–100 score). No hallucination risk:  
   $$\text{Score} = (0.40 \times \text{Tech Pain}) + (0.30 \times \text{Commercial Intent}) + (0.30 \times \text{Contact Quality})$$
   - $\ge 70 \to$ **QUALIFIED** (gets a custom outreach draft)  
   - $65\text{–}69 \to$ **NEEDS_REVIEW** (also gets a draft for manual approval)  
   - $< 65 \to$ **DISQUALIFIED** (skipped)

5. **Outreach (`core/graph/nodes/outreach.py`)**  
   For qualified leads, it queries the Supabase vector store for relevant case studies and drafts a personalized email using `smart_llm`.
   - **Has Website:** Calls out specific website issues found during the audit and quotes a relevant case study.
   - **No Website:** Pitches the upside of building a simple landing page and quotes a relevant case study.

6. **Human-in-the-Loop Approval (`dispatch`)**  
   The graph is configured with `interrupt_before=["dispatch"]`. It generates the proposal and pauses. It **never** sends an email on its own until a human clicks "Approve" in the dashboard.

---

## Integrating with the Backend

Import the compiled graph directly from `core.graph.workflow`:

```python
from core.graph.workflow import app_graph

# 1. Start a run with a unique thread ID
config = {"configurable": {"thread_id": "unique-run-id"}}
initial_state = {
    "niche": "dental clinic",
    "location": "Bangalore",
    "batch_size": 1,
    "retry_count": 0,
    "error_log": [],
}

# 2. Stream until it pauses right before dispatch
for event in app_graph.stream(initial_state, config=config):
    pass

# 3. Pull the generated proposal for display in the UI
state = app_graph.get_state(config)
proposal = state.values.get("proposal_draft")
print(proposal.email_subject)
print(proposal.email_body_markdown)

# 4. When approved by a user, resume execution
for event in app_graph.stream(None, config=config):
    pass
```

A working simulation of this entire cycle can be found in `core/test_integration.py`.

---

## Setup & Configuration

### 1. Install Dependencies
```bash
pip install -r requirement.txt
python -m playwright install chromium
```

### 2. Environment Variables
Create a `.env` file in the project root with the following keys:

```ini
GROQ_API_KEY="your_groq_api_key"
GROQ_MODEL="openai/gpt-oss-120b"
GROQ_MODEL_SMART="qwen/qwen3.6-27b"

SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_KEY="your_supabase_anon_key"

LANGGRAPH_STRICT_MSGPACK=false
```

---

## Important: Groq Reasoning & Rate Limit Gotchas

1. **Deprecated Models:** `llama-3.1-8b-instant` and `llama-3.3-70b-versatile` were decommissioned by Groq. Make sure you are using active models like `openai/gpt-oss-120b` or `qwen/qwen3.6-27b`.
2. **Reasoning Models Leak Thoughts:** Reasoning models output internal `<think>...</think>` tokens by default. To prevent these thoughts from corrupting JSON payloads, keep `reasoning_format="parsed"` enabled on `ChatGroq`.
3. **The 1,000 Output Token Limit (429 Error):** Groq's on-demand free tier enforces an Output Tokens Per Minute (OTPM) ceiling of 1,000 tokens on certain models. If an LLM call doesn't specify `max_tokens`, Groq assumes the output could be 1,000+ tokens and immediately returns a `429 RateLimitError`. Always set `max_tokens=600` or `800` on reasoning models to stay inside the rate limits:

```python
smart_llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=GROQ_MODEL_SMART,
    temperature=0.3,
    max_tokens=600,
    reasoning_format="parsed"
)
```

---

## Running & Testing

Always run commands using `python -m` from the project root directory so Python can resolve internal module paths correctly:

```powershell
# Scrapers
python -m core.scrapers.maps_discovery
python -m core.scrapers.site_crawler

# Individual Nodes
python -m core.graph.nodes.critic
python -m core.graph.nodes.scoring
python -m core.graph.nodes.outreach

# Vector Store & RAG
python -m core.rag.vector_store

# End-to-End Simulation
python -m core.test_integration
```

---

## Known Edge Cases

- **Google Maps Ratings:** Google frequently rotates the DOM on Maps listings. If the rating span can't be parsed, it falls back to `None` without stopping the pipeline.
- **Bot-Blocked Sites:** If a target site has strict Cloudflare or bot protection, the crawler fails cleanly. The Critic treats this as missing data rather than an exception, and the lead is scored on whatever data is available.
- **LangGraph Checkpoint Warnings:** You may see `Deserializing unregistered type` warnings when resuming state. This is harmless in LangGraph >= 1.2, and setting `LANGGRAPH_STRICT_MSGPACK=false` keeps it quiet.
