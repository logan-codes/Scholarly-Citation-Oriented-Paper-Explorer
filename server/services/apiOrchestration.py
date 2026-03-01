import requests
import feedparser

def fetch_arxiv(query, max_results=5):
    url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={max_results}"

    response = requests.get(url)
    feed = feedparser.parse(response.text)

    papers = []
    for entry in feed.entries:
        papers.append({
            "source": "arXiv",
            "title": entry.title,
            "authors": [author.name for author in entry.authors],
            "abstract": entry.summary,
            "published": entry.published,
            "pdf_link": entry.link
        })

    return papers


def fetch_semantic_scholar(query, limit=5):
    url = "https://api.semanticscholar.org/graph/v1/paper/search"

    params = {
        "query": query,
        "limit": limit,
        "fields": "title,authors,year,abstract,citationCount,doi,url"
    }

    response = requests.get(url, params=params)
    data = response.json()

    papers = []
    for paper in data.get("data", []):
        papers.append({
            "source": "Semantic Scholar",
            "title": paper.get("title"),
            "authors": [author["name"] for author in paper.get("authors", [])],
            "abstract": paper.get("abstract"),
            "year": paper.get("year"),
            "citations": paper.get("citationCount"),
            "doi": paper.get("doi"),
            "url": paper.get("url")
        })

    return papers

def fetch_core(query, api_key, limit=5):
    url = "https://api.core.ac.uk/v3/search/works"

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "q": query,
        "limit": limit
    }

    response = requests.post(url, headers=headers, json=data)
    results = response.json()

    papers = []
    for paper in results.get("results", []):
        papers.append({
            "source": "CORE",
            "title": paper.get("title"),
            "authors": paper.get("authors"),
            "abstract": paper.get("abstract"),
            "year": paper.get("yearPublished"),
            "doi": paper.get("doi"),
            "url": paper.get("downloadUrl")
        })

    return papers