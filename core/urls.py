from django.urls import path
from . import views


urlpatterns = [
    path("chat/", views.chat_room_view, name="chat_room"),
]
