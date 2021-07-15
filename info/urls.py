from os import name
from django.urls import path ,include
from django.views.decorators.http import require_POST
from . import views
from rest_framework.routers import DefaultRouter


# cache_page(120) -> for pages that has no need to login in account


app_name = "info"


router = DefaultRouter()

router.register(prefix=r"", viewset=views.PhoneNumberViewSet, basename="add-form")


urlpatterns = [
    path("show/", views.ShowPhoneNumbers.as_view(), name="show_info"),
    path("add/", views.AddPhoneNumber.as_view(), name="add_info"),
    path("update/", require_POST(views.EditPhoneNumber.as_view()), name="update"),
    path("search/", views.SearchPhoneNumber.as_view(), name="search"),
    path('download-phone-book/', views.DownloadPhoneBook.as_view(), name='download-phone-book'),
    path('delete/<int:pk>/', require_POST(views.DeletePhoneNumber.as_view()), name='delete_phone_number'),

    path("add-phone/", include(router.urls), name='add_phone'),
]
