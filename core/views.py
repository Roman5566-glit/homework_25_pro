from django.shortcuts import render


def chat_room_view(request):
    return render(request, 'core/chat.html')
