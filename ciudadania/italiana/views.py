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
        offspring = get_offspring("d1b44fb3-e415-458d-a8bf-edff17669cf9", "Jonathan Farley")
        text= ""
        for person in offspring:
          if text=="":  
            text = person.name
          else:
            text += ", " + person.name
        return HttpResponse(text)

def add_family_uuid(member, family_uuid):
    member["family_uuid"] = family_uuid
    return member

@csrf_exempt
def create_family(request):
    if request.method == "POST":
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

def get_offspring(family_uuid, name):
  query = (
    'MATCH ((p1:Person{family_uuid:$family_uuid, name:$name}) - [:OFFSPRING*1..] -> (p2:Person{family_uuid:$family_uuid}))'
    'RETURN p2'
  )
  params = {"family_uuid": family_uuid, "name": name}
  results, meta = db.cypher_query(query, params)
  offspring = [Person.inflate(row[0]) for row in results]
  return offspring

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
