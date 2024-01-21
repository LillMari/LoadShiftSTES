import base64

import requests
import json
import pandas as pd


def get_token(filename):
    with open(filename) as file:
        client_id = file.readline().split(':')[1].strip()
        secret = file.readline().split(':')[1].strip()
    return client_id, secret


api_url = 'https://frost.met.no'

client_id, secret = get_token('frost_id.txt')
auth = (client_id, secret)
headers = {'Accept': 'application/json'}

# Source picked from API website. type = SensorSystem, (10.72, 59.9423) Blindern Oslo.
source = "SN18700"

params = {
    'sources': source,
    'elements': 'air_temperature',
    'referencetime': '2021-01-01/2022-01-01',
    'timeresolutions': 'PT1H',
    'fields': 'value,referenceTime'
}
observationIndex = 1  # observation [0] is 10m above ground, [1] is 2m

r = requests.get(f'{api_url}/observations/v0.jsonld', params=params, headers=headers, auth=auth)
print("Response length:", r.headers['Content-Length'])

#  with open("frost_results.json", "bw") as fil:
#      fil.write(r.content)

times = []
temps = []
for data_point in r.json()["data"]:
    times.append(data_point["referenceTime"])
    temps.append(data_point["observations"][observationIndex]["value"])

temperature = pd.DataFrame({'temperature [degC]': temps}, index=times)
temperature.to_csv('temperatur_blindern2021.csv')


