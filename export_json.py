import json

from django.core.management.base import BaseCommand
from gestoria.models import Familia


class Command(BaseCommand):
    help = "fills a json with all families"

    # def add_arguments(self, parser):
    #     parser.add_argument("file", type=str)

    def handle(self, *args, **options):
        data = []
        for familia in Familia.objects.all():
            familia_dict = []
            for familiar in familia.primera_generacion.all():
                familiar_descendientes_dict = self.familiar_descendientes(familiar)

                familia_dict.append(familiar_descendientes_dict)

            data.append(familia_dict)

        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        self.stdout.write(self.style.SUCCESS("Export successful"))

    def familiar_descendientes(self, familiar):
        familiar_dict = self.familiar_dict(familiar)

        parejas = []
        for pareja in familiar.get_parejas():
            if pareja.primer_integrante == familiar:
                partner = pareja.segundo_integrante
            else:
                partner = pareja.primer_integrante

            pareja_dict = self.familiar_dict(partner)

            hijos = []
            for hijo in pareja.hijos.all():
                hijos.append(self.familiar_descendientes(hijo))
            pareja_dict["offspring"] = hijos

            parejas.append(pareja_dict)

        familiar_dict["partners"] = parejas

        return familiar_dict

    def familiar_dict(self, familiar):
        # if familiar.partida_de_nacimiento:
        #     if familiar.partida_de_nacimiento.fecha:
        #         nacimiento = familiar.partida_de_nacimiento.fecha.year
        if familiar.fecha_de_nacimiento_desde:
            nacimiento = familiar.fecha_de_nacimiento_desde.year
        else:
            nacimiento = None

        return {
            "sex": familiar.sexo,
            "birthday": nacimiento,
            "has_citizenship": "IT" in familiar.nacionalidades,
            "citizenship_resignation_date": None,
        }
