from neomodel import StructuredNode, StringProperty, DateProperty, BooleanProperty, RelationshipTo, IntegerProperty


class Person(StructuredNode):
    name = StringProperty(required=True)
    family = IntegerProperty(required=True)
    SEXES = {"male": "Male", "female": "Female", "other": "Other"}
    sex = StringProperty(required=True, choices=SEXES)
    birthday = DateProperty(required=False)
    has_citizenship = BooleanProperty(required=True)
    citizenship_resignation_date = DateProperty(required=False)

    offspring = RelationshipTo("Person", "OFFSPRING")
