import json
import names

from django.core.management.base import BaseCommand, CommandError
from italiana.models import Person


class Command(BaseCommand):
    help = "Creates instances from a .json file"

    def add_arguments(self, parser):
        parser.add_argument("file", type=str)

    def handle(self, *args, **options):
        with open(options["file"]) as json_file:
            data = json.load(json_file)

            family_number = 0
            for family in data:
                for person in family:
                    create_person_and_descendants(person=person, family_number=family_number)

                family_number += 1

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
    name = names.get_full_name(gender=sex)

    return Person.objects.create(
        name=name,
        family=family_number,
        sex=sex,
        birthday=person["birthday"],
        has_citizenship=person["has_citizenship"],
        citizenship_resignation_date=person["citizenship_resignation_date"],
    )


def create_offspring_instances(parents, family_number, children):
    for child in children:
        create_person_and_descendants(person=child, parents=parents, family_number=family_number)
