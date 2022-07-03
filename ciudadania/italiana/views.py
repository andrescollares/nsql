import json
import uuid

from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, date

from neomodel import Q
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
        query = ('MATCH(p:Person) Return DISTINCT p.family_uuid')
        results, meta = db.cypher_query(query)
        family_uuids = [row[0] for row in results]
        text = None
        for item in family_uuids:
          if not text:  
            text = f"\"{item}\""
          else:
            text += ", " + f"\"{item}\""
        text = f"[{text}]"
        return HttpResponse(text)


def add_family_uuid(member, family_uuid):
    member["family_uuid"] = family_uuid
    member["birthday"] = datetime.strptime(member["birthday"], "%Y-%m-%d")
    if member.get("citizenship_resignation_date"):
        member["citizenship_resignation_date"] = datetime.strptime(member["citizenship_resignation_date"], "%y-%m-%d")
    return member


@csrf_exempt
def create_family(request):
    if request.method == "POST":
        data = request.POST.dict()
        members = json.loads(data["members"])
        relations_partners = json.loads(data["relations_partners"])
        relations_offsprings = json.loads(data["relations_offsprings"])
        family_uuid = uuid.uuid4()
        persons = [add_family_uuid(member, family_uuid) for member in members]

        with db.transaction:
            people = Person.create(*persons)

        for relation_partner in relations_partners:
            people[relation_partner["first"]].partner.connect(people[relation_partner["second"]], {"is_married": relation_partner["married"]})

        for relation_offspring in relations_offsprings:
            people[relation_offspring["first"]].offspring.connect(people[relation_offspring["second"]])
        # TODO redirect to the other view
        return HttpResponse("", status=201)


def get_offspring(family_uuid, name):
    query = "MATCH ((p1:Person{family_uuid:$family_uuid, name:$name}) - [:OFFSPRING*1..] -> (p2:Person{family_uuid:$family_uuid})) RETURN p2"
    params = {"family_uuid": family_uuid, "name": name}
    results, meta = db.cypher_query(query, params)
    offspring = [Person.inflate(row[0]) for row in results]
    return offspring


def possible_citizenship(person, could_get_citizenship):
    if(person.has_citizenship or could_get_citizenship.get(person.id) or person.citizenship_resignation_date):
        #corresponde la ciudadanía hacía los hijos ?
        if person.date_of_death and person.date_of_death < date(1861,1,1):
            return could_get_citizenship
        if person.sex == "FEMALE" and person.date_of_death and person.date_of_death < date(1948,1,1):
            return could_get_citizenship
        offspring = person.offspring.all()
        for member in offspring:
            if person.citizenship_resignation_date == None or (person.citizenship_resignation_date and member.birthday < person.citizenship_resignation_date):    
                if not could_get_citizenship.get(member.id):
                    could_get_citizenship[member.id] = member
                could_get_citizenship = possible_citizenship(member, could_get_citizenship)
    return could_get_citizenship

@csrf_exempt
def process_family(request, family_uuid):
    if request.method == "GET":
        family = Person.nodes.filter(family_uuid=family_uuid)
        could_get_citizenship = dict()
        italian_relatives = family.filter(has_citizenship=True)
        for italian_relative in italian_relatives:
            could_get_citizenship = possible_citizenship(italian_relative, could_get_citizenship)
        citizenship_ids = {}
        for person in could_get_citizenship.values():
            citizenship_ids[person.id] = True
        query = "MATCH (p1:Person {family_uuid:$family_uuid}) WHERE not (p1) <-- () RETURN p1"
        params = {"family_uuid": family_uuid}
        results, meta = db.cypher_query(query, params)
        first_nodes = [Person.inflate(row[0]) for row in results]

        data = tree_data(first_nodes, citizenship_ids)
        context = {"familyUUID": family_uuid, "treeData": data}
        return render(request, template_name="italiana/tree.html", context=context)


def tree_data(nodes, citizenship_ids):
    data = []

    for node in nodes:
        person_json = person_to_json(node, citizenship_ids)

        partners = node.partner.all()
        if partners:
            person_json["marriages"] = [partner_to_json(partner, citizenship_ids) for partner in partners]

        data.append(person_json)

    return data


def person_to_json(person, citizenship_ids):
    person_json = {}
    person_json["name"] = person.name
    person_json["class"] = person.sex

    person_json["extra"] = person_extra_info(person, citizenship_ids)

    return person_json


def person_extra_info(person, citizenship_ids):
    extra = {}

    if person.birthday:
        extra["nacimiento"] = person.birthday.year
    else:
        extra["nacimiento"] = "?"

    if person.date_of_death:
        extra["defuncion"] = person.date_of_death.year
    else:
        extra["defuncion"] = ""

    extra["nacionalidades"] = []
    if person.has_citizenship:
        extra["nacionalidades"].append("it.gif")
        extra["ciudadania_disponible"] = "true"
    elif citizenship_ids.get(person.id):
        extra["ciudadania_disponible"] = "true"

    return extra


def partner_to_json(partner, citizenship_ids):
    spouse = {}

    spouse["name"] = partner.name
    spouse["class"] = partner.sex
    spouse["extra"] = person_extra_info(partner, citizenship_ids)

    offspring = partner.offspring.all()
    if offspring:
        return {"spouse": spouse, "children": tree_data(offspring, citizenship_ids), "extra": {}}

    return {"spouse": spouse, "extra": {}}

