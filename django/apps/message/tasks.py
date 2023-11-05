import time

import requests
from celery import shared_task


@shared_task()
def send_message(url: str, headers: dict = None, json_data: dict = None):
    retries = 5
    for _ in range(retries):
        response = requests.post(url, headers=headers, json=json_data)
        if response.status_code != 500:
            return response.status_code
        time.sleep(2)
    return 500
