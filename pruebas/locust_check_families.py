from locust import HttpUser, task, between, run_single_user
import json
from random import randint, random, randrange
from names import get_full_name
from datetime import timedelta, date
import os
from family_uuids import FAMILY_UUIDS

class QuickstartUser(HttpUser):
    host = "http://localhost:8000/"
    # wait_time = 120
    wait_time = between(1, 3)
    family_uuid = ""
    
    def on_start(self):
        # grab uuid from families.json
        familiy_index = randint(0, len(FAMILY_UUIDS)-1)
        self.family_uuid = FAMILY_UUIDS[familiy_index]

    @task
    def check_family(self):
        with self.client.get(f"process_family/{self.family_uuid}/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()

if __name__ == "__main__":
    run_single_user(QuickstartUser)