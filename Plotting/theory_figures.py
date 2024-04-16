import matplotlib.pyplot as plt
import numpy as np
from matplotlib import ticker
import pandas as pd
import seaborn as sns


NOK2024_TO_EUR = 0.087

def month_xticks(ax):
    months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    month_hours = [m * 24 for m in months]
    month_hours_cum = [sum(month_hours[:x]) for x in range(12)]
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    ax.set_xticks(month_hours_cum)
    ax.set_xticklabels(month_names)


def plot_yearly_load_profile(save=False):

    load_profiles_statnett = pd.read_csv('plotting_data/ProductionConsumption-2023.csv', sep=';')
    load_profiles_statnett['Consumption'] /= 1000

    ymin = 8
    ymax = 24

    plt.figure(figsize=(8, 4))
    sns.lineplot(load_profiles_statnett, y='Consumption', x='Time(Local)')
    month_xticks(plt.gca())
    ax = plt.gca()
    ax.set_ylim(ymin, ymax)
    plt.ylabel('Hourly consumption [GWh/h]')
    plt.xlabel('Time')
    plt.margins(x=0)
    plt.tight_layout()
    plt.grid()
    if save:
        plt.savefig('theory_figures/yearly_load_profile_statnett.pdf')
    plt.show()


def plot_yearly_duration_curve(save=False):
    load_profiles_statnett = pd.read_csv('plotting_data/ProductionConsumption-2023.csv', sep=';')
    load = load_profiles_statnett['Consumption'] / 1000
    load = load.sort_values(ascending=False, ignore_index=True)

    length = (len(load)-1)
    ymin = 8
    ymax = 24
    xmin = 0

    plt.figure(figsize=(8, 4))
    sns.lineplot(load)
    plt.ylabel('Hourly consumption [GWh/h]')
    plt.xlabel('Percentage of year [%]')

    ax = plt.gca()
    ax.set_ylim(ymin, ymax)

    ax.set_xticks(np.linspace(0, 1, 11) * length)
    ax.xaxis.set_major_formatter(ticker.PercentFormatter(xmax=length))

    plt.margins(x=0)
    plt.vlines(x=(0.1 * length), ymin=ymin, ymax=load[int(0.1 * length)], ls='--', colors='gray')
    plt.hlines(y=load[int(0.1 * length)], xmin=xmin, xmax=(0.1 * length), ls='--', colors='gray')
    plt.plot((0.1 * length), load[int(0.1 * length)], color='gray', marker='o')
    plt.tight_layout()
    plt.grid()
    if save:
        plt.savefig('theory_figures/yearly_duration_curve_statnett.pdf')
    plt.show()


def plot_daily_load_profile(save=False):
    load_profiles_statnett = pd.read_csv('plotting_data/ProductionConsumption-2023.csv', sep=';')
    load_profiles_statnett['Consumption'] /= 1000

    for t in load_profiles_statnett.index:
        load_profiles_statnett.loc[t, 'day'] = int(((t//24) + 6) % 7)  # First day of year is a Sunday (6)

    weekdays = [0, 1, 2, 3, 4]
    weekday_profiles = load_profiles_statnett[load_profiles_statnett['day'].isin(weekdays)].copy()
    weekday_profiles['hour'] = weekday_profiles['Time(Local)'].str.extract(r" (\d\d):")
    mean_consumption = weekday_profiles.groupby('hour')['Consumption'].mean()
    ymin = 13.5
    ymax = 17

    plt.figure(figsize=(8, 4))
    sns.lineplot(data=mean_consumption)
    ax = plt.gca()
    ax.set_ylim(ymin, ymax)
    plt.ylabel('Hourly consumption [GWh/h]')
    plt.xlabel('Time')
    plt.margins(x=0)
    plt.tight_layout()
    plt.grid()
    if save:
        plt.savefig('theory_figures/weekday_load_profile_statnett.pdf')
    plt.show()


def plot_mean_2030_prices(save=False):
    price_profile = pd.read_csv('plotting_data/NVE_fremtid_ukesnitt.csv')

    price_profile.loc[:, 'Mean_EUR'] = price_profile['Mean'] * NOK2024_TO_EUR
    price_profile.loc[:, 'Std_dev_EUR'] = price_profile['Std dev'] * NOK2024_TO_EUR
    price2030 = price_profile[price_profile['Model year'] == 2030]
    lower = price2030['Mean_EUR'] - price2030['Std_dev_EUR']
    upper = price2030['Mean_EUR'] + price2030['Std_dev_EUR']

    plt.figure(figsize=(8, 4))
    sns.lineplot(data=price2030, x='Week', y='Mean_EUR', label='Weekly mean electricity price')

    plt.gca().fill_between(price2030['Week'], lower, upper, alpha=0.2, label='Weekly price variation')
    plt.margins(x=0)
    plt.ylabel('Electricity price [cents/kWh]')
    plt.legend(loc='lower right')
    if save:
        plt.savefig('theory_figures/weekly_electricity_price_2030.pdf')
    plt.show()


if __name__ == '__main__':
    # plot_yearly_load_profile(save=True)
    # plot_yearly_duration_curve(save=True)
    # plot_daily_load_profile()
    plot_mean_2030_prices(save=True)

