import json
import re
import time
from typing import Optional

from core.logger import logger

from langchain_groq import ChatGroq
from httpx import TimeoutException, HTTPStatusError

from schema.enrich import EnrichmentResult, Enrich, prompt

GROQ_MODEL = "llama-3.1-8b-instant"
TAGS_MAX_WORDS = 10
CONTRIBUTION_MAX_WORDS = 20
REQUEST_INTERVAL_SECONDS = 2.1

def _extractive_contribution(abstract: str) -> str:
    if not abstract or not abstract.strip():
        return "Contribution unavailable."

    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', abstract.strip())
    source = sentences[1] if len(sentences) > 1 else sentences[0]
    source = source.strip()

    words = source.split()
    if len(words) > CONTRIBUTION_MAX_WORDS:
        source = " ".join(words[:CONTRIBUTION_MAX_WORDS]) + "..."

    return source

def _call_groq(llm: ChatGroq,abstract: str) -> Optional[dict]:

    structured_llm= llm.with_structured_output(Enrich)

    chain = prompt | structured_llm

    response = chain.invoke({
        "abstract":abstract,
        "tags_max":TAGS_MAX_WORDS,
        "contrib_max":CONTRIBUTION_MAX_WORDS,
    })

    tags = response.tags
    contribution = response.contribution

    if not tags or not contribution:
        logger.warning("Groq returned empty tags or contribution")
        return None

    return {"tags": tags, "contribution": contribution}    

# Public interface
def enrich_paper(
    llm: ChatGroq,
    abstract: str,
    title: str = "",
    rate_limit_sleep: bool = True,
) -> EnrichmentResult:
    """
    Enrich a single paper. Always returns a populated EnrichmentResult.

    Args:
        client:            Groq client instance (caller owns it)
        abstract:          Reconstructed plain-text abstract
        title:             Paper title (used only for logging context)
        rate_limit_sleep:  If True, sleep REQUEST_INTERVAL_SECONDS before call.
                           Set False when caller handles its own throttling.

    Returns:
        EnrichmentResult with tags, contribution, used_fallback, fallback_reason
    """
    # Guard: no abstract → skip Groq entirely
    if not abstract or not abstract.strip():
        logger.info("No abstract for '%s', using extractive fallback", title[:60])
        return EnrichmentResult(
            tags=[],
            contribution=_extractive_contribution(abstract),
            used_fallback=True,
            fallback_reason="no_abstract",
        )

    # Rate limit guard
    if rate_limit_sleep:
        time.sleep(REQUEST_INTERVAL_SECONDS)

    # Attempt Groq call
    try:
        result = _call_groq(llm, abstract)

        if result:
            return EnrichmentResult(
                tags=result["tags"],
                contribution=result["contribution"],
                used_fallback=False,
                fallback_reason=None,
            )
        else:
            # Groq responded but output was invalid
            logger.warning("Groq returned invalid output for '%s', falling back", title[:60])
            return EnrichmentResult(
                tags=[],
                contribution=_extractive_contribution(abstract),
                used_fallback=True,
                fallback_reason="invalid_output",
            )

    except TimeoutException as e:
        logger.warning(
            "Groq rate limit hit for '%s': %s. Using extractive fallback.",
            title[:60], str(e)
        )
        return EnrichmentResult(
            tags=[],
            contribution=_extractive_contribution(abstract),
            used_fallback=True,
            fallback_reason="rate_limit",
        )

    except HTTPStatusError as e:
        logger.error(
            "Groq API error for '%s': %s. Using extractive fallback.",
            title[:60], str(e)
        )
        return EnrichmentResult(
            tags=[],
            contribution=_extractive_contribution(abstract),
            used_fallback=True,
            fallback_reason=f"api_error:{e.status_code}",
        )

    except json.JSONDecodeError as e:
        logger.warning(
            "Groq returned non-JSON for '%s': %s. Using extractive fallback.",
            title[:60], str(e)
        )
        return EnrichmentResult(
            tags=[],
            contribution=_extractive_contribution(abstract),
            used_fallback=True,
            fallback_reason="json_parse_error",
        )

    except Exception as e:
        # Broad catch — pipeline must not crash on a single paper
        logger.exception("Unexpected error enriching '%s': %s", title[:60], str(e))
        return EnrichmentResult(
            tags=[],
            contribution=_extractive_contribution(abstract),
            used_fallback=True,
            fallback_reason=f"unexpected:{type(e).__name__}",
        )

def enrich_batch(
    llm: ChatGroq,
    papers: list[dict],
    progress_callback=None,
) -> list[tuple[str, EnrichmentResult]]:
    """
    Enrich a list of papers with built-in rate limiting.

    Args:
        client:            Groq client instance
        papers:            List of dicts with keys: openalex_id, abstract, title
        progress_callback: Optional callable(current, total, result) for progress tracking

    Returns:
        List of (openalex_id, EnrichmentResult) tuples, in input order.

    Rate limiting: sleeps REQUEST_INTERVAL_SECONDS between each call.
    Groq free tier = 30 req/min. At 2.1s intervals = ~28 req/min (safe headroom).

    For 2M papers: ~46 days. This is expected — use for daily_sync and incremental
    backfill, not for one-shot full backfill.
    """
    results = []
    total = len(papers)

    for i, paper in enumerate(papers):
        openalex_id = paper.get("openalex_id", f"unknown_{i}")
        abstract = paper.get("abstract", "")
        title = paper.get("title", "")

        # rate_limit_sleep=False here — batch handles its own sleep via loop
        if i > 0:
            time.sleep(REQUEST_INTERVAL_SECONDS)

        result = enrich_paper(
            llm=llm,
            abstract=abstract,
            title=title,
            rate_limit_sleep=False,
        )
        results.append((openalex_id, result))

        if progress_callback:
            progress_callback(i + 1, total, result)
        elif i % 100 == 0:
            fallback_count = sum(1 for _, r in results if r.used_fallback)
            logger.info(
                "Enriched %d/%d papers | fallbacks: %d",
                i + 1, total, fallback_count
            )

    return results


# Usage example (not called in production)
if __name__ == "__main__":
    """
    Smoke test — runs a single enrichment call with a real abstract.
    Requires GROQ_API_KEY in environment.

        python enrich.py
    """
    import os
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Set GROQ_API_KEY environment variable")
    
    llm = ChatGroq(
        model=GROQ_MODEL,
        temperature=0.1,
        groq_api_key=api_key
    )

    test_abstract = (
        "We propose a novel architecture for neural machine translation that "
        "relies entirely on attention mechanisms, dispensing with recurrence and "
        "convolutions entirely. The model, called the Transformer, achieves "
        "28.4 BLEU on the WMT 2014 English-to-German translation task, improving "
        "over the existing best results, including ensembles, by over 2 BLEU."
    )

    result = enrich_paper(
        llm=llm,
        abstract=test_abstract,
        title="Attention Is All You Need",
        rate_limit_sleep=False,
    )

    print(f"\nTags:          {result.tags}")
    print(f"Contribution:  {result.contribution}")
    print(f"Used fallback: {result.used_fallback}")
    print(f"Fallback reason: {result.fallback_reason}")