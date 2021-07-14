from django.urls import path
from . import views

app_name = "home"

urlpatterns = [
    path("", views.ShowHome.as_view(), name="home"),
    path("activities/", views.ShowActivities.as_view(), name="activities"),
]
