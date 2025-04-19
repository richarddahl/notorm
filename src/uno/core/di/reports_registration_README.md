# Reports Module DI Registration

All Reports module services and repositories must be registered with the global DI container using `configure_reports_services(container)` found in `src/uno/core/di/container.py`.

To inject a Reports service in FastAPI endpoints, use the central DI system:

```python
from uno.core.di.di_fastapi import FromDI
from uno.reports.domain_services import ReportTemplateService

@app.get("/some-endpoint")
def some_endpoint(service: ReportTemplateService = Depends(FromDI(ReportTemplateService))):
    ...
```

Ad hoc provider functions such as `get_report_template_service` have been removed. All dependency resolution is now via the DI container.
