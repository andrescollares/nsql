from neomodel import (
    StructuredNode,
    StructuredRel,
    StringProperty,
    DateProperty,
    BooleanProperty,
    RelationshipTo,
    IntegerProperty,
)


class PartnerRel(StructuredRel):
    is_married = BooleanProperty(required=True)


class Person(StructuredNode):
    name = StringProperty(required=True)
    family = IntegerProperty(required=True, index=True)
    SEXES = {"male": "Male", "female": "Female", "other": "Other"}
    sex = StringProperty(required=True, choices=SEXES)
    birthday = DateProperty(required=False)
    has_citizenship = BooleanProperty(required=True)
    citizenship_resignation_date = DateProperty(required=False)

    partner = RelationshipTo("Person", "PARTNER", model=PartnerRel)
    offspring = RelationshipTo("Person", "OFFSPRING")
