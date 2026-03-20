from core.config import settings
from core.logger import get_logger
import requests
import time
from typing import List, Dict, Optional, Iterator

logger=get_logger(__name__)

api_key = settings.OPEN_ALEX_API_KEY

BASE_URL = "https://api.openalex.org/works"
DEFAULT_PER_PAGE = 200          # OpenAlex max per page
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_SEC = 2         # doubles on each retry
DEFAULT_LIMIT = 100


def _reconstruct_abstract(index: Optional[Dict]) -> str:
    if not index:
        return ""
    try:
        length = max(pos for positions in index.values() for pos in positions) + 1
        words = [""] * length

        for word, positions in index.items():
            for pos in positions:
                words[pos] = word

        return " ".join(w for w in words if w).strip()
    except(ValueError,TypeError):
        return ""

def _parse_authors(authorships: List[Dict]) -> List[Dict]:
    authors = []
    for a in authorships:
        author = a.get("author") or {}
        raw_id = author.get("id") or ""
        institutions = a.get("institutions") or []
        authors.append({
            "name": author.get("display_name") or "Unknown",
            "openalex_id": raw_id.split("/")[-1] if raw_id else None,
            "institution": institutions[0].get("display_name") if institutions else None,
        })
    return authors

def _parse_work(work) -> Dict:
    # Title
    title = work.get("display_name") or work.get("title") or None
    
    # Venue
    primary_loc=work.get("primary_location") or {}
    source = primary_loc.get("source") or {}
    venue=source.get("display_name") or None
    
    # Concept fields
    concepts = work.get("concepts") or []
    fields = [c["display_name"] for c in concepts[:3] if c.get("display_name")]

    # DOI
    doi=work.get("doi") or ""

    # OpenAlex ID
    work_id_r=work.get("id") or ""
    openalex_id = work_id_r.split("/")[-1] if work_id_r else None

    # Referenced works IDs
    referenced_works = [
        r.split("/")[-1]
        for r in (work.get("referenced_works") or [])
        if r
    ]


    return {
        "openalex_id": openalex_id,
        "doi": doi,
        "title": title,
        "abstract": _reconstruct_abstract(work.get("abstract_inverted_index")),
        "authors": _parse_authors(work.get("authorships") or []),
        "venue": venue,
        "year": work.get("publication_year"),
        "fields": fields or None,
        "citation_count": work.get("cited_by_count",0),
        "counts_by_year": work.get("counts_by_year") or [],
        "referenced_works": referenced_works,
        "open_access": work.get("open_access", {}).get("is_oa"),
        "updated_date": work.get("updated_date") or None,
    }

def _fetch_page(
    params: Dict,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff: int = DEFAULT_BACKOFF_SEC
    ):
    for attempt in range(1,max_retries+1):
        try:
            response= requests.get(BASE_URL,params=params,timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429 or attempt < max_retries:
                wait = backoff * (2 ** (attempt - 1))
                logger.warning("HTTP %s on attempt %d/%d — retrying in %.1fs",
                               response.status_code, attempt, max_retries, wait)
                time.sleep(wait)
            else:
                logger.error(f"HTTP error after {max_retries} attempts: {e}")
                return None
        except requests.exceptions.RequestException as e:
            if attempt < max_retries:
                wait = backoff * (2 ** (attempt - 1))
                logger.warning("Request error on attempt %d/%d: %s — retrying in %.1fs",
                               attempt, max_retries, e, wait)
                time.sleep(wait)
            else:
                logger.error("Request failed after %d attempts: %s", max_retries, e)
                return None
    return None

def _iter_pages(
    pub_year: int,
    per_page: int = DEFAULT_PER_PAGE,
    max_retries: int = DEFAULT_MAX_RETRIES,
    extra_filters: Optional[str] = None,
    ) -> Iterator[List[Dict]]:

    filters = f"publication_year:{pub_year}"
    if extra_filters:
        filters+=f",{extra_filters}"
    
    params = {
        "filter": filters,
        "sort": "publication_date:desc",
        "per_page": per_page,
        "cursor": "*",          
        "api_key": api_key,
    }

    page_num = 0
    while True:
        page_num += 1
        cursor=params["cursor"]
        logger.info(f"Fetching page {page_num} (cursor={cursor})…")

        data = _fetch_page(params, max_retries=max_retries)
        if not data:
            logger.error("Empty response on page %d — stopping.", page_num)
            break

        results = data.get("results") or []
        if not results:
            logger.info("No more results after page %d.", page_num - 1)
            break

        yield results

        # Advance the cursor for the next page
        next_cursor = (data.get("meta") or {}).get("next_cursor")
        if not next_cursor:
            logger.info("No next_cursor — all pages fetched.")
            break

        params["cursor"] = next_cursor

        # Be polite to the API (~ 10 req/s guideline)
        time.sleep(0.1)

def fetch_single_work(openalex_id: str) -> Optional[Dict]:
    """Fetch a single work by its OpenAlex ID."""
    # Ensure ID doesn't have the https prefix if passed that way
    if openalex_id.startswith("https://api.openalex.org/works/"):
        openalex_id = openalex_id.split("/")[-1]
    
    url = f"{BASE_URL}/{openalex_id}"
    params = {"api_key": api_key} if api_key else {}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        work = response.json()
        return _parse_work(work)
    except Exception as e:
        logger.error(f"Failed to fetch single work {openalex_id}: {e}")
        return None

def get_data(
        pub_year:int , 
        limit: Optional[int] = DEFAULT_LIMIT,
        per_page:int= DEFAULT_PER_PAGE,
        skip_missing_abstract: bool=True,
        skip_missing_doi: bool=True,
        extra_filters: Optional[str]= None,
        max_retries: int= DEFAULT_MAX_RETRIES
    ) -> Iterator[Dict]:
    pass

def stream_data(
        pub_year:int , 
        limit: Optional[int] = DEFAULT_LIMIT,
        per_page:int= DEFAULT_PER_PAGE,
        skip_missing_abstract: bool=True,
        skip_missing_doi: bool=True,
        extra_filters: Optional[str]= None,
        max_retries: int= DEFAULT_MAX_RETRIES
    ) -> Iterator[Dict]:
    count =0
    for r_page in _iter_pages(pub_year,per_page,max_retries,extra_filters):
        for work in r_page:
            parsed = _parse_work(work)
            if skip_missing_abstract and not parsed.get("abstract"):
                continue
            if skip_missing_doi and not parsed.get("doi"):
                continue
            count+=1
            yield parsed

            if limit and count >= limit:
                logger.info(f"Reached requested limit of {limit} papers.")
                return
        logger.info(f"Collected {count} papers so far...")
    logger.info(f"Done, Total papers fetched: {count}")

