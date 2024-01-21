

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def plot_one_price_profile(df, scenario, period):
    seasons = ['winter', 'spring', 'summer', 'fall']
    profile = df[((df['Scenario'] == scenario) &
                  (df['Period'] == period) &
                  (~df['Season'].str.contains('peak')))]

    return profile


def plot_price_profiles(df, scenarios, periods):
    plt.figure()
    for scenario in scenarios:
        for period in periods:
            profile = plot_one_price_profile(df, scenario, period)
            sns.lineplot(profile, x='Hour', y='Price_EURperMWh',
                         hue='Season') #, label=(period + scenario)) # TODO: endre legend
    plt.show()


def plot_PV_price():
    installed_cap = [3.3, 4.4, 5.5, 7.7]
    price = [56900, 74500, 96900, 135220]
    plt.figure()
    plt.plot(installed_cap, price)
    plt.title('Solcellespesialisten, priser')
    plt.show()


if __name__ == '__main__':

    price_profiles = pd.read_csv('Framtidspriser/filtrerte_priser.csv')
    mean_price = price_profiles[((~price_profiles['Season'].str.contains('peak')) &
                                 (price_profiles['Scenario'] != 'scenario3'))]
    mean_price = mean_price.groupby('Hour')['Price_EURperMWh'].mean()
    sns.lineplot(data=mean_price)


    scenarios = price_profiles['Scenario'].unique()
    periods = price_profiles['Period'].unique()

    plot_price_profiles(price_profiles, scenarios[3:10], periods[3:4])

    plot_PV_price()
