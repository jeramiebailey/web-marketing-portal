from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from docker_drf_backend.users.models import User

def index(request):
    user = request.user
    template = 'pages/home.html'
    context = {
        'user': user
    }
    return render(request, template, context)