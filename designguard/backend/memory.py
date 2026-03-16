import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

DATABASE_URL = os.environ.get("DATABASE_URL", "")
engine = create_engine(DATABASE_URL, poolclass=NullPool)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class ScanRecord(Base):
    __tablename__ = "designguard_scans_v2"

    scan_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    url = Column(String, nullable=False, index=True)
    quality_score = Column(Integer, nullable=False, default=0)
    figma_match_score = Column(Integer, nullable=False, default=100)
    all_bugs = Column(JSON, nullable=False, default=list)
    functional_bugs = Column(JSON, nullable=False, default=list)
    dom_a11y_bugs = Column(JSON, nullable=False, default=list)
    security_bugs = Column(JSON, nullable=False, default=list)
    network_issues = Column(JSON, nullable=False, default=list)
    figma_deviations = Column(JSON, nullable=False, default=list)
    fixes = Column(JSON, nullable=False, default=list)
    new_bugs = Column(JSON, nullable=False, default=list)
    pages_visited = Column(JSON, nullable=False, default=list)
    performance_metrics = Column(JSON, nullable=False, default=dict)
    screenshots_meta = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def save_scan(data: Dict[str, Any]) -> None:
    db = SessionLocal()
    try:
        record = ScanRecord(
            scan_id=data["scan_id"],
            user_id=data["user_id"],
            url=data["url"],
            quality_score=data.get("quality_score", 0),
            figma_match_score=data.get("figma_match_score", 100),
            all_bugs=data.get("all_bugs", []),
            functional_bugs=data.get("functional_bugs", []),
            dom_a11y_bugs=data.get("dom_a11y_bugs", []),
            security_bugs=data.get("security_bugs", []),
            network_issues=data.get("network_issues", []),
            figma_deviations=data.get("figma_deviations", []),
            fixes=data.get("fixes", []),
            new_bugs=data.get("new_bugs", []),
            pages_visited=data.get("pages_visited", []),
            performance_metrics=data.get("performance_metrics", {}),
            screenshots_meta=data.get("screenshots_meta", []),
            created_at=datetime.utcnow(),
        )
        db.add(record)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"DB save error: {e}")
    finally:
        db.close()


def get_previous_scan(user_id: str, url: str) -> Optional[Dict[str, Any]]:
    db = SessionLocal()
    try:
        record = (
            db.query(ScanRecord)
            .filter(ScanRecord.user_id == user_id, ScanRecord.url == url)
            .order_by(ScanRecord.created_at.desc())
            .first()
        )
        if not record:
            return None
        return {
            "scan_id": record.scan_id,
            "all_bugs": record.all_bugs or [],
        }
    finally:
        db.close()


def get_user_history(user_id: str) -> List[Dict[str, Any]]:
    db = SessionLocal()
    try:
        records = (
            db.query(ScanRecord)
            .filter(ScanRecord.user_id == user_id)
            .order_by(ScanRecord.created_at.desc())
            .limit(20)
            .all()
        )
        return [
            {
                "scan_id": r.scan_id,
                "url": r.url,
                "created_at": r.created_at.isoformat(),
                "quality_score": r.quality_score,
                "figma_match_score": r.figma_match_score,
                "total_bugs": len(r.all_bugs or []),
                "critical_count": sum(1 for b in (r.all_bugs or []) if b.get("severity") == "critical"),
                "serious_count": sum(1 for b in (r.all_bugs or []) if b.get("severity") == "serious"),
                "moderate_count": sum(1 for b in (r.all_bugs or []) if b.get("severity") == "moderate"),
                "new_bugs_count": len(r.new_bugs or []),
                "pages_scanned": len(r.pages_visited or []),
                "network_issues": len(r.network_issues or []),
                "performance_metrics": r.performance_metrics or {},
            }
            for r in records
        ]
    finally:
        db.close()


def get_scan(scan_id: str) -> Optional[Dict[str, Any]]:
    db = SessionLocal()
    try:
        record = db.query(ScanRecord).filter(ScanRecord.scan_id == scan_id).first()
        if not record:
            return None
        return {
            "scan_id": record.scan_id,
            "user_id": record.user_id,
            "url": record.url,
            "quality_score": record.quality_score,
            "figma_match_score": record.figma_match_score,
            "all_bugs": record.all_bugs or [],
            "functional_bugs": record.functional_bugs or [],
            "dom_a11y_bugs": record.dom_a11y_bugs or [],
            "security_bugs": record.security_bugs or [],
            "network_issues": record.network_issues or [],
            "figma_deviations": record.figma_deviations or [],
            "fixes": record.fixes or [],
            "new_bugs": record.new_bugs or [],
            "pages_visited": record.pages_visited or [],
            "performance_metrics": record.performance_metrics or {},
            "screenshots_meta": record.screenshots_meta or [],
            "created_at": record.created_at.isoformat(),
        }
    finally:
        db.close()
