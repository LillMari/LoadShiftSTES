from entsoe import EntsoePandasClient
import pandas as pd


def get_token(filename):
    with open(filename) as file:
        secret = file.readline()
    return secret


client = EntsoePandasClient(api_key=get_token('token.txt'))

start = pd.Timestamp('20190101', tz='Europe/Oslo')
end = pd.Timestamp('20200101', tz='Europe/Oslo')
country_code = 'NO_1'  # Norway


# Dump results to file
ts = client.query_day_ahead_prices(country_code, start=start, end=end)
ts.to_csv('spot_price_2019.csv')
