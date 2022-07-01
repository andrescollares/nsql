import json
import uuid

from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime

from .models import Person

# Create your views here.


@csrf_exempt
def index(request):
    if request.method == "POST":
        print(request.POST)
        print(request.FILES)
        data = request.POST.dict()

        if data.get("name") == "bolo":
            return HttpResponse("", status=201)
        else:
            return HttpResponse("", status=404)
    else:
        return HttpResponse("<h1>Welcome to TechVidvan Employee Portal</h1>")


@csrf_exempt
def create_family(request):
    if request.method == "POST":
        data = request.POST.dict()
        members = json.loads(data["members"])
        relations_partners = json.loads(data["relations_partners"])
        relations_offsprings = json.loads(data["relations_offsprings"])
        family_number = uuid.uuid4()
        person_id = {}
        for person in members:
            instance = Person(
                name=person["name"],
                family=family_number,
                sex=person["sex"],
                has_citizenship=person["has_citizenship"],
            )

            birthday = person["birthday"]
            if birthday:
                instance.birthday = datetime.strptime(birthday, '%Y-%m-%d')

            citizenship_resignation_date = person.get("citizenship_resignation_date")
            if citizenship_resignation_date:
                instance.citizenship_resignation_date = datetime.strptime(citizenship_resignation_date, '%y-%m-%d')

            instance.save()

            person_id[person["id"]] = instance

        for relation_partner in relations_partners:
            person_id[relation_partner["first"]].partner.connect(person_id[relation_partner["second"]], {"is_married": relation_partner["married"]})

        for relation_offspring in relations_offsprings:
            person_id[relation_offspring["first"]].offspring.connect(person_id[relation_offspring["second"]])
        return HttpResponse("", status=201)
