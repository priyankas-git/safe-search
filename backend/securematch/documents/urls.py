from django.urls import path
from .views import (
    UploadDocumentView,
    InternalSearchView,
    ExternalSearchView,
    RotateAuditorKeyView,
    VerifyAuditorCredentialsView,
    AuditorLogsView,
    InternalMetricsView,
    ExternalMetricsView,
    CreateAuditorView,
    DeleteAuditorView,
    HealthCheckView,
    DownloadAuditorCredentialsView,
)

urlpatterns = [
    path("health/", HealthCheckView.as_view()),
    path("upload/", UploadDocumentView.as_view()),
    path("search/internal/", InternalSearchView.as_view()),
    path("search/external/", ExternalSearchView.as_view()),
    path("auditor/verify/", VerifyAuditorCredentialsView.as_view()),
    path("auditor/rotate-key/", RotateAuditorKeyView.as_view()),
    path("auditor/<int:auditor_id>/logs/", AuditorLogsView.as_view()),
    path("metrics/internal/", InternalMetricsView.as_view()),
    path("metrics/external/", ExternalMetricsView.as_view()),
    path("auditor/rotate-key/", RotateAuditorKeyView.as_view()),
    path("auditor/create/", CreateAuditorView.as_view()),
    path("auditor/<int:auditor_id>/delete/", DeleteAuditorView.as_view()),
    path("auditor/<int:auditor_id>/download/", DownloadAuditorCredentialsView.as_view()),
]

