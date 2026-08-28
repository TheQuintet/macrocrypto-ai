"""Export API endpoints for data export in various formats.

This module provides REST API endpoints for exporting data in CSV, PNG,
and PDF formats for predictions, correlations, accuracy, and regimes data.
"""

import logging
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBearer
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_active_user
from app.core.rabbitmq import rabbitmq_client
from app.services.export_service import export_service
from app.models.user import User
from app.models.export_history import ExportHistory, ExportStatus
from app.core.database import get_db

logger = logging.getLogger(settings.SERVICE_NAME)

# ============================================
# ROUTER
# ============================================

router = APIRouter(tags=["Exports"])
security = HTTPBearer()


# ============================================
# PYDANTIC MODELS
# ============================================

class ExportResponse(BaseModel):
    """Export response model."""

    export_id: int
    file_name: str
    file_size: int
    content_type: str
    download_url: Optional[str] = None
    status: str
    created_at: str
    expires_at: Optional[str] = None
    cached: bool = Field(False, description="Whether response was cached")


# ============================================
# ENDPOINTS
# ============================================

@router.get(
    "",
    responses={
        200: {"description": "Successful export"},
        401: {"description": "Unauthorized"},
        429: {"description": "Rate limit exceeded"},
        400: {"description": "Invalid parameters"},
    },
)
async def export_data(
    request: Request,
    export_type: str = Query(
        ...,
        description="Type of data: 'predictions', 'accuracy', 'correlations', 'regimes'",
        pattern="^(predictions|accuracy|correlations|regimes)$"
    ),
    format: str = Query(
        ...,
        description="Export format: 'csv', 'png', 'pdf'",
        pattern="^(csv|png|pdf)$"
    ),
    timeframe: Optional[str] = Query(
        "24h",
        description="Timeframe for predictions and regimes",
        pattern="^(24h|7d|1w|1m)$"
    ),
    symbol: str = Query(
        "BTC",
        description="Trading symbol (default: BTC)"
    ),
    days: Optional[int] = Query(
        30,
        ge=1,
        le=365,
        description="Number of days for accuracy metrics"
    ),
    window: Optional[str] = Query(
        "30d",
        description="Time window for correlations",
        pattern="^(30d|90d|1y)$"
    ),
    model_type: Optional[str] = Query(
        "ensemble",
        description="Model type for predictions",
        pattern="^(ensemble|lstm|transformer)$"
    ),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Export data in the specified format.

    Returns exported data in CSV, PNG, or PDF format.

    Args:
        request: The HTTP request object.
        export_type: Type of data to export.
        format: Export format (csv, png, pdf).
        timeframe: Timeframe for predictions and regimes.
        symbol: Trading symbol.
        days: Days for accuracy metrics.
        window: Window for correlations.
        model_type: Model type for predictions.
        current_user: The authenticated user.
        db: The database session.

    Returns:
        Response: The exported file.

    Raises:
        HTTPException: If export fails or parameters are invalid.
    """
    # Create export history record
    export_record = ExportHistory(
        user_id=current_user.id,
        export_type=export_type,
        format=format,
        status=ExportStatus.PENDING,
    )
    db.add(export_record)
    db.commit()
    db.refresh(export_record)

    try:
        # Update status to processing
        export_record.status = ExportStatus.PROCESSING
        db.commit()

        # Generate export
        export_result = await export_service.generate_export(
            user_id=current_user.id,
            data_type=export_type,
            format_type=format,
            timeframe=timeframe,
            symbol=symbol,
            days=days,
            window=window,
            model_type=model_type,
        )

        # Update export record
        export_record.status = ExportStatus.COMPLETED
        export_record.file_path = export_result["file_path"]
        export_record.file_name = export_result["file_name"]
        export_record.file_size = export_result["file_size"]
        export_record.completed_at = datetime.now(timezone.utc)
        export_record.set_expiry_days(7)  # Files expire after 7 days
        db.commit()

        # Publish ExportCompleted event
        try:
            rabbitmq_client.publish_event(
                event_type="ExportCompleted",
                data={
                    "export_id": export_record.id,
                    "user_id": current_user.id,
                    "export_type": export_type,
                    "format": format,
                    "file_size": export_result["file_size"],
                    "file_name": export_result["file_name"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                routing_key="export.completed"
            )
        except Exception as e:
            logger.warning(f"Failed to publish ExportCompleted event: {e}")

        # Return file
        content_type = export_result["content_type"]
        filename = export_result["file_name"]

        return Response(
            content=export_result["data"],
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Export-ID": str(export_record.id),
            },
        )

    except ValueError as e:
        # Invalid parameters
        export_record.status = ExportStatus.FAILED
        export_record.error_message = str(e)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # General error
        export_record.status = ExportStatus.FAILED
        export_record.error_message = str(e)
        db.commit()
        logger.error(f"Export failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.get("/history")
async def get_export_history(
    request: Request,
    limit: int = Query(50, ge=1, le=100, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get export history for the current user.

    Returns a list of previous export records with status and metadata.

    Args:
        request: The HTTP request object.
        limit: Number of records to return.
        offset: Number of records to skip.
        current_user: The authenticated user.
        db: The database session.

    Returns:
        dict: Export history with pagination.
    """
    query = db.query(ExportHistory).filter(
        ExportHistory.user_id == current_user.id
    )

    total = query.count()

    history = query.order_by(
        ExportHistory.created_at.desc()
    ).offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": h.id,
                "export_type": h.export_type,
                "format": h.format,
                "file_name": h.file_name,
                "file_size": h.file_size,
                "status": h.status,
                "created_at": h.created_at.isoformat() if h.created_at else None,
                "completed_at": h.completed_at.isoformat() if h.completed_at else None,
                "expires_at": h.expires_at.isoformat() if h.expires_at else None,
                "download_count": h.download_count,
                "error_message": h.error_message,
            }
            for h in history
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/{export_id}/download")
async def download_export(
    export_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Download a previously exported file.

    Args:
        export_id: The export record ID.
        current_user: The authenticated user.
        db: The database session.

    Returns:
        Response: The exported file.

    Raises:
        HTTPException: If the export is not found, expired, or not completed.
    """
    # Find export record
    export_record = db.query(ExportHistory).filter(
        ExportHistory.id == export_id,
        ExportHistory.user_id == current_user.id,
    ).first()

    if not export_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found"
        )

    if export_record.status != ExportStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Export not completed (status: {export_record.status})"
        )

    if export_record.is_expired:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Export file has expired"
        )

    # Read file
    try:
        import os
        if not os.path.exists(export_record.file_path):
            raise FileNotFoundError("File not found")

        with open(export_record.file_path, "rb") as f:
            file_data = f.read()

        # Increment download count
        export_record.increment_download_count()
        db.commit()

        # Determine content type
        content_type = {
            "csv": "text/csv",
            "png": "image/png",
            "pdf": "application/pdf",
        }.get(export_record.format, "application/octet-stream")

        return Response(
            content=file_data,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={export_record.file_name}",
            },
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not found"
        )
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}"
        )