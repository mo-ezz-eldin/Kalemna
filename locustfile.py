import os
import random
import uuid

import pandas as pd
from locust import HttpUser, between, tag, task
from locust.exception import StopUser

from src.application.graphs.intents_without_needing_tools import INTENTS_CONFIGURED_WITOUT_NEEDING_TOOLS

data_file = os.path.join('benchmarks', 'all_evaluation_dataset.csv')
dt = pd.read_csv(data_file)
queries = dt.loc[dt['intent'].isin(INTENTS_CONFIGURED_WITOUT_NEEDING_TOOLS) , 'query' ].tolist()


class User(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        user_name = str(uuid.uuid4())
        password = str(uuid.uuid4())

        sign_up_response = self.client.post('/signup', json={
            'username': user_name,
            'password': password,
            'email': f'{user_name}@gmail.com',
            'phone': '01019440379',
            'default_address': 'Giza'
        })

        if sign_up_response.status_code in [200, 201]:
            response = self.client.post('/login', data={
                'username': user_name,
                'password': password
            })

            if response.status_code == 200:
                token = response.json()['access_token']
                self.client.headers.update({'Authorization': f'Bearer {token}'})
            else:
                raise StopUser()
        else:
            raise StopUser()

    @tag('testing chat')
    @task
    def test_chat_endpoint(self):
         self.client.post('/chat', json={'text': random.choice(queries)})

