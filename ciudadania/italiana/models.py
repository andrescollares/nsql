from django.db import models
from neomodel import StructuredNode, StringProperty

class Persona(StructuredNode):
    nombre = StringProperty(required=True)
