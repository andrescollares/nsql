from locust import HttpUser, task, between
import json
from random import randint
import os

class QuickstartUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
      base_path = os.path.abspath(os.getcwd())
      file_path = str(base_path) + "/pruebas/test_families.json"
      with open(file_path) as json_file:
          data = json.load(json_file)
          random_index = randint(0,len(data)-1)
          family = data[random_index]
          self.client.post("/create", family)

    @task
    def create_family(self):
        self.client.get("/hello")
        self.client.get("/world")

    @task(3)
    def view_item(self):
        for item_id in range(10):
            self.client.get(f"/item?id={item_id}", name="/item")
