# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Dashboard management module for the reports system.

This module provides utilities for creating, configuring, and rendering
interactive dashboards based on report templates.
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from io import BytesIO
from sqlalchemy.ext.asyncio import AsyncSession

from uno.dependencies.fastapi import get_db_session, inject_dependency
from uno.core.errors.result import Result, unwrap_or_raise
from uno.reports.services import ReportTemplateService, ReportExecutionService
from uno.reports.aggregation import ReportDataAggregator


# Pydantic models for request/response
class DashboardFilter(BaseModel):
    field: str
    value: Any
    operator: str = "eq"


class DashboardWidget(BaseModel):
    id: str
    type: str
    title: str
    report_id: str
    data_key: str
    config: Dict[str, Any] = {}
    position: Dict[str, int] = {"x": 0, "y": 0, "w": 3, "h": 3}


class DashboardConfig(BaseModel):
    name: str
    description: Optional[str] = None
    report_ids: List[str]
    widgets: List[DashboardWidget]
    default_date_range: Dict[str, str] = {
        "start": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
        "end": datetime.now().strftime("%Y-%m-%d")
    }
    default_filters: List[DashboardFilter] = []
    refresh_interval: int = 0
    created_by: Optional[str] = None
    is_public: bool = False
    theme: Optional[str] = None


# Create router
router = APIRouter(prefix="/dashboards", tags=["dashboards"])


# Dependency for data aggregator
async def get_data_aggregator(
    session: AsyncSession = Depends(get_db_session),
    execution_service: ReportExecutionService = Depends(inject_dependency(ReportExecutionService))
) -> ReportDataAggregator:
    """Get the data aggregator service."""
    return ReportDataAggregator(session, execution_service)


# Dashboard endpoints
@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    dashboard: DashboardConfig,
    session: AsyncSession = Depends(get_db_session),
    template_service: ReportTemplateService = Depends(inject_dependency(ReportTemplateService))
):
    """Create a new dashboard configuration."""
    # Validate that all report IDs exist
    for report_id in dashboard.report_ids:
        result = await template_service.get_template(report_id)
        if result.is_failure:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report template with ID {report_id} not found"
            )
    
    # Create a database entry for the dashboard configuration
    dashboard_dict = dashboard.dict()
    
    # Add creation timestamp
    dashboard_dict["created_at"] = datetime.now().isoformat()
    dashboard_dict["updated_at"] = dashboard_dict["created_at"]
    
    # Store dashboard in database
    # In a real implementation, this would use a repository
    # For now, we'll simulate with a simple dictionary
    dashboard_id = "d-" + str(hash(json.dumps(dashboard_dict)) % 10000)
    dashboard_dict["id"] = dashboard_id
    
    # In a real implementation: await dashboard_repository.create(dashboard_dict)
    
    return {
        "id": dashboard_id,
        **dashboard_dict
    }


@router.get("/{dashboard_id}", response_model=Dict[str, Any])
async def get_dashboard(
    dashboard_id: str = Path(..., description="The ID of the dashboard to retrieve")
):
    """Get a dashboard configuration by ID."""
    # In a real implementation: await dashboard_repository.get(dashboard_id)
    
    # Simulate database lookup with error handling
    if dashboard_id.startswith("d-"):
        return {
            "id": dashboard_id,
            "name": "Example Dashboard",
            "description": "This is an example dashboard",
            "report_ids": ["r-1001", "r-1002", "r-1003"],
            "widgets": [
                {
                    "id": "w1",
                    "type": "metric",
                    "title": "Total Sales",
                    "report_id": "r-1001",
                    "data_key": "total_sales",
                    "config": {"format": "currency"},
                    "position": {"x": 0, "y": 0, "w": 3, "h": 2}
                },
                {
                    "id": "w2",
                    "type": "chart",
                    "title": "Sales by Region",
                    "report_id": "r-1002",
                    "data_key": "sales_by_region",
                    "config": {"chart_type": "bar"},
                    "position": {"x": 3, "y": 0, "w": 9, "h": 6}
                },
                {
                    "id": "w3",
                    "type": "table",
                    "title": "Top Products",
                    "report_id": "r-1003",
                    "data_key": "top_products",
                    "config": {"page_size": 5},
                    "position": {"x": 0, "y": 2, "w": 3, "h": 4}
                }
            ],
            "default_date_range": {
                "start": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "end": datetime.now().strftime("%Y-%m-%d")
            },
            "default_filters": [],
            "refresh_interval": 300,
            "created_by": "system",
            "is_public": True,
            "theme": "light",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dashboard with ID {dashboard_id} not found"
        )


@router.put("/{dashboard_id}", response_model=Dict[str, Any])
async def update_dashboard(
    dashboard: DashboardConfig,
    dashboard_id: str = Path(..., description="The ID of the dashboard to update"),
    session: AsyncSession = Depends(get_db_session),
    template_service: ReportTemplateService = Depends(inject_dependency(ReportTemplateService))
):
    """Update a dashboard configuration."""
    # Validate that all report IDs exist
    for report_id in dashboard.report_ids:
        result = await template_service.get_template(report_id)
        if result.is_failure:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report template with ID {report_id} not found"
            )
    
    # In a real implementation: validate dashboard exists
    # existing = await dashboard_repository.get(dashboard_id)
    # if not existing:
    #     raise HTTPException(...)
    
    # Update dashboard
    dashboard_dict = dashboard.dict()
    dashboard_dict["id"] = dashboard_id
    dashboard_dict["updated_at"] = datetime.now().isoformat()
    
    # In a real implementation: await dashboard_repository.update(dashboard_id, dashboard_dict)
    
    return {
        "id": dashboard_id,
        **dashboard_dict
    }


@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: str = Path(..., description="The ID of the dashboard to delete")
):
    """Delete a dashboard configuration."""
    # In a real implementation: await dashboard_repository.delete(dashboard_id)
    
    # Simulate success with empty response
    return None


@router.get("/{dashboard_id}/data", response_model=Dict[str, Any])
async def get_dashboard_data(
    dashboard_id: str = Path(..., description="The ID of the dashboard"),
    date_start: Optional[str] = Query(None, description="Start date for report data"),
    date_end: Optional[str] = Query(None, description="End date for report data"),
    filters: Optional[str] = Query(None, description="JSON string of filters"),
    force_refresh: bool = Query(False, description="Force data refresh"),
    data_aggregator: ReportDataAggregator = Depends(get_data_aggregator)
):
    """Get data for all reports in a dashboard."""
    # Get dashboard configuration
    # In a real implementation: dashboard = await dashboard_repository.get(dashboard_id)
    # if not dashboard:
    #     raise HTTPException(...)
    
    # Simulate dashboard lookup
    dashboard = {
        "id": dashboard_id,
        "report_ids": ["r-1001", "r-1002", "r-1003"]
    }
    
    # Parse filters
    filter_dict = {}
    if filters:
        try:
            filter_dict = json.loads(filters)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filter JSON format"
            )
    
    # Prepare date range
    date_range = {
        "start": date_start or (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
        "end": date_end or datetime.now().strftime("%Y-%m-%d")
    }
    
    # Get data from the aggregator
    result = await data_aggregator.get_multi_report_data(
        dashboard["report_ids"],
        date_range,
        filter_dict,
        cache_key=f"dashboard:{dashboard_id}:{date_range['start']}:{date_range['end']}:{json.dumps(filter_dict)}",
        force_refresh=force_refresh
    )
    
    dashboard_data = unwrap_or_raise(result)
    
    return {
        "dashboard_id": dashboard_id,
        "date_range": date_range,
        "filters": filter_dict,
        "data": dashboard_data,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/{dashboard_id}/export", response_class=StreamingResponse)
async def export_dashboard(
    dashboard_id: str = Path(..., description="The ID of the dashboard"),
    format: str = Query(..., description="Export format (pdf or xlsx)"),
    date_start: Optional[str] = Query(None, description="Start date for report data"),
    date_end: Optional[str] = Query(None, description="End date for report data"),
    filters: Optional[str] = Query(None, description="JSON string of filters"),
    data_aggregator: ReportDataAggregator = Depends(get_data_aggregator)
):
    """Export dashboard data in specified format."""
    # Get dashboard configuration and data (similar to get_dashboard_data)
    # In a real implementation, this would use template rendering services
    # to generate the PDF or Excel file with proper formatting
    
    # For now, just return sample data
    if format.lower() == 'pdf':
        # Example PDF generation (in a real implementation, use a PDF library)
        content = b"%PDF-1.5\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n3 0 obj\n<</Type/Page/MediaBox[0 0 612 792]/Resources<<>>/Contents 4 0 R/Parent 2 0 R>>\nendobj\n4 0 obj\n<</Length 68>>\nstream\nBT\n/F1 12 Tf\n50 700 Td\n(This is a sample dashboard export. Dashboard ID: " + dashboard_id.encode() + b") Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000056 00000 n \n0000000111 00000 n \n0000000212 00000 n \ntrailer\n<</Size 5/Root 1 0 R>>\nstartxref\n329\n%%EOF"
        
        return StreamingResponse(
            BytesIO(content),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=dashboard_{dashboard_id}.pdf"}
        )
    elif format.lower() == 'xlsx':
        # Example Excel generation (in a real implementation, use an Excel library)
        content = b"PK\x03\x04\x14\x00\x06\x00\x08\x00\x00\x00!\x00\xb4\x0c\x00\xd5\xe3\x01\x00\x00\xe8\x05\x00\x00\x13\x00\x08\x02[Content_Types].xml \xa2\x04\x01(\xa0\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00PK\x03\x04\x14\x00\x06\x00\x08\x00\x00\x00!\x00\xb4\x0c\x00\xd5\xe3\x01\x00\x00\xe8\x05\x00\x00\x0b\x00\x00\x00_rels/.rels\xad\x93\xcfJ\xc3@\x10\x87\xef\x82\xef0\xe4\xdej\xd3\"\x89bA\xad\x82\x97\x05\x0f\xbe\xc0\x98\xfd\x13\x92\xdd\x84\xccl\xb5}\xfb\xbd{\xb0\xe9\xaaEQ\xf0\x98\xcd\xfc\xe6\x9b\xc3\xec\x9e\xe6\xe3\xd4x1\xa1s\xdaFW\xb0\xde\x94\xa0\xb0\xb1\x03\x1d\xa2+\xe8\xf6\xb7\xb7Ux\x9c\xcd&\xb7\x8c]0\x91\xb0\x13\n+Ozx*CZc\xa3\xdc\xca\x84.C\x05\xed\xb4\xa8w@\x9c\xcc\xd8\xd1\xc4\xd84\x91\x1a[\xd3F\xd9\xc3\xa8\xe5\xf6\xe3\xc6X\xdf\xfb\xc0\x1a{\x9d\xa0\xf4\xde$n\xd0^D\x1c\xa2%x\x17\x04y\xc5\x0f\x83\x16<\x11\xe6\\U\x05\xd7\xe6\x90\xf6\x83\x90\n\xd9\xccI\xbdfj\xd3\xba>S\xd5\xf7*X\xd1\xaf\x8fX\x00\xe4>\xb8\x165\x9c\xc3\t\xa2\x91MX\x0f\xb2\xcc\xef\xd8\xe1@MK\t\x14\x02Q\x04\x19\xc4\xa9\xc7\x89Gr\x02~\xac$\xfc\x88\x9d|\xf4\x02\xbeR [\xfe3\nX\xe2\x97\xf1\xf6\xee\x1d\xcc\xa6/\x90\x86\x81<Mb\xbbL\xed\x87\xf8\x1a\nt`\x81\xe4\x98\x9b9\x8c\r\xf5\xfd\r\xdb\x13\xfd1\xda\xcf\x91\xa6\n\x91\xf6\xa7\x1a\xb3\x1b\xef\xab\x87\xbf\x00PK\x03\x04\x14\x00\x06\x00\x08\x00\x00\x00!\x00\xb4\x0c\x00\xd5\xe3\x01\x00\x00\xe8\x05\x00\x00\x10\x00\x00\x00docProps/app.xml\xa4\x90\xc1J\x031\x10\x86\xef\n}\x87!\xb7\xedFC\xa9\xb4M\x0f\n\x82`{\x94\xecd\x9b\xb2\x9b\x84$Zw\xdf\xde\xb8\xfa\x00\x1ee\xe6\xe7\xfb'\x99\xaa?\x8c=\xbcQN\xc6\x87\xa6Xf\x05\x80\xe0\xbc\xed\xc3\xae!?\x9em\x8a\n(\xaa\xe0\xac\xeeCDC\x8e\x98\xeame!\xd9\n\x12Z\xb0\x93\x89\xd2Ai_\x9c[\x0e\xdaL\r\x892;\xb0\x17\x81\xd2\x97X\xe5\xb0\x07\xd5\x99\x0eX\xcb\xf3\xabJ\x15\x87{\xd0\xf1\xfbe\xd9\x98\xf7\xc8\xe1\x1a\xba\x01\xc3\xf8\x80\x94\x17\xcd\x19\xacaN\xcb\xbc\xa7\xb5\x9aua\x9e\xdaH:\x12\x7f\xe7\x916\xaf\x90\x07\x90#\x1a:5`\xbd\xd4\x89\xfa\xe7\x19\xec\x99#T\xf7Z\x1e\x18\xfdf\t\xdcp\x8c\x8dG\xb9\xd1\x8c\xd0\xfc6\x97\xc5^2\xcc\x05\xa6\xbb\xdf\x92\x94\xe6g\xe59\x1f\xee\x85M?\x0e!\xdf\x06\xea\x97\xd1\x9d\xb6\xe7\xfcwB\r\xed;\xea\xca\xe7\x04\xef\xf0O\xd5\x08{\x18\x07\xde\x92\xe3\xf6\x0b\xf8\x04PK\x03\x04\x14\x00\x06\x00\x08\x00\x00\x00!\x00\xb4\x0c\x00\xd5\xe3\x01\x00\x00\xe8\x05\x00\x00\x11\x00\x00\x00docProps/core.xml\x8d\x92\xc1n\x830\x10D\xef\x95\xfa\x0f\x96o \xb4\xadT\xd5\x08\xb8I\x94K\xd3\x03\xaa\xaa^M\xb3`\xc5\xd8\xc8\xbb\xa0\xf6\xdfwI\xa8\xd2K\xdbCm\xc9\xf6\xbc\xf1\xcc\xae\xad\xf7\xb3\x18M\xb1\xb3J\xcb\x00\x9d\x9f\x1c\"$\x990\xbd\xec\x82\xf8\xfez\x8cW\x88I\na\nI\x9aH\x01\xa9\xaa\xb21f\xb4\xf8\x19\xfbV$0(3\xa3\x00\x83\xc2\xa2.\x07X\xee\xa6d$\xc5\xb7\xe6\x0e\xcd\x8cs\xae\xb9\x16N[\xd1\x19c\x9cO\xef\xbb\xb6\xfb\xd0\x03\x18\xd7\xccrE\n\xa6\x82\xe8(\xcb-?\xcbl\xde\xf60F\xdc\xfd=W\x9b\xcfM\xf7\xd0\x0fgf\xb01\xf0\xa0B\x98\x0eF\xb8\xdcp\xf2\xeb\xc3\x91\x86{\xb7}\xf8\xd8\x9c\x8e\x17\xe7\xb3Oq\xbd\xa3\xc0\x17\xc5x\xae\xf5\x9dt\xbd\x19\x90\xf5\xaa\xb0-\xda\x07S\x01\x17<U\x84(\x0e{\x98\x00b| n!\xd1@\x1eX\xa2rn\xb6X\xbe`\xe0\x9d\xe5\xb6\x92>\xc0M\xb8I?\xd9>u\xb3\x05;\x0b\x16\xfc\xcaI\x89\xdc\x8db\xe1\xd21\x19\xfc\xffJxAg\xb0\xe9h\xf7JA\xa7_$\x84\xcf\xf3\xf3\xa3u\xea\x82\xdd\xa7c\x1c\xbe\xb6\r\x9f\x01\x00\x00\xff\xffPK\x03\x04\x14\x00\x06\x00\x08\x00\x00\x00!\x00\xb4\x0c\x00\xd5\xe3\x01\x00\x00\xe8\x05\x00\x00\x13\x00\x00\x00xl/workbook.xml\x8c\x91\xcfj\xc30\x10\xc4\xef\x81\xbc\x83\xd0\xbd\x89\x93\x12JT;\x87\x96\xe6\x94\xd2\x9e{\xb1VIX{W\xacc\xda\xb7\xafbC\x08\xf4\xb0\xb7\xe1\xfb\xcd\xecH;\xdd\x9e\x9a&ZQP\xeda\x12\xf7c\x14\x91\xaf\xc1\xd6\xbet\xf1\xe3\xfc\x16\xcfe\x14\x9c\xf1\xb6\xf5\r\xf8\x88\x04\xdb\xc9m\x16\x87a8\x88n\xc3!>\xac\x16o\xc7\xf5r;H\xad.\x1d\xd7\xfe\xa2[\xa0\x1a\xbd\xff\xd8\x9c\x9c\nj\x01\xb5H\xe8\xf5\xbd\x96\xf8\xea\xfa\xd9\x1eM$\xf2\xd2\xc6\t\x1f>\x1f\xe2#\xdf4\x1a\x94e\xb9[\x8a\xa8\xfa\xca\xfaFZ\xbf\x1eP\xaa\xf5\xab\xd0\x97\x92\x84L\xfbi\x9a\xee\x9a\xf89\xbd\xdf\xb1\xf4\x81S\n\xba\x1a%\xfck\xba\xbe\xf3m\xde\xd2\x0e]9\xa9$\xcf\x18\xc2\x8a\xee\xf94\xcd\xdf\xe3K\x86\xe4\x98\x0e\x8c\x12\xb2K\x04\xfd\xc8\x8a\xd0\x0eo\xfc\xdf\xd6\xce\xa2\x8b\x10\xf0\xc4\xfd\xa2Y\xc1\xdf'R\xf3\x80\xc2\xb1\x00\xfea%\x9e\x1c\x0beV\x9a\x11\x0f\xd5\xe1vPc\xfe\xa90\xbe\x01\x00\x00\xff\xffPK\x03\x04\x14\x00\x06\x00\x08\x00\x00\x00!\x00\xb4\x0c\x00\xd5\xe3\x01\x00\x00\xe8\x05\x00\x00\x1a\x00\x00\x00xl/_rels/workbook.xml.rels\xac\x94]o\xdb0\x10\xc7\xef\x03\xf6\x1d\x08}\x16\x1c\xaf\xdb\xb2\x84\x14\xc3\x96\xa0E\x07lmQ\xa0\xcf\x89\xc5\xa4\x05\x93\xd2@R\x8e\xfd\xed;\xca~\xf8!M\x8b\x06\xc3\x1e\xc4\xe3\xfd\xffGw:%\xfd~\xd3*\xb2FgL\x90pIy8\xe0\x04\x03\xcd\x9a\x80\xf3@\xbe\xde]^\\ORJ\x16\xa8\x16\xa8\x82\x80\x87f\xa0\xef\x93Y\x04\xa1\x07\xda\x02+\xda\x91\x03\xe3*\x1aC\xb0\xeb\xbe\xabc\ra\xad\x01GN\xc7p\x85\x9e\xa0m\xba\xedH\xa0\xa5N\x94\x8a\x1c\xabU\xac\x0b\x0c!>\xab\xe8\xa3X\xc1\x13\xd8YS\xde\xab4\xcax\xb6\"\xef\xec\xe9\xce\xeb\x06\xb7\xd8\xd4\xc4\x9b^v\xb8e\xddb\xabfp\x0e(\x0fQ\x96\xc6\xdaq\x064\xf6\x18\x84\xa1\xd7\xb5\xda\x14sGR\xc7\xaf\x1a.\xc2$\x84\xbb\x16\xeb\xa6`?]\x11I<\xce/\xc7\xfa\xadL\xd2\xf7\xfa\x8bL\x93\x8e\xf2\xf8\xa1\xd2\xeb\xdb\x9e\x07\x83\xd9\xe4Bn@`\x80b\xe1(\xcf\x96\xeb\xb8y\xe6\xb1\x1c\xe5\xa3\x18\xe2\x1c\xe5#G\xb9\xe3UU\xa1\xb3x\x94\xc7yB\x9e\n\xf2\xf4\xf5\xb2\xae%ZFI\x94OI\x1c\xbd\xa0m\xe6\x9e\x1e\xe5\x01\\\xa0\x15\x1a\xa2!Y\xa5\xe0RK\xef\xc0\xc8\xf28\x9f\x9d\x9f\xb1I\xe2\xe0\xec\x9c\x15JIg\x94\xd3\xcc\x10\xd3\xc6+\nS\xf7\xe0\xacx\xa6\x19w\xf1D|y\x82s'\xc5\xe6\xfaf\xf9\xed\xfad\xff\xf7\xb8\x83\xb7Y\xfdd\x9a\xe1\xefS/\xca\xa7\x9b\xff\x81\xab\xa6\x80\xdaO\xdet\x84;~\xf6\xdd\x96\xfd\x04\x00\x00\xff\xffPK\x03\x04\x14\x00\x06\x00\x08\x00\x00\x00!\x00\xb4\x0c\x00\xd5\xe3\x01\x00\x00\xe8\x05\x00\x00\x0f\x00\x00\x00xl/styles.xml\xac\x95]o\xdb0\x10\xc7\xef\x03\xf6\x1d\x0c\xbd\xe7\x99\xf2\xd2\x14\x82]\xa0\xc5\x80\xed\xa5\xc0\x9e\x03Y\xa2b\xcc\xf2\x01\x89N\x9c}z\x8e\xb2\x93.\xc9\xd2\xa5Y\xfbP\x89\x14\x8f\xf7\xfb\xe9\xe8\x1c\xb1\xbd\xde\xf5\x8a\xdc\xc3h\xa4\xd6\x8c&\xd3\xd9\x94\x100\x95\xee\xa4\xae2\xfa\xe5\xfd\xc9\xe2\x8ai\"\x8c\xeeD\xafM\x87j\xe3\xec\x86L\x88\x96;\x84\xbd\xc4\xf8\x99\xd5\xf8\xc0\xa7\x85\xdc\n;W\x1b7\xb5F\xed\xf0\xc3\xd2(\xb2\xb1\xb5\xa9\x91\xfblJ\xd2\xf4*\xfb(\xe5\x07y\x0fr\xdbe\x84\x9f\x9eK\xb9\x92\x0f\xf8s\xddG\xe0\x10\x93\x8a\x9dx\xec\xc4\x08\x9d\xbc+\xc83\x10\x1a\x1e\x83\x89\xa9\x18\xc0\xfe\x8e|\xd1\xd7\xf7\xbbS)w}\xa5\xbb\x8c\xac\xc50\xec\xb4\x19\xbb\x1fs\xcf\xc9\x18\xa56fww\xce\xccc2\x16\x8a\xfcq\xf2\xc5\xbc\x89\x01r\x8fns\x0c\x02\x8c\xb9\x99\x13\x1b!B\xa1@\x8a\x94\xd1\xb7t\xba\xac=\xda\x8b\xbe\x13]K\xff~\x99\x17\xc1\xd4\x9f\xe0_\x84\x1a\x82B\xe5\x07j\x82\x84(\x9a(\x1cp5@\xf9\xc7U\xf6\xa3:W/dX;\xb0\x0b\x03\xf9X\t\xfc\xe3I\x84\x93\xf7\xdbo\x7f\x91$\xdb.\x11\xe6\x1dZv\x84\x11\x06\xfb\x81\xd0\x18x\x8c&\xbcL\x1d\x03/\x91>\x91\xf4q\x1eoW\x87&\n@\xde\x10W\x91\xcd\x01\xb2\xff\x91Y\xfcCf\xc4mS\xf7\xaaAjQ\xefj\xe4\x1c\xe4\xcc\xf3\xdd\xc2.\xe8\x9e\xd9\xc8\xa7\x11\xf6\xaf\xecl\xf9\x1a\xde\xff>0\t\x89?ov\x03\xef\xc2\xf6P.\xf1\xdaD}\x05\xcf\xcf\xfd\xb1n\x0e\xf5\x1em\xee\xac\xa3\x01\n\x0c\xd7h\x1e\xa0\xbbC\xfc\xfc\t\x00\x00\xff\xffPK\x03\x04\x14\x00\x06\x00\x08\x00\x00\x00!\x00\xb4\x0c\x00\xd5\xe3\x01\x00\x00\xe8\x05\x00\x00\x18\x00\x00\x00xl/worksheets/sheet1.xml\xac\x95]o\xdb0\x10\xc7\xef\x03\xf6\x1d\x0c\xbd\x17\x96\x9c\xac\x06\x82\xdc\xa0\xf5\x06d\x0f\x03\xd6>\x00c\xd1\x11\x16\xbf\x820\xca\xd8\xd3\x8b\xd5\xaeX\x9a\xba\xab\xba\x0f\r3\xc9\xe3\xfd\xff\xee\x0e\xd9\xdb\xc3n\xa8\xbd'\xe3\x94V\x95\xf7.\xccc\x8f(\xa2\xdbNUW\xde_\xef\xcf\x16\xb7^\x05\x11\xaa\x1b\x0ej\xa3*\xcf\xe6\xde\xe1\xee\xd5*\xa9\xb7\xc8N\xf9\xc0:\xe5_\x94\xac\x94\xf7\x8c\xb1\x91*\xef`#\xad\\\x7f\x1fvJU\x93\x12\x95\xc3\xb3\xf5\x9e\xf7\xa1\x04\xac@\xebC\xb9\x8c\xe3\xf2\xca{\xbaB\x0eY\xb6\xc9c\x7f\x91\x87r\x9d\x9c\xfc\x9dB(\x82%PdP\x00\x16\xd9\x12\x0b\x86\x05c\x04\x02\x0e\x18\xc0\xc0\xc3\x10\xb2 \x11\x9ey\xf1\xd9\xd7\x93\xe3\xd5\xb2:S\xfb\xae\xe9\x87\xdak\x0c-\xab\xc1h\xe7\xdf\xcb*\xf2\xbc\x0e\xd4\xd0\xbe\xdd\xdaxD\xdeP\xf5\xbf\xf2\xce\xdc\x8d\x1c\x90\xb6\xa1\xfdA\xe3\x84\xdc\xd50\xac<\xd7\xa1\t\x04\xd3\xc6\xa5\x97\x84\x19\xc6 \xf3\xb3\x98\x05Y\xeew\xf6#\xeb\x17\xf2Z\xd8\xeeM\xecl\xfd\xb7\x85\xe3\xfe\xb9[f\xb9\rB\x8e\x9e\xdb!\xc9\xdf\xad\xf8K\xbaR\x9dPwv\x90\xb3\x93s<0\x0fe\xe3|I;\x91\x1a\xbdU\xfdp^>9\xa6\xb9\xb8\xfa^m\xc4\x03e'\x85o\x8dp\x06\xf2\x1e\xbfO\xa5\xb0\xb7\xa1\xe9{\xf2\x9bn\xc6\x03k\x8f\x94\x91J\xb6\xf5\xb3\x1d\xb7(W\xb9\x13\xd7Q\xe1p\xa5\xa7F~\xed!\n\xd4\x94\x9d\x94\xac\x06\xa3\x7f\xd2\x91\xc2\x8a\xbf\x05\x00\x00\xff\xffPK\x01\x02-\x00\x14\x00\x06\x00\x08\x00\x00\x00!\x00\xb4\x0c\x00\xd5\xe3\x01\x00\x00\xe8\x05\x00\x00\x13\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00[Content_Types].xmlPK\x01\x02-\x00\x14\x00\x06\x00\x08\x00\x00\x00!\x00\xb4\x0c\x00\xd5\xe3\x01\x00\x00\xe8\x05\x00\x00\x0b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00=\x02\x00\x00_rels/.relsPK\x01\x02-\x00\x14\x00\x06\x00\x08\x00\x00\x00!\x00\xb4\x0c\x00\xd5\xe3\x01\x00\x00\xe8\x05\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1c\x04\x00\x00docProps/app.xmlPK\x01\x02-\x00\x14\x00\x06\x00\x08\x00\x00\x00!\x00\xb4\x0c\x00\xd5\xe3\x01\x00\x00\xe8\x05\x00\x00\x11\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xfb\x05\x00\x00docProps/core.xmlPK\x01\x02-\x00\x14\x00\x06\x00\x08\x00\x00\x00!\x00\xb4\x0c\x00\xd5\xe3\x01\x00\x00\xe8\x05\x00\x00\x13\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xe2\x07\x00\x00xl/workbook.xmlPK\x01\x02-\x00\x14\x00\x06\x00\x08\x00\x00\x00!\x00\xb4\x0c\x00\xd5\xe3\x01\x00\x00\xe8\x05\x00\x00\x1a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xcc\t\x00\x00xl/_rels/workbook.xml.relsPK\x01\x02-\x00\x14\x00\x06\x00\x08\x00\x00\x00!\x00\xb4\x0c\x00\xd5\xe3\x01\x00\x00\xe8\x05\x00\x00\x0f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xe8\x0c\x00\x00xl/styles.xmlPK\x01\x02-\x00\x14\x00\x06\x00\x08\x00\x00\x00!\x00\xb4\x0c\x00\xd5\xe3\x01\x00\x00\xe8\x05\x00\x00\x18\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xee\x0f\x00\x00xl/worksheets/sheet1.xmlPK\x05\x06\x00\x00\x00\x00\x08\x00\x08\x00\xd1\x01\x00\x00\x00\x13\x00\x00\x00\x00\x00"
        
        return StreamingResponse(
            BytesIO(content),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=dashboard_{dashboard_id}.xlsx"}
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format: {format}"
        )


def register_endpoints(app):
    """Register dashboard endpoints with the FastAPI app."""
    app.include_router(router)