import json
import uuid

from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime

from neomodel.match import Traversal, OUTGOING, db

from .models import Person, PartnerRel

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

def add_family_uuid(member, family_uuid):
    member["family_uuid"] = family_uuid
    return member

@csrf_exempt
def create_family(request):
    if request.method == "POST":
<<<<<<< HEAD
        json_data = json.loads(request.body)
        family_uuid = uuid.uuid4()
        persons = [add_family_uuid(member, family_uuid) for member in json_data["members"]]
        
        with db.transaction:
            people = Person.create(*persons)

        for relation_partner in json_data["relations_partners"]:
            people[relation_partner["first"]].partner.connect(people[relation_partner["second"]], {"is_married": relation_partner["married"]})

        for relation_offspring in json_data["relations_offspring"]:
            people[relation_offspring["first"]].offspring.connect(people[relation_offspring["second"]])
    # TODO redirect to the algorithm run
        return HttpResponse("", status=201)


@csrf_exempt
def process_family(request, family_uuid):
    if request.method == "GET":
        family = Person.nodes.filter(family_uuid=family_uuid)
        # Dado que la ciudadanía se hereda desde familiares italianos
        # filtraremos por los mismos y haremos recorridas transversales
        italian_relatives = family.filter(has_citizenship=True)
        for italian_relative in italian_relatives:
            pass
            # Hacer query que consiga a todos los descendientes de un italiano
