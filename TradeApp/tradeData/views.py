from django.shortcuts import render, HttpResponse
from .models import TodoItem
# Create your views here.
def home(request):
    return render(request, "base.html")

def contact(request):
    items = TodoItem.objects.all()
    return render(request, "contact.html", {"items":items})
