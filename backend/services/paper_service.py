# backend/services/paper_service.py
# Purpose: Fetch relevant research papers using Semantic Scholar API
# and PubMed API (both free, no key required for basic usage)

import requests
import os
from dotenv import load_dotenv

load_dotenv()

# API endpoints
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1"
PUBMED_SEARCH_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH_API  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# Your email for PubMed (set in .env)
PUBMED_EMAIL = os.getenv("PUBMED_EMAIL", "researcher@example.com")


def fetch_papers_semantic_scholar(query: str, max_results: int = 5) -> list:
    """
    Fetch research papers from Semantic Scholar.
    Includes retry logic for 429 rate limiting.
    """
    import time

    endpoint = f"{SEMANTIC_SCHOLAR_API}/paper/search"

    params = {
        "query":  query,
        "limit":  max_results,
        "fields": "title,abstract,authors,year,citationCount,externalIds,tldr"
    }

    # Retry up to 3 times with increasing delays for rate limiting
    for attempt in range(3):
        try:
            response = requests.get(endpoint, params=params, timeout=30)

            if response.status_code == 429:
                wait = (attempt + 1) * 5  # 5s, 10s, 15s
                print(f"  ⏳ Semantic Scholar rate limit — waiting {wait}s (attempt {attempt+1}/3)...")
                time.sleep(wait)
                continue

            response.raise_for_status()
            data = response.json()

            papers = []
            for paper in data.get("data", []):
                tldr    = paper.get("tldr", {})
                summary = tldr.get("text", "") if tldr else ""
                authors = [a.get("name", "") for a in paper.get("authors", [])]

                papers.append({
                    "source":         "Semantic Scholar",
                    "title":          paper.get("title", "No title"),
                    "abstract":       paper.get("abstract") or "No abstract available",
                    "summary":        summary or "No summary available",
                    "authors":        authors[:3],
                    "year":           paper.get("year"),
                    "citation_count": paper.get("citationCount", 0),
                    "paper_id":       paper.get("paperId", "")
                })

            return papers

        except requests.exceptions.RequestException as e:
            print(f"  Semantic Scholar error: {e}")
            return []

    print("  ⚠️  Semantic Scholar unavailable after retries — using PubMed only")
    return []


def fetch_papers_pubmed(query: str, max_results: int = 5) -> list:
    """
    Fetch research papers from PubMed (NCBI).
    Two-step process: search for IDs, then fetch details.
    """
    
    # Step 1: Search for paper IDs
    search_params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
        "sort": "relevance",
        "email": PUBMED_EMAIL
    }
    
    try:
        search_response = requests.get(
            PUBMED_SEARCH_API, 
            params=search_params, 
            timeout=30
        )
        search_response.raise_for_status()
        search_data = search_response.json()
        
        ids = search_data.get("esearchresult", {}).get("idlist", [])
        
        if not ids:
            return []
        
        # Step 2: Fetch paper details using the IDs
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "xml",
            "rettype": "abstract",
            "email": PUBMED_EMAIL
        }
        
        fetch_response = requests.get(
            PUBMED_FETCH_API, 
            params=fetch_params, 
            timeout=30
        )
        fetch_response.raise_for_status()
        
        # Parse the XML response manually (avoid heavy XML libraries)
        papers = parse_pubmed_xml(fetch_response.text, ids)
        return papers
        
    except requests.exceptions.RequestException as e:
        print(f"  PubMed error: {e}")
        return []


def parse_pubmed_xml(xml_text: str, ids: list) -> list:
    """
    Simple XML parser for PubMed responses.
    Extracts title and abstract without heavy dependencies.
    """
    import re
    papers = []
    
    # Split by article
    articles = xml_text.split("<PubmedArticle>")
    
    for i, article in enumerate(articles[1:], 0):  # Skip first empty split
        
        # Extract title
        title_match = re.search(
            r"<ArticleTitle>(.*?)</ArticleTitle>", 
            article, re.DOTALL
        )
        title = title_match.group(1).strip() if title_match else "No title"
        # Clean XML tags from title
        title = re.sub(r"<[^>]+>", "", title)
        
        # Extract abstract
        abstract_match = re.search(
            r"<AbstractText.*?>(.*?)</AbstractText>", 
            article, re.DOTALL
        )
        abstract = abstract_match.group(1).strip() if abstract_match else "No abstract"
        abstract = re.sub(r"<[^>]+>", "", abstract)
        
        # Extract year
        year_match = re.search(r"<PubDate>.*?<Year>(\d{4})</Year>", article, re.DOTALL)
        year = int(year_match.group(1)) if year_match else None
        
        # Get PMID
        pmid = ids[i] if i < len(ids) else ""
        
        papers.append({
            "source": "PubMed",
            "title": title[:200],
            "abstract": abstract[:500],
            "summary": abstract[:150] + "..." if len(abstract) > 150 else abstract,
            "authors": [],
            "year": year,
            "citation_count": 0,
            "paper_id": f"PMID:{pmid}",
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        })
    
    return papers


def fetch_papers_for_disease(disease_name: str, protein_symbol: str = "", max_results: int = 5) -> dict:
    """
    Master function: Fetch papers from both sources and combine.
    
    Args:
        disease_name: e.g., "Alzheimer disease"
        protein_symbol: e.g., "APOE" (optional, narrows search)
        max_results: papers per source
    
    Returns combined, deduplicated paper list
    """
    
    # Build search query
    if protein_symbol:
        query = f"{disease_name} {protein_symbol} treatment mechanism"
    else:
        query = f"{disease_name} molecular target therapy"
    
    print(f"  → Searching papers for: '{query}'")
    
    # Fetch from both sources
    ss_papers  = fetch_papers_semantic_scholar(query, max_results)
    pm_papers  = fetch_papers_pubmed(query, max_results)
    
    all_papers = ss_papers + pm_papers
    
    # Simple deduplication by title similarity
    seen_titles = set()
    unique_papers = []
    for paper in all_papers:
        title_key = paper["title"][:50].lower().strip()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_papers.append(paper)
    
    # Sort by citation count (most cited first)
    unique_papers.sort(key=lambda x: x.get("citation_count", 0), reverse=True)
    
    return {
        "query": query,
        "total_papers": len(unique_papers),
        "papers": unique_papers
    }


# ── Quick test ──────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing Paper Retrieval APIs...")
    print("=" * 50)
    
    result = fetch_papers_for_disease(
        disease_name="Alzheimer disease",
        protein_symbol="APOE",
        max_results=3
    )
    
    print(f"\nTotal papers found: {result['total_papers']}")
    print(f"Query used: {result['query']}")
    print("\nPapers:")
    print("-" * 50)
    
    for i, paper in enumerate(result["papers"], 1):
        print(f"{i}. [{paper['source']}] {paper['title'][:80]}")
        print(f"   Year: {paper['year']} | Citations: {paper['citation_count']}")
        print(f"   Summary: {paper['summary'][:120]}...")
        print()