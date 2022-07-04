import json
import uuid

from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from datetime import datetime, date

from neomodel.match import db

from .models import Person

# Create your views here.


@csrf_exempt
@require_GET
def index(request):
    # Returns all the existing family uuids in the database
    query = "MATCH(p:Person) Return DISTINCT p.family_uuid"
    results, meta = db.cypher_query(query)
    family_uuids = [row[0] for row in results]
    return HttpResponse(json.dumps(family_uuids))


def add_family_uuid(member, family_uuid):
    member["family_uuid"] = family_uuid
    member["birthday"] = datetime.strptime(member["birthday"], "%Y-%m-%d")
    if member.get("citizenship_resignation_date"):
        member["citizenship_resignation_date"] = datetime.strptime(member["citizenship_resignation_date"], "%y-%m-%d")
    return member


@csrf_exempt
@require_POST
def create_family(request):
    data = request.POST.dict()
    members = json.loads(data["members"])
    relations_partners = json.loads(data["relations_partners"])
    relations_offspring = json.loads(data["relations_offsprings"])
    family_uuid = uuid.uuid4()
    persons = [add_family_uuid(member, family_uuid) for member in members]

    with db.transaction:
        people = Person.create(*persons)

    for relation in relations_partners:
        people[relation["first"]].partner.connect(people[relation["second"]], {"is_married": relation["married"]})

    for relation in relations_offspring:
        people[relation["first"]].offspring.connect(people[relation["second"]])
    return HttpResponse(family_uuid, status=201)

def possible_citizenship(person, could_get_citizenship):
    if person.has_citizenship or could_get_citizenship.get(person.id) or person.citizenship_resignation_date:
        # corresponde la ciudadanía hacía los hijos ?
        if person.date_of_death and person.date_of_death < date(1861, 1, 1):
            return could_get_citizenship
        if could_get_citizenship.get(person.id):
            administrative = could_get_citizenship.get(person.id)["administrative"]
        elif person.sex == "FEMALE" and person.date_of_death and person.date_of_death < date(1948, 1, 1):
            administrative = False
        else:
            administrative = True
        offspring = person.offspring.all()
        for member in offspring:
            if person.citizenship_resignation_date == None or (
                person.citizenship_resignation_date and member.birthday < person.citizenship_resignation_date
            ):
                if not could_get_citizenship.get(member.id):
                    could_get_citizenship[member.id] = {"member": member.id, "administrative": administrative}
                could_get_citizenship = possible_citizenship(member, could_get_citizenship)
    return could_get_citizenship

def tree_data_beta(nodes, citizenship_ids):
    data = []

    for node in nodes:
        person_json = person_to_json_beta(node, citizenship_ids)

        partners = node.partner.all()
        if partners:
            person_json["marriages"] = [partner_to_json_beta(partner, citizenship_ids) for partner in partners]

        data.append(person_json)

    return data


def person_to_json_beta(person, citizenship_ids):
    person_json = {}
    person_json["name"] = person.name
    person_json["class"] = person.sex

    person_json["extra"] = person_extra_info_beta(person, citizenship_ids)

    return person_json


def person_extra_info_beta(person, citizenship_ids):
    extra = {}
    extra["nacimiento"] = person.birthday.year if person.birthday else "?"
    extra["defuncion"] = person.date_of_death.year if person.date_of_death else ""

    extra["nacionalidades"] = []
    if person.has_citizenship:
        extra["nacionalidades"].append("it.gif")
        extra["ciudadano"] = "true"
    else:
        if citizenship_ids.get(person.id) and citizenship_ids.get(person.id)["administrative"]:
            extra["ciudadania_admin"] = "true"
        elif citizenship_ids.get(person.id):
            extra["ciudadania_juicio"] = "true"

    return extra


def partner_to_json_beta(partner, citizenship_ids):
    spouse = {}
    spouse["name"] = partner.name
    spouse["class"] = partner.sex
    spouse["extra"] = person_extra_info_beta(partner, citizenship_ids)

    offspring = partner.offspring.all()
    if offspring:
        return {"spouse": spouse, "children": tree_data_beta(offspring, citizenship_ids), "extra": {}}
    return {"spouse": spouse, "extra": {}}

@csrf_exempt
@require_GET
def process_family_beta(request, family_uuid):
    family = Person.nodes.filter(family_uuid=family_uuid)
    could_get_citizenship = dict()
    italian_relatives = family.filter(has_citizenship=True)
    for italian_relative in italian_relatives:
        could_get_citizenship = possible_citizenship(italian_relative, could_get_citizenship)
    query = "MATCH (p1:Person {family_uuid:$family_uuid}) WHERE not (p1) <-- () RETURN p1"
    params = {"family_uuid": family_uuid}
    results, meta = db.cypher_query(query, params)
    first_nodes = [Person.inflate(row[0]) for row in results]

    data = tree_data_beta(first_nodes, could_get_citizenship)
    context = {"familyUUID": family_uuid, "treeData": data}
    return render(request, template_name="italiana/tree.html", context=context)

@csrf_exempt
@require_GET
def process_family(request, family_uuid):
    query = "MATCH (p1:Person {family_uuid:$family_uuid}) WHERE not (p1) <-- () RETURN p1"
    params = {"family_uuid": family_uuid}
    results, meta = db.cypher_query(query, params)
    first_nodes = [Person.inflate(row[0]) for row in results]

    data = tree_data(first_nodes, [], "")
    context = {"familyUUID": family_uuid, "treeData": data}
    return render(request, template_name="italiana/tree.html", context=context)


def value_citizenship(person, parent_rel, citizenship_state):
    if citizenship_state == "NO":
        for parent in [parent_rel.start_node(), parent_rel.end_node()]:
            if (
                (parent.citizenship_resignation_date and (person.birthday < parent.citizenship_resignation_date or person.birthay > date(1992, 1, 1)))
                or parent.has_citizenship
                and not (person.date_of_death and person.date_of_death < date(1861, 1, 1) or person.citizenship_resignation_date)
            ):
                # Caso 3
                return "ADMIN"
        return "NO"
    else:
        if person.has_citizenship:
            if person.date_of_death and person.date_of_death < date(1861, 1, 1) or person.citizenship_resignation_date:
                # Caso 1 y 2
                return "NO"
            elif person.sex == "FEMALE" and person.date_of_death and person.date_of_death < date(1948, 1, 1):
                # Caso 6
                return "TRIAL"
            else:
                return "ADMIN"
        elif person.citizenship_resignation_date:
            # Caso 5
            return "NO"
        else:
            # Se continua con el mismo estado
            return citizenship_state


def tree_data(nodes, parent_rel, citizenship_state):
    data = []

    for node in nodes:
        citizenship_state = value_citizenship(node, parent_rel, citizenship_state)
        person_json = person_to_json(node, citizenship_state)

        partners = node.partner.all()
        partners_rels = [node.partner.relationship(partner) for partner in partners]
        if partners_rels:
            person_json["marriages"] = [partner_to_json(partner_rel, citizenship_state) for partner_rel in partners_rels]

        data.append(person_json)

    return data


def person_to_json(person, citizenship_state):
    person_json = {}
    person_json["name"] = person.name
    person_json["class"] = person.sex

    person_json["extra"] = person_extra_info(person, citizenship_state)

    return person_json


def person_extra_info(person, citizenship_state):
    extra = {}
    extra["nacimiento"] = person.birthday.year if person.birthday else "?"
    extra["defuncion"] = person.date_of_death.year if person.date_of_death else ""

    extra["citizenship_resignation_date"] = person.citizenship_resignation_date if person.citizenship_resignation_date else "No renunció"

    extra["nacionalidades"] = []
    if person.has_citizenship:
        extra["nacionalidades"].append("it.gif")
        extra["ciudadano"] = "true"
    else:
        if citizenship_state == "ADMIN":
            extra["ciudadania_admin"] = "true"
        elif citizenship_state == "TRIAL":
            extra["ciudadania_juicio"] = "true"

    return extra


def partner_to_json(partner_rel, citizenship_state):
    spouse_instance = partner_rel.end_node()
    spouse = {}
    spouse["name"] = spouse_instance.name
    spouse["class"] = spouse_instance.sex
    spouse["extra"] = person_extra_info(spouse_instance, citizenship_state if partner_rel.is_married else "NO")
    if partner_rel.is_married:
        icon = "💍"
    else:
        icon = "❔"

    offspring = spouse_instance.offspring.all()
    if offspring:
        return {"spouse": spouse, "children": tree_data(offspring, partner_rel, citizenship_state), "extra": {"icon": icon}}
    return {"spouse": spouse, "extra": {"icon": icon}}
