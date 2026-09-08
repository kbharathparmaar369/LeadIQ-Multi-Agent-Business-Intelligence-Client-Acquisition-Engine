# core/ — AI Engine (Person A)

This folder contains the entire AI/agentic pipeline for the Lead Intelligence Engine.
It discovers businesses, audits their websites, scores them as leads, and drafts
outreach emails — all compiled into a single LangGraph workflow that Person B's
backend imports and runs.

> 📖 **Looking for a beginner-friendly, step-by-step breakdown?** Check out [**`HOW_IT_WORKS.md`**](file:///d:/MY%20PROJECTS/lead-intelligence-engine/HOW_IT_WORKS.md) for a plain-English explanation, visual flowchart, and component guide.

## Folder structure

```text
core/
├── config.py           # Loads .env, exposes fast_llm, smart_llm, supabase
├── schemas.py          # Single source of truth for all data shapes
├── scrapers/
│   ├── maps_discovery.py # Google Maps scraper (Playwright)
│   └── site_crawler.py   # Website auditor (Crawl4AI)
├── rag/
│   ├── vector_store.py # Embeddings + similarity search (Supabase pgvector)
│   └── seed_cases.py   # Seeds case_studies table with example projects
├── graph/
│   ├── nodes/
│   │   ├── critic.py   # Validates scraped data, flags issues
│   │   ├── scoring.py  # Deterministic 0-100 lead scoring rubric
│   │   └── outreach.py # Drafts cold emails (website + no-website paths)
│   └── workflow.py     # Compiles everything into app_graph
├── run_batch.py        # Local tool: run the graph across multiple leads
└── test_integration.py # Simulates what Person B's backend will do with app_graph
```

## What each stage does

1. **Discovery** (`scrapers/maps_discovery.py`) — scrapes Google Maps for businesses
   matching a niche + location. Returns `DiscoveredBusiness` objects.

2. **Research** (`scrapers/site_crawler.py`) — crawls a business's website and checks
   5 categories: performance, tech stack, conversion/CRO, SEO/metadata, AI-readiness.
   Returns `SiteAuditData`. Pure local parsing, no LLM calls.

3. **Critic** (`graph/nodes/critic.py`) — validates the scraped data. Checks email
   quality (placeholder/personal-domain detection) and does one `fast_llm` call on a
   small cleaned summary (never raw HTML) to catch mismatches like a "coming soon"
   headline. If completeness is too low, the graph retries Research once (max 1 retry,
   then falls back to scoring with whatever data exists).

4. **Scoring** (`graph/nodes/scoring.py`) — pure deterministic math, no LLM:

   `Score = (0.40 × Tech Pain) + (0.30 × Commercial Intent) + (0.30 × Contact Quality)`

   Score ≥ 70 → QUALIFIED, 65-69 → NEEDS_REVIEW, below 65 → DISQUALIFIED.

5. **Outreach** (`graph/nodes/outreach.py`) — for qualified/needs-review leads, pulls
   matching case studies via RAG and drafts a personalized email with `smart_llm`.
   Two paths: `draft_proposal` (business has a website, cites specific flaws) and
   `draft_no_website_proposal` (no website at all, pitches building one from scratch).

6. **Dispatch (HITL checkpoint)** — the graph pauses right before dispatch
   (`interrupt_before=["dispatch"]`). Nothing is sent automatically. Person B's
   backend resumes the graph after a human approves the draft in the React UI.

## The main entry point

Person B's backend imports the compiled graph like this:

```python
from core.graph.workflow import app_graph
```

Basic usage pattern:

```python
config = {"configurable": {"thread_id": "some-unique-id"}}

# Run until it pauses before dispatch
for event in app_graph.stream(initial_state, config=config):
    ...

# Check the pending proposal
state = app_graph.get_state(config)
proposal = state.values.get("proposal_draft")

# Resume after human approval
for event in app_graph.stream(None, config=config):
    ...
```

See `test_integration.py` for a full worked example of this pattern (search request →
show proposal → approve → dispatch payload).

## Environment setup

Copy `.env.example` to `.env` and fill in:
- `GROQ_API_KEY`
- `SUPABASE_URL`, `SUPABASE_KEY`

Run `pip install -r requirement.txt` then `python -m playwright install chromium`.

## IMPORTANT: Groq model gotcha (read this before touching LLM code)

`llama-3.1-8b-instant` and `llama-3.3-70b-versatile` were **deprecated by Groq on
August 16, 2026**. If you're setting this up fresh, do NOT use those model names —
they no longer exist and every request will fail.

Current working config:

```ini
GROQ_MODEL=openai/gpt-oss-120b
GROQ_MODEL_SMART=qwen/qwen3.6-27b
```

**Every model currently available on Groq's free tier is a reasoning model** — meaning
it "thinks" internally before answering, and by default that thinking leaks into the
response as `<think>...</think>` tags, breaking JSON parsing. Two settings in
`config.py` fix this:

```python
smart_llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=GROQ_MODEL_SMART,
    temperature=0.2,
    max_tokens=600,              # keeps reasoning under the 1000 token rate limit
    reasoning_format="parsed"    # keeps reasoning out of .content
)
```

Without `max_tokens` set, the model's internal reasoning alone can exceed the
free tier's ~1000 output-tokens-per-minute limit, causing `429 rate_limit_exceeded`
errors even on a single request. Without `reasoning_format="parsed"`, the reasoning
text leaks into the answer and breaks JSON parsing.

If Groq deprecates these models in the future too, check
`https://console.groq.com/docs/deprecations` for the current replacement, and confirm
whether it's a reasoning model — if so, apply the same two settings above.

## Known non-blocking issues

- LangGraph shows `Deserializing unregistered type` warnings for the Pydantic schema
  types during checkpointing. Doesn't break anything currently (tested on
  `langgraph==1.2.11`). Set `LANGGRAPH_STRICT_MSGPACK=false` in `.env` if you want to
  silence the underlying concern explicitly. Revisit if upgrading langgraph ever turns
  this into a hard failure instead of a warning.
- `maps_discovery.py`'s rating extraction is unreliable due to Google's DOM structure;
  left as `None` when it fails. Non-blocking since `rating` is optional everywhere
  downstream.
- Anti-bot-protected sites (some real dental clinic sites hit this) fail cleanly during
  Research — the Critic's retry loop handles this gracefully, and the business just
  scores low on completeness rather than crashing the pipeline.

## Testing individual pieces

Always run tests using `python -m` from the project root directory:

```powershell
python -m core.scrapers.maps_discovery
python -m core.scrapers.site_crawler
python -m core.graph.nodes.critic
python -m core.graph.nodes.scoring
python -m core.rag.vector_store
python -m core.graph.nodes.outreach
python -m core.graph.workflow
python -m core.run_batch
python -m core.test_integration
```
