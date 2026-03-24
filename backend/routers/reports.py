from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.models.blood_report import BloodReport
from backend.ml.report_parser import BloodReportParser
from backend.security.auth import get_current_user

router = APIRouter(prefix="/api/reports", tags=["reports"])
_parser = BloodReportParser()


@router.post("/upload", status_code=201)
async def upload_report(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    allowed = {".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
    ext = "." + file.filename.split(".")[-1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {allowed}")

    contents = await file.read()
    parsed = _parser.parse_file(contents, file.filename)

    if "error" in parsed:
        raise HTTPException(status_code=422, detail=parsed["error"])

    # Mark previous reports as not latest
    db.query(BloodReport).filter(
        BloodReport.user_id == current_user.id,
        BloodReport.is_latest == True,
    ).update({"is_latest": False})

    report = BloodReport(
        user_id=current_user.id,
        raw_text=parsed.pop("raw_text", None),
        **{k: v for k, v in parsed.items() if hasattr(BloodReport, k)},
        is_latest=True,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return {
        "id": report.id,
        "parsed_values": parsed,
        "message": f"Report parsed successfully. {len(parsed)} biomarkers extracted.",
    }


@router.get("/latest")
def get_latest_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = (
        db.query(BloodReport)
        .filter(BloodReport.user_id == current_user.id, BloodReport.is_latest == True)
        .first()
    )
    if not report:
        return {"message": "No blood report uploaded yet", "report": None}

    return {
        "id": report.id,
        "uploaded_at": report.uploaded_at.isoformat(),
        "hemoglobin": report.hemoglobin,
        "platelets": report.platelets,
        "wbc": report.wbc,
        "total_cholesterol": report.total_cholesterol,
        "ldl": report.ldl,
        "hdl": report.hdl,
        "triglycerides": report.triglycerides,
        "creatinine": report.creatinine,
        "hba1c": report.hba1c,
        "tsh": report.tsh,
        "vitamin_d": report.vitamin_d,
        "vitamin_b12": report.vitamin_b12,
    }
