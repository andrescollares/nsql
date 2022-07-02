import json
import names
import datetime
import uuid

from django.core.management.base import BaseCommand, CommandError
from italiana.models import Person


class Command(BaseCommand):
    help = "Creates instances from a .json file"

    def add_arguments(self, parser):
        parser.add_argument("file", type=str)

    def handle(self, *args, **options):
        with open(options["file"]) as json_file:
            data = json.load(json_file)

            for family in data:
                family_number = str(uuid.uuid4())
                for person in family:
                    create_person_and_descendants(person=person, family_number=family_number)


        self.stdout.write(self.style.SUCCESS("Import successful"))


def create_person_and_descendants(person, family_number, parents=[]):
    instance = create_person(person, family_number)

    for parent in parents:
        parent.offspring.connect(instance)

    for partner in person["partners"]:

        is_married = partner.pop("is_married", False)
        partner_instance = create_person(partner, family_number=family_number)
        instance.partner.connect(partner_instance, {"is_married": is_married})

        children = partner["offspring"]
        parents = [instance, partner_instance]
        create_offspring_instances(parents=parents, family_number=family_number, children=children)


def create_person(person, family_number):
    sex = person["sex"]
    if not sex:
        sex = "OTHER"
    name = names.get_full_name(gender=sex.lower())

    instance = Person(
        name=name,
        family_uuid=family_number,
        sex=sex,
        has_citizenship=person["has_citizenship"],
    )

    birthday = person["birthday"]
    date_of_death = person["date_of_death"]
    citizenship_resignation_date = person["citizenship_resignation_date"]
    if birthday:
        instance.birthday = datetime.datetime.fromisoformat(birthday)
    if date_of_death:
        instance.date_of_death = datetime.datetime.fromisoformat(date_of_death)
    if citizenship_resignation_date:
        instance.citizenship_resignation_date = datetime.datetime.fromisoformat(citizenship_resignation_date)

    instance.save()
    return instance


def create_offspring_instances(parents, family_number, children):
    for child in children:
        create_person_and_descendants(person=child, parents=parents, family_number=family_number)
