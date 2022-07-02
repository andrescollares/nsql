import json
import uuid

from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from neomodel import db
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
        offspring = get_offspring("d1b44fb3-e415-458d-a8bf-edff17669cf9", "Jonathan Farley")
        text= ""
        for person in offspring:
          if text=="":  
            text = person.name
          else:
            text += ", " + person.name
        return HttpResponse(text)


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

def get_offspring(family_uuid, name):
  query = (
    'MATCH ((p1:Person{family_uuid:$family_uuid, name:$name}) - [:OFFSPRING*1..] -> (p2:Person{family_uuid:$family_uuid}))'
    'RETURN p2'
  )
  params = {"family_uuid": family_uuid, "name": name}
  results, meta = db.cypher_query(query, params)
  offspring = [Person.inflate(row[0]) for row in results]
  return offspring