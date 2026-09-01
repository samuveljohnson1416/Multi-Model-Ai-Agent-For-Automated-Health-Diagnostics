"""
GET /api/reports/{report_id} — retrieve a report.
GET /api/reports — list reports for a user.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Query

router = APIRouter(prefix="/api", tags=["Reports"])


@router.get("/reports/{report_id}")
async def get_report(request: Request, report_id: str):
    """Retrieve a previously analyzed report by its ID."""
    repository = request.app.state.repository
    report = await repository.get_report(report_id)

    if not report:
        raise HTTPException(status_code=404, detail=f"Report not found: {report_id}")

    return report


@router.get("/reports")
async def list_reports(
    request: Request,
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
):
    """List reports, optionally filtered by user ID."""
    repository = request.app.state.repository

    if not user_id:
        raise HTTPException(
            status_code=400,
            detail="user_id query parameter is required",
        )

    reports = await repository.get_user_reports(user_id)
    return {"user_id": user_id, "reports": reports, "total": len(reports)}


@router.get("/debug/recent-reports")
async def recent_reports(request: Request):
    """Recent analysis runs (in-memory, this process only) for the internal
    /agent-review page. Returns id, file name, and timestamp — no report data."""
    recent = getattr(request.app.state, "recent_reports", None)
    return {"reports": list(recent) if recent else []}


@router.delete("/reports/{report_id}")
async def delete_report(request: Request, report_id: str):
    """Delete a report and its chat history."""
    repository = request.app.state.repository

    report = await repository.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report not found: {report_id}")

    await repository.delete_report(report_id)
    return {"status": "deleted", "report_id": report_id}
