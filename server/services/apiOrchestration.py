from dotenv import load_dotenv
load_dotenv()
import os

import requests
from typing import List, Dict

api_key = os.getenv("OPEN_ALEX_API_KEY")
if not api_key:
    raise ValueError("OPEN_ALEX_API_KEY not set")

def reconstruct_abstract(index) -> str:
    if not index:
        return None

    length = max(pos for positions in index.values() for pos in positions) + 1
    words = [""] * length

    for word, positions in index.items():
        for pos in positions:
            words[pos] = word

    return " ".join(words)

def parse_work(work) -> Dict:

    abstract = reconstruct_abstract(work.get("abstract_inverted_index"))

    authors = []
    for a in work.get("authorships", []):
        author = a.get("author", {})

        author_id = None
        if author.get("id"):
            author_id = author["id"].split("/")[-1]

        authors.append({
            "name": author.get("display_name"),
            "openalex_id": author_id,
            "institution": (
                a["institutions"][0]["display_name"]
                if a.get("institutions") else None
            )
        })

    venue = None
    if work.get("primary_location") and work["primary_location"].get("source"):
        venue = work["primary_location"]["source"]["display_name"]

    fields = [c["display_name"] for c in work.get("concepts", [])[:3]]

    return {
        "openalex_id": work["id"].split("/")[-1],
        "doi": (work.get("doi") or "").replace("https://doi.org/", ""),
        "title": work.get("display_name"),
        "abstract": abstract,
        "authors": authors,
        "venue": venue,
        "year": work.get("publication_year"),
        "fields": fields,
        "citation_count": work.get("cited_by_count"),
        "counts_by_year": work.get("counts_by_year"),
        "referenced_works": [
            r.split("/")[-1] for r in work.get("referenced_works", [])
        ],
        "open_access": work.get("open_access", {}).get("is_oa"),
        "updated_date": work.get("updated_date")
    }


def get_data(pub_year:int , per_pg:int) -> List[Dict]:
    raw_data = requests.get(
        f"https://api.openalex.org/works?filter=publication_year:{pub_year}&sort=publication_date:desc&per_page={per_pg}&cursor=*&api_key={api_key}"
    , timeout=10).json()
    
    parsed_opt=[]
    for work in raw_data["results"]:
        parsed=parse_work(work)
        parsed_opt.append(parsed)
    
    return parsed_opt

if __name__ == "__main__":
    print(get_data(2026,5))