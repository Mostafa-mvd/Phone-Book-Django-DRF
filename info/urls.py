from os import name
from django.urls import path ,include
from django.views.decorators.http import require_POST
from . import views


app_name = "info"


urlpatterns = [
    # path("add/", views.AddPhoneNumber.as_view(), name="add_info"),
    # path("show/", views.ShowPhoneNumbers.as_view(), name="show_info"),
    # path("update/", require_POST(views.EditPhoneNumber.as_view()), name="update"),
    # path('delete/<int:pk>/', require_POST(views.DeletePhoneNumber.as_view()), name='delete_phone_number'),
    # path("search/", views.SearchPhoneNumber.as_view(), name="search"),
    path('download-phone-book/', views.DownloadPhoneBook.as_view(), name='download-phone-book'),

    path('phone-book/add/', views.CreatePhoneNumbers.as_view(), name='add'),
    path('phone-book/list/', views.ListPhoneNumbers.as_view(), name='list'),
    path('phone-book/update/', views.UpdatePhoneNumbers.as_view(), name='update'),
    path('delete/<int:pk>/', views.DeletePhoneNumbers.as_view(), name='delete_phone_number'),
    path("search/", views.SearchPhoneNumbers.as_view(), name="search")
]
