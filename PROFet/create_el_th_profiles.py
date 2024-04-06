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

TEMPERATURE = pd.read_csv('../Temperaturprofiler/temperatur_blindern2021.csv')['temperature [degC]'].to_list()


def get_token(filename):
    with open(filename) as file:
        secret = file.readline()
    return secret


def create_payload(building, reg, tout, startdate='2021-01-01', eff_e=0, eff_n=0, vef=0):
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
        "StartDate": startdate,
        "Areas": {
            building: {
                "Reg": reg,
                "Eff-E": eff_e,
                "Eff-N": eff_n,
                "Vef": vef
            },
        },
        "RetInd": False,
        "Country": "Norway",
        "TimeSeries": {
            "Tout": tout,
            'HolidayFlag': None}
    }

    r = predict.post(api_url, json=payload)
    data = r.json()
    df = pd.DataFrame.from_dict(data)
    df.index = pd.to_datetime(df.index.astype('int64'), unit='ms')

    el_th_ratio = (df['Electric'] + df['DHW']) / (df['Electric'] + df['DHW'] + df['SpaceHeating'])
    return el_th_ratio


def main():
    house_ratio = create_payload("Hou", 1, TEMPERATURE)
    apt_ratio = create_payload('Apt', 1, TEMPERATURE)
    ratio_df = pd.DataFrame({'House': house_ratio, 'Apartment': apt_ratio})
    ratio_df.to_csv('el_th_ratio.csv')


if __name__ == "__main__":
    main()
