from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("home/", views.home, name="home"),
    path("nifty_chain/", views.nifty_chain, name="nifty_chain"),
    path("live_pcr/", views.live_pcr, name="live_pcr"),
    path("oi_change_data_display/", views.oi_change_data_display, name="oi_change_data_display"),
]
