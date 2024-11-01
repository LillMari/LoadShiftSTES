from entsoe import EntsoePandasClient
import pandas as pd


# https://github.com/EnergieID/entsoe-py

def get_token(filename):
    with open(filename) as file:
        secret = file.readline()
    return secret


def get_historic_sport_prices(country_dict, start_y, end_y):
    print(country_dict['country'])
    client = EntsoePandasClient(api_key=get_token('token.txt'))

    start = pd.Timestamp(f'{start_y}0101', tz=country_dict['tz'])
    end = pd.Timestamp(f'{end_y}0101', tz=country_dict['tz'])
    country_code = country_dict['country_code']

    # Dump results to file
    ts = client.query_day_ahead_prices(country_code, start=start, end=end)
    # ts.to_csv(f'../Profiles/{country_dict["country"]}/spot_price.csv')  # [EUR/MWh]
    ts.to_csv(f'spot_price_{country_dict["country"]}_{start_y}.csv')  # [EUR/MWh]


country_dicts = [{'country': 'Norway', 'tz': 'Europe/Oslo', 'country_code': 'NO_1'},
                 # {'country': 'Germany', 'tz': 'Europe/Berlin', 'country_code': 'DE_LU'},
                 # {'country': 'Spain', 'tz': 'Europe/Madrid', 'country_code': 'ES'}
                 ]

for country in country_dicts:
    for year in [('2021', '2022'), ('2022', '2023'), ('2023', '2024')]:  # ('2019', '2020'), ('2020', '2021'),
        get_historic_sport_prices(country, year[0], year[1])
