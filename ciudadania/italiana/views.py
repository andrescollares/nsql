from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json

# Create your views here.

@csrf_exempt
def Index(request):
  if request.method == 'POST':
    print(request.POST)
    print(request.FILES)
    data = request.POST.dict()

    if data.get("name") == "bolo":
      return HttpResponse("", status=201)
    else:
      return HttpResponse("", status=404)
  else:
    return HttpResponse("<h1>Welcome to TechVidvan Employee Portal</h1>")
