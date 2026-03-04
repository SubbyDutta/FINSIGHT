from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import json
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.services.research_agent_service import generate_research_report
from app.schemas.research_report_schema import ResearchReport

router = APIRouter(prefix="/agent", tags=["Agent"])


@router.post("/research/{ticker}")
def run_research(ticker: str, db: Session = Depends(get_db)):

    try:
        result = generate_research_report(db, ticker.upper())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    report: ResearchReport = result["report"]

    return {
        "ticker": report.ticker,
        "generated_at": report.generated_at,
        "summary": report.summary,
        "recommendation": report.recommendation,
        "pdf_path": result["pdf_path"]
    }

@router.get("/report/{ticker}")
def get_report(ticker: str):

    ticker = ticker.upper()

    path = Path(f"reports/{ticker}/latest_report.json")

    if not path.exists():
        raise HTTPException(status_code=404, detail="Report not found")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    return data


@router.get("/report/{ticker}/pdf")
def get_report_pdf(ticker: str):

    ticker = ticker.upper()

    path = Path(f"reports/{ticker}/latest_report.pdf")

    if not path.exists():
        raise HTTPException(status_code=404, detail="PDF not found")

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"{ticker}_research_report.pdf"
    )
