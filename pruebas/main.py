from lib2to3.pgen2 import driver
from neo4j import GraphDatabase
import logging
from neo4j.exceptions import ServiceUnavailable

class App:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        # Don't forget to close the driver connection when you are finished with it
        self.driver.close()

    def create_person(self, id, name, sex, birth_day="1998-02-16", birth_place="Uruguay", has_citizenship=True, resignation_date_citizenship="2022-06-24"):
      with self.driver.session() as session:
        query = (
            "CREATE (p1:Person { id: $id, name: $name, sex: $sex, birth_day: date($birth_day), birth_place: $birth_place, has_citizenship: $has_citizenship, resignation_date_citizenship: date($resignation_date_citizenship) }) "
            "RETURN p1"
        )

        if (resignation_date_citizenship==""):
          resignation_date_citizenship = None
        result = session.run(query, id=id, name=name, sex=sex, birth_day=birth_day, birth_place=birth_place, has_citizenship=has_citizenship, resignation_date_citizenship=resignation_date_citizenship)
        print([record["p1"] for record in result])

    def create_relation(self, id1, id2, rel_type):
      with self.driver.session() as session:
        query = (
            "MATCH (p1:Person { id: $id1 }) "
            "MATCH (p2:Person { id: $id2 }) "
            "CREATE (p1) - [rel: IS_BROTHER] - (p2)"
            "RETURN rel"
        )
        result = session.run(query, id1=id1, id2=id2, rel_type=rel_type )
        print([record["rel"] for record in result])
    
    def find_relation(self, id1, id2, rel_type):
      with self.driver.session() as session:
        query = (
            "MATCH (p1:Person { id: $id1 }) "
            "MATCH (p2:Person { id: $id2 }) "
            "MATCH (p1) - [rel: IS_BROTHER] - (p2)"
            "RETURN rel"
        )
        result = session.run(query, id1=id1, id2=id2, rel_type=rel_type )
        print([record["rel"] for record in result])


    def create_friendship(self, person1_name, person2_name):
        with self.driver.session() as session:
            # Write transactions allow the driver to handle retries and transient errors
            result = session.write_transaction(
                self._create_and_return_friendship, person1_name, person2_name)
            for row in result:
                print("Created friendship between: {p1}, {p2}".format(p1=row['p1'], p2=row['p2']))

    @staticmethod
    def _create_and_return_friendship(tx, person1_name, person2_name):
        # To learn more about the Cypher syntax, see https://neo4j.com/docs/cypher-manual/current/
        # The Reference Card is also a good resource for keywords https://neo4j.com/docs/cypher-refcard/current/
        query = (
            "CREATE (p1:Person { name: $person1_name }) "
            "CREATE (p2:Person { name: $person2_name }) "
            "CREATE (p1)-[:KNOWS]->(p2) "
            "RETURN p1, p2"
        )
        result = tx.run(query, person1_name=person1_name, person2_name=person2_name)
        try:
            return [{"p1": row["p1"]["name"], "p2": row["p2"]["name"]}
                    for row in result]
        # Capture any errors along with the query and data for traceability
        except ServiceUnavailable as exception:
            logging.error("{query} raised an error: \n {exception}".format(
                query=query, exception=exception))
            raise

    def find_person(self, person_name):
        with self.driver.session() as session:
            result = session.read_transaction(self._find_and_return_person, person_name)
            for row in result:
                print("Found person: {row}".format(row=row))

    @staticmethod
    def _find_and_return_person(tx, person_name):
        query = (
            "MATCH (p:Person) "
            "WHERE p.name = $person_name "
            "RETURN p"
        )
        result = tx.run(query, person_name=person_name)
        return [row["p"] for row in result]


if __name__ == "__main__":
    # Aura queries use an encrypted connection using the "neo4j+s" URI scheme
    uri = "neo4j+s://ae2241fd.databases.neo4j.io"
    user = "neo4j"
    password = "E3VqtgpRegtjG-s-efEXpZB65YkjI7GKooNiWmUIwcI"
    app = App(uri, user, password)
    # app.create_person(1, "Bolo", "Male")
    # app.create_person(2, "Bola", "Female")
    # app.create_relation(1,2,"hermanos")
    app.find_person("Bolo")
    app.find_relation(1,2,"hermanos")
    app.close()