import json
import names
import datetime

from django.core.management.base import BaseCommand
from italiana.models import Person


class Command(BaseCommand):
    help = "Creates Person instances from a .json file"

    def add_arguments(self, parser):
        parser.add_argument("file", type=str)

    def handle(self, *args, **options):
        with open(options["file"]) as json_file:
            data = json.load(json_file)

            for family in data:
                for person in family:
                    create_person_and_descendants(person=person)


        self.stdout.write(self.style.SUCCESS("Import successful"))


def create_person_and_descendants(person, parents=[]):
    instance = create_person(person)

    for parent in parents:
        parent.offspring.connect(instance)

    for partner in person["partners"]:

        is_married = partner.pop("is_married", False)
        partner_instance = create_person(partner)
        instance.partner.connect(partner_instance, {"is_married": is_married})

        children = partner["offspring"]
        parents = [instance, partner_instance]
        create_offspring_instances(parents=parents, children=children)


def create_person(person):
    sex = person["sex"]
    if not sex:
        sex = "OTHER"
    name = names.get_full_name(gender=sex.lower())

    instance = Person(
        name=name,
        family_uuid=person["family_uuid"],
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


def create_offspring_instances(parents, children):
    for child in children:
        create_person_and_descendants(person=child, parents=parents)
