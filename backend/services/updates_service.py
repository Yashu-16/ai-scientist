# backend/services/updates_service.py
# Feature 7: Real-Time Scientific Updates Engine
# Monitors PubMed daily for new papers on tracked diseases
# Stores updates in memory cache with timestamps
# Exposed via /latest-updates endpoint

import time
import requests
from datetime import datetime, timedelta
from typing import Optional


# ── In-Memory Updates Store ───────────────────────────────────
class UpdatesStore:
    """
    Simple in-memory store for scientific updates.
    Tracks new papers per disease with timestamps.
    """

    def __init__(self):
        self._updates:  dict = {}   # disease → list of updates
        self._tracked:  list = []   # diseases being monitored
        self._last_check: Optional[datetime] = None
        self._check_count: int = 0

    def add_tracked_disease(self, disease_name: str):
        """Add a disease to the monitoring list."""
        if disease_name not in self._tracked:
            self._tracked.append(disease_name)
            print(f"   📡 Now tracking: {disease_name}")

    def get_tracked_diseases(self) -> list:
        return self._tracked.copy()

    def store_updates(self, disease_name: str, papers: list):
        """Store new paper updates for a disease."""
        if disease_name not in self._updates:
            self._updates[disease_name] = []

        for paper in papers:
            # Add timestamp
            paper["fetched_at"] = datetime.now().isoformat()
            self._updates[disease_name].append(paper)

        # Keep only last 20 updates per disease
        self._updates[disease_name] = \
            self._updates[disease_name][-20:]

    def get_updates(self, disease_name: str = None) -> dict:
        """Get updates for a disease or all diseases."""
        if disease_name:
            return {
                disease_name: self._updates.get(disease_name, [])
            }
        return dict(self._updates)

    def get_stats(self) -> dict:
        return {
            "tracked_diseases": self._tracked,
            "total_updates":    sum(
                len(v) for v in self._updates.values()
            ),
            "last_check":       self._last_check.isoformat()
                                if self._last_check else None,
            "check_count":      self._check_count,
            "updates_per_disease": {
                k: len(v) for k, v in self._updates.items()
            }
        }

    def mark_checked(self):
        self._last_check = datetime.now()
        self._check_count += 1


# Global store instance
updates_store = UpdatesStore()

# Pre-track common diseases
DEFAULT_TRACKED = [
    "Alzheimer disease",
    "Parkinson disease",
    "breast cancer",
    "type 2 diabetes"
]
for d in DEFAULT_TRACKED:
    updates_store.add_tracked_disease(d)


# ── PubMed Recent Papers Fetcher ──────────────────────────────
PUBMED_SEARCH_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH_API  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def fetch_recent_papers(
    disease_name: str,
    days_back:    int = 7,
    max_results:  int = 5
) -> list:
    """
    Fetch papers published in the last N days for a disease.
    Uses PubMed date filter to get only recent publications.
    """
    # Calculate date range
    end_date   = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    date_str   = (
        f"{start_date.strftime('%Y/%m/%d')}:"
        f"{end_date.strftime('%Y/%m/%d')}[dp]"
    )

    query = f"{disease_name} drug therapy mechanism {date_str}"

    search_params = {
        "db":      "pubmed",
        "term":    query,
        "retmax":  max_results,
        "retmode": "json",
        "sort":    "pub+date",
        "email":   "researcher@example.com"
    }

    try:
        r = requests.get(PUBMED_SEARCH_API,
                         params=search_params, timeout=15)
        r.raise_for_status()
        data = r.json()
        ids  = data.get("esearchresult", {}).get("idlist", [])

        if not ids:
            return []

        # Fetch details
        fetch_params = {
            "db":      "pubmed",
            "id":      ",".join(ids),
            "retmode": "xml",
            "rettype": "abstract",
            "email":   "researcher@example.com"
        }
        fr = requests.get(PUBMED_FETCH_API,
                          params=fetch_params, timeout=15)
        fr.raise_for_status()

        papers = _parse_recent_papers(fr.text, ids, disease_name)
        return papers

    except Exception as e:
        print(f"   ⚠️  PubMed fetch error for {disease_name}: {e}")
        return []


def _parse_recent_papers(xml_text: str, ids: list,
                          disease_name: str) -> list:
    """Parse PubMed XML into paper dicts."""
    import re
    papers = []

    articles = xml_text.split("<PubmedArticle>")
    for i, article in enumerate(articles[1:], 0):
        if i >= len(ids):
            break

        title_m = re.search(
            r"<ArticleTitle>(.*?)</ArticleTitle>",
            article, re.DOTALL
        )
        title = re.sub(r"<[^>]+>", "",
                       title_m.group(1).strip()) if title_m else "No title"

        abstract_m = re.search(
            r"<AbstractText.*?>(.*?)</AbstractText>",
            article, re.DOTALL
        )
        abstract = re.sub(
            r"<[^>]+>", "",
            abstract_m.group(1).strip()
        ) if abstract_m else ""

        year_m = re.search(
            r"<PubDate>.*?<Year>(\d{4})</Year>",
            article, re.DOTALL
        )
        year = int(year_m.group(1)) if year_m else datetime.now().year

        pmid = ids[i]
        papers.append({
            "title":       title[:150],
            "abstract":    abstract[:300],
            "year":        year,
            "pmid":        pmid,
            "url":         f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "disease":     disease_name,
            "source":      "PubMed",
            "is_new":      True
        })

    return papers


# ── Scheduled Update Job ──────────────────────────────────────
def run_update_check():
    """
    Main job: check PubMed for new papers on all tracked diseases.
    Called by APScheduler daily (or on-demand).
    """
    tracked = updates_store.get_tracked_diseases()
    print(f"\n🔄 Running scientific update check...")
    print(f"   Tracking {len(tracked)} diseases")

    total_new = 0

    for disease in tracked:
        print(f"   📡 Checking: {disease}")
        papers = fetch_recent_papers(disease, days_back=7, max_results=3)

        if papers:
            updates_store.store_updates(disease, papers)
            print(f"      ✅ Found {len(papers)} recent papers")
            total_new += len(papers)
        else:
            print(f"      ℹ️  No new papers found")

        time.sleep(1)   # Rate limiting between requests

    updates_store.mark_checked()
    print(f"\n✅ Update check complete: {total_new} new papers found")
    return total_new


def setup_scheduler(app):
    """
    Set up APScheduler to run daily update checks.
    Attaches to FastAPI app lifecycle.
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler

        scheduler = BackgroundScheduler(timezone="UTC")

        # Run daily at 6 AM UTC
        scheduler.add_job(
            run_update_check,
            trigger   = "cron",
            hour      = 6,
            minute    = 0,
            id        = "daily_updates",
            name      = "Daily PubMed Update Check",
            replace_existing = True
        )

        scheduler.start()
        print("📅 Scheduler started — daily updates at 06:00 UTC")
        return scheduler

    except Exception as e:
        print(f"⚠️  Scheduler setup failed: {e}")
        return None


# ── Quick test ────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing Updates Service...")
    print("=" * 50)

    # Test fetching recent papers
    print("\n📡 Fetching recent Alzheimer papers...")
    papers = fetch_recent_papers("Alzheimer disease", days_back=30,
                                 max_results=3)
    print(f"Found {len(papers)} papers")
    for p in papers:
        print(f"  • [{p['year']}] {p['title'][:70]}")
        print(f"    URL: {p['url']}")

    # Test store
    updates_store.store_updates("Alzheimer disease", papers)
    stats = updates_store.get_stats()
    print(f"\nStore stats: {stats}")
    print("✅ Updates service working!")