import json
import uuid

from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

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
        json_data = json.loads(request.body)
        family_number = uuid.uuid4()
        person_id = {}
        for person in json_data["members"]:
            instance = Person(
                name=person["name"],
                family=family_number,
                sex=person["sex"],
                has_citizenship=person["has_citizenship"],
            )

            birthday = person["birthday"]
            if birthday:
                instance.birthday = birthday

            citizenship_resignation_date = person["citizenship_resignation_date"]
            if citizenship_resignation_date:
                instance.citizenship_resignation_date = citizenship_resignation_date

            instance.save()

            person_id[person["id"]] = instance

        for relation_partner in json_data["relations_partners"]:
            person_id[relation_partner["first"]].partner.connect(person_id[relation_partner["second"]], {"is_married": relation_partner["married"]})

        for relation_offspring in json_data["relations_offsprings"]:
            person_id[relation_offspring["first"]].offspring.connect(person_id[relation_offspring["second"]])
