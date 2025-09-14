"""
Hooks router for automated tasks and reporting.
Handles daily reports, manual report generation, and other hook-based functionality.
"""

import logging
from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from ..models.analytics import DailyReportRequest, DailyReportResponse
from ..services.daily_report_service import daily_report_service
from ..utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/hooks", tags=["hooks"])


class SendDailyReportRequest(BaseModel):
    """Request model for sending daily reports"""
    date: Optional[str] = Field(None, description="Date in YYYY-MM-DD format, defaults to yesterday")
    domain_filter: Optional[str] = Field(None, description="Filter by specific domain")
    email_recipients: Optional[list[str]] = Field(None, description="Email recipients, defaults to user's email")
    send_email: bool = Field(True, description="Whether to send email or just return HTML")


@router.post("/send_daily_report", response_model=DailyReportResponse)
async def send_daily_report(
    request: SendDailyReportRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate and optionally send daily analytics report.
    
    This endpoint generates a comprehensive daily report including:
    - Total clicks and links for the specified date
    - Top performing links
    - Geographic breakdown of clicks
    - Device and referrer analytics
    - HTML formatted email content
    
    If SendGrid is configured and send_email is True, the report will be emailed.
    Otherwise, the HTML content is returned for manual use.
    """
    try:
        # Parse date or default to yesterday
        if request.date:
            try:
                report_date = datetime.strptime(request.date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Use YYYY-MM-DD"
                )
        else:
            # Default to yesterday
            from datetime import timedelta
            report_date = (datetime.utcnow() - timedelta(days=1)).date()
        
        # Set email recipients
        email_recipients = request.email_recipients or [current_user.get('email')]
        if not email_recipients or not email_recipients[0]:
            raise HTTPException(
                status_code=400,
                detail="No email recipients specified and user email not available"
            )
        
        # Generate the report
        report = await daily_report_service.generate_daily_report(
            report_date=report_date,
            domain_filter=request.domain_filter,
            user_uid=current_user.get('uid')
        )
        
        # Send email if requested and configured
        if request.send_email:
            background_tasks.add_task(
                daily_report_service.send_report_email,
                report=report,
                recipients=email_recipients,
                user_name=current_user.get('name', 'User')
            )
            logger.info(f"Scheduled daily report email for {report_date} to {email_recipients}")
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate daily report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate daily report: {str(e)}"
        )


@router.get("/daily_report_preview")
async def preview_daily_report(
    date: Optional[str] = None,
    domain_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Preview daily report without sending email.
    Returns HTML content for manual review.
    """
    try:
        # Parse date or default to yesterday
        if date:
            try:
                report_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Use YYYY-MM-DD"
                )
        else:
            from datetime import timedelta
            report_date = (datetime.utcnow() - timedelta(days=1)).date()
        
        # Generate the report
        report = await daily_report_service.generate_daily_report(
            report_date=report_date,
            domain_filter=domain_filter,
            user_uid=current_user.get('uid')
        )
        
        return {
            "date": report.date.isoformat(),
            "html_content": report.html_content,
            "summary": {
                "total_clicks": report.total_clicks,
                "total_links": report.total_links,
                "top_links_count": len(report.top_links)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to preview daily report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to preview daily report: {str(e)}"
        )


@router.post("/test_email_config")
async def test_email_config(current_user: dict = Depends(get_current_user)):
    """
    Test SendGrid email configuration.
    Sends a test email to verify the setup.
    """
    try:
        user_email = current_user.get('email')
        if not user_email:
            raise HTTPException(
                status_code=400,
                detail="User email not available for testing"
            )
        
        success = await daily_report_service.test_email_configuration(
            test_recipient=user_email,
            user_name=current_user.get('name', 'User')
        )
        
        if success:
            return {
                "status": "success",
                "message": f"Test email sent successfully to {user_email}"
            }
        else:
            return {
                "status": "error",
                "message": "SendGrid not configured or test email failed"
            }
            
    except Exception as e:
        logger.error(f"Email configuration test failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Email test failed: {str(e)}"
        )