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
                    create_person_descendants(person=person, family_number=family_number)

                family_number += 1

            self.stdout.write(self.style.SUCCESS("Import successful"))


def create_offspring_instances(parent, children):
    for child in children:
        create_person_descendants(person=child, parent=parent, family_number=parent.family)

def create_person_descendants(person, family_number, parent=None):
    sex = person["sex"]
    name = names.get_full_name(gender=sex)
    birthday = person["birthday"]
    has_citizenship = person["has_citizenship"]
    citizenship_resignation_date = person["citizenship_resignation_date"]
    children = person["offspring"]

    instance = Person.objects.create(
        name=name,
        family=family_number,
        sex=sex,
        birthday=birthday,
        has_citizenship=has_citizenship,
        citizenship_resignation_date=citizenship_resignation_date,
    )
    if parent:
        parent.offspring.connect(instance)

    create_offspring_instances(parent=instance, children=children)
