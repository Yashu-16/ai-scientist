# AI Scientist — Biomedical Hypothesis Generation Platform

> Generate evidence-backed biomedical hypotheses by combining protein biology, drug data, and scientific literature with LLM reasoning.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-orange)

## What It Does

Input a disease name → Get:
- **Protein targets** with association scores (OpenTargets)
- **Drug-protein mappings** with FDA adverse event signals
- **Research papers** from PubMed + Semantic Scholar  
- **AI-generated hypotheses** with confidence scores

## Architecture
```
Disease Name
    ↓
[OpenTargets API]     → Protein targets + association scores
    ↓
[OpenTargets + FDA]   → Drug mappings + adverse event signals
    ↓
[PubMed + Semantic Scholar] → Research paper evidence
    ↓
[GPT-4o-mini]         → Evidence-backed hypothesis generation
    ↓
Structured hypotheses with confidence scores
```

## Quick Start

### 1. Clone & Setup
```powershell
git clone https://github.com/YOUR_USERNAME/ai-scientist.git
cd ai-scientist
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment
```powershell
copy .env.example .env
# Edit .env and add your API keys
```

### 3. Run Backend
```powershell
uvicorn backend.main:app --reload --port 8000
```

### 4. Run Frontend
```powershell
streamlit run frontend/app.py
```

Open `http://localhost:8501`

## API Keys Required

| Key | Where to Get | Cost |
|-----|-------------|------|
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) | ~$0.01/analysis |
| `PUBMED_EMAIL` | Just your email address | Free |

Optional: `GROQ_API_KEY` from [console.groq.com](https://console.groq.com) (free alternative to OpenAI)

## Project Structure
```
ai-scientist/
├── backend/
│   ├── main.py                    ← FastAPI app
│   ├── services/
│   │   ├── protein_service.py     ← OpenTargets API
│   │   ├── drug_service.py        ← Drug + FDA FAERS
│   │   ├── paper_service.py       ← PubMed + Semantic Scholar
│   │   ├── hypothesis_service.py  ← LLM hypothesis generation
│   │   └── pipeline_service.py    ← Pipeline orchestrator
│   └── models/
│       └── schemas.py             ← Pydantic data models
├── frontend/
│   └── app.py                     ← Streamlit UI
├── .env.example
├── requirements.txt
└── README.md
```

## Data Sources

- **[OpenTargets](https://platform.opentargets.org/)** — Disease-protein associations
- **[FDA FAERS](https://open.fda.gov/apis/drug/event/)** — Drug adverse events
- **[PubMed](https://pubmed.ncbi.nlm.nih.gov/)** — Biomedical literature
- **[Semantic Scholar](https://www.semanticscholar.org/)** — AI paper summaries

## Disclaimer

This tool generates AI-assisted research hypotheses for exploratory purposes only. 
Not intended for clinical use or medical decision-making.