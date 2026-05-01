from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.setup_page, name="setup"),
    path("calendar/", views.calendar_page, name="calendar"),
    path("api/events/", views.emotion_calendar_events, name="emotion_events"),
    path("import/api/", views.import_tweets_from_api, name="import_tweets_from_api"),
    path("import/between/", views.import_between_mar24_may8, name="import_between"),
    path("import/archive/", views.import_archive_view, name="import_tweets_from_js"),
    path("analyze/", views.analyze_tweets, name="analyze_tweets"),
    path("api/analyze-progress/", views.analyze_progress, name="analyze_progress"),
    path("api/tweets/", views.get_tweets_by_label, name="get_tweets_by_label"),
    path("graph/", views.graph_page, name="graph"),
    path("api/graphdata/", views.graph_data, name="graph_data"),
]
