from locust import HttpUser, task, between, run_single_user
import json
from random import randint, random, randrange
from names import get_full_name
from datetime import timedelta, date
import os
from family_uuids import FAMILY_UUIDS

def get_random_date(start_date, end_date):
  time_between_dates = end_date - start_date
  days_between_dates = time_between_dates.days
  random_number_of_days = randrange(days_between_dates)
  random_date = start_date + timedelta(days=random_number_of_days)

  return random_date

def create_random_family():
  qty_members =  randint(3,40)
  persons = []
  for i in range(qty_members):
    instance = {}
    instance["id"] = i
    if randint(1,100) < 50:
      instance["sex"] = 'MALE'
    else:
      instance["sex"] = 'FEMALE'
    instance["name"] = get_full_name(instance["sex"])
    if randint(1,100) < 10:
      instance["has_citizenship"] = True
    else:
      instance["has_citizenship"] = False
    instance["birthday"] = get_random_date(date(1800,1,1), date.today())
    if randint(1,1000) < 1:
      instance["citizenship_resignation_date"] = get_random_date(instance["birthday"], date.today())
    persons.append(instance)
  relations_partners = []
  for i in range(0, qty_members//2):
    relation_partners = {}
    relation_partners["first"] = randint(0, qty_members-1)
    relation_partners["second"] = randint(0, qty_members-1)
    while (relation_partners["first"] == relation_partners["second"]):
      relation_partners["second"] = randint(0, qty_members-1)
    if randint(1,100) < 75:
      relation_partners["married"] = True
    else:
      relation_partners["married"] = False
    relations_partners.append(relation_partners)
  relations_offsprings = []
  for i in range(0, qty_members//2):
    relation_offsprings = {}
    relation_offsprings["first"] = randint(0, qty_members-1)
    relation_offsprings["second"] = randint(0, qty_members-1)
    while (relation_offsprings["first"] == relation_offsprings["second"]):
      relation_offsprings["second"] = randint(0, qty_members-1)
    relations_offsprings.append(relation_offsprings)
  family = {"members": json.dumps(persons, default=str), "relations_partners": json.dumps(relations_partners), "relations_offsprings": json.dumps(relations_offsprings)}
  return family

# class QuickstartUser(HttpUser):
#     host = "http://localhost:8000/"
#     wait_time = between(1, 2)
#     family = {}
#     family_uuid = ""
    
#     def on_start(self):
#       self.family = create_random_family()
#       # grab uuid from families.json
#       self.family_uuid = "45876d60-9535-42fb-8739-87f5e46572cf"

#     @task
#     def generate_family(self):
#       self.family = create_random_family()

#     @task
#     def create_family(self):
#         with self.client.post("create_family/",data=self.family, catch_response=True) as response:
#             if response.status_code == 201:
#                 response.success()
    
#     @task
#     def check_family(self):
#         with self.client.get(f"process_family/{self.family_uuid}/", catch_response=True) as response:
#             if response.status_code == 200:
#                 response.success()

class CreateUser(HttpUser):
    host = "http://localhost:8000/"
    weight = 2
    wait_time = between(120, 180)
    
    # def on_start(self):
    #   self.family = create_random_family()

    # @task
    # def generate_family(self):
    #   self.family = create_random_family()

    @task
    def create_family(self):
        family = create_random_family()
        with self.client.post("create_family/",data=family, catch_response=True) as response:
            if response.status_code == 201:
                response.success()

class QueryUser(HttpUser):
    host = "http://localhost:8000/"
    wait_time = between(1, 2)
    family = {}
    weight = 8
    def on_start(self):
        familiy_index = randint(0, len(FAMILY_UUIDS)-1)
        self.family_uuid = FAMILY_UUIDS[familiy_index]

    @task
    def get_new_family_uuid(self):
        familiy_index = randint(0, len(FAMILY_UUIDS)-1)
        self.family_uuid = FAMILY_UUIDS[familiy_index]

    @task
    def check_family(self):
        with self.client.get(f"process_family/{self.family_uuid}/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()

if __name__ == "__main__":
    run_single_user(CreateUser)
    run_single_user(QueryUser)