from django_neomodel import DjangoNode
from neomodel import (
    StructuredNode,
    StructuredRel,
    StringProperty,
    DateProperty,
    BooleanProperty,
    RelationshipTo,
    UniqueIdProperty,
)


class PartnerRel(StructuredRel):
    is_married = BooleanProperty(required=True)


class Person(DjangoNode):
    uid = UniqueIdProperty()
    name = StringProperty(required=True)
    family_uuid = StringProperty(index=True, required=True, unique=False)
    SEXES = {"MALE": "Male", "FEMALE": "Female", "OTHER": "Other"}
    sex = StringProperty(required=True, choices=SEXES)
    birthday = DateProperty(required=False)
    date_of_death = DateProperty(required=False)
    has_citizenship = BooleanProperty(required=True)
    citizenship_resignation_date = DateProperty(required=False)

    partner = RelationshipTo("Person", "PARTNER", model=PartnerRel)
    offspring = RelationshipTo("Person", "OFFSPRING")

    class Meta:
        app_label = "italiana"
