# -*- coding: utf-8 -*-
"""
Created on Fri Mar  4 08:44:56 2022

@author: hwaln
"""
import requests
import json
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
import pandas as pd
import ast


def get_token(filename):
    with open(filename) as file:
        secret = file.readline()
    return secret


token_url = "https://identity.byggforsk.no/connect/token"
api_url = "https://flexibilitysuite.byggforsk.no/api/Profet"

client_id = 'profet_2024'
client_secret = get_token('token.txt')

api_client = BackendApplicationClient(client_id=client_id)
oauth = OAuth2Session(client=api_client)
token = oauth.fetch_token(token_url=token_url, client_id=client_id,
        client_secret=client_secret)

predict = OAuth2Session(token=token)

payload = {
    "StartDate": "1990-01-01",              # Initial date (influences weekday/weekend. N.B. In Shops and Culture_Sport, Saturday has a different profile than Sunday)
    "Areas": {                              # Spesification of areas for building categories and efficiency levels
        "Off": {                            # building category office, add sections for multiple categories. Available categories are ['Hou', 'Apt', 'Off', 'Shp', 'Htl', 'Kdg', 'Sch', 'Uni', 'CuS', 'Nsh', 'Hos', 'Other']
            "Reg": 100000,                  # Category regular. 'Regular' means average standard of buildings in the stock
            "Eff-E": 100000,                # Category Efficient Existing. 'Efficient' means at about TEK10 standard, representing an ambitious yet realistic target for energy efficient renovation
            "Eff-N": 50000,                 # Category Efficient New. 'Efficient' means at about TEK10 standard. Gives same results as Eff-E
            "Vef": 50000                    # Category Very Efficient.'Very efficient' means at about passive house standard
        },
        # "Other": {                          # Category other represents the composition of the total norwegian building stock
        #     "Reg": 1000000,
        #     "Eff-E": 1000000,
        #     "Eff-N": 500000,
        #     "Vef": 500000
        # }
    },
    "RetInd": False,                        # Boolean, if True, individual profiles for each category and efficiency level are returned
#    "Country": "Norway",                   # Optional, possiblity to get automatic holiday flags from the python holiday library.
#     "TimeSeries": {                         # Time series input. If not used. 1 year standard Oslo climate is applied. If time series is included, prediction will be same length as input. Minimum 24 timesteps (hours)
#         "Tout": [1.1, 1.1, 1.1, 0.9, 1.2, 1.1, 1.1, 1.3,
#                  1.5, 1.6, 1.7, 1.6, 2.0, 2.2, 2.0, 2.4,
#                  2.3, 2.3, 2.3, 2.2, 1.7, 1.4, 1.1, 1.6]
# #        'HolidayFlag':[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
#     }
}

r = predict.post(api_url, json=payload)
data = r.json()
df = pd.DataFrame.from_dict(data)
df.index = pd.to_datetime(df.index.astype('int64'), unit='ms')
print(df)
