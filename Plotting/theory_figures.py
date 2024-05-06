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

    plt.figure(figsize=(6, 3))
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

    plt.figure(figsize=(6, 3))
    sns.lineplot(load)
    plt.ylabel('Hourly consumption [GWh/h]')
    plt.xlabel('Percentage of year [%]')

    ax = plt.gca()
    ax.set_ylim(ymin, ymax)

    ax.set_xticks(np.linspace(0, 1, 11) * length)
    ax.xaxis.set_major_formatter(ticker.PercentFormatter(xmax=length))
    ax.set_yticks(np.linspace(ymin, ymax, 6))

    y = load[int(0.1 * length)]
    x = (0.1 * length)

    plt.margins(x=0)
    plt.vlines(x=x, ymin=ymin, ymax=y, ls='--', colors='gray')
    plt.hlines(y=y, xmin=xmin, xmax=x, ls='--', colors='gray')
    plt.plot(x, y, color='gray', marker='o')
    ax.text(x + 100, y + 0.2, f'({y:.0f} GWh/h, 10%)', color='dimgray')
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

    plt.figure(figsize=(6, 3))
    plt.grid()
    sns.lineplot(data=price2030, x='Week', y='Mean_EUR', label='Weekly mean electricity price')

    plt.gca().fill_between(price2030['Week'], lower, upper, alpha=0.2, label='Weekly price variation')
    plt.margins(x=0)
    plt.ylabel('Electricity price [cents/kWh]')
    plt.legend(loc='lower right')
    plt.xlim(1, 52)
    plt.ylim(0, 10)
    plt.gca().set_xlabel('Week')
    plt.tight_layout()
    if save:
        plt.savefig('theory_figures/weekly_electricity_price_2030.pdf')
    plt.show()


def plot_production_and_load_profile():
    grouping = 24

    load_profiles_statnett = pd.read_csv('plotting_data/ProductionConsumption-2023.csv', sep=';')
    total_load = load_profiles_statnett['Consumption'] / 1e6
    total_daily_load = total_load.groupby(total_load.index // grouping + 1).sum()

    pv_profile = pd.read_csv('../PV_profiler/pv_profil_oslo_2014.csv', skiprows=3)['electricity']  # kW/kWp
    pv_profile = pv_profile * 10  # 10 kW_p system
    total_daily_pv = pv_profile.groupby(pv_profile.index // grouping + 1).sum()

    plt.figure(figsize=(7, 3))
    ax = plt.gca()
    ax2 = plt.twinx()

    ax2.plot(total_daily_load, label="Load", lw=3)
    ax2.set_ylabel("Daily load [TWh/day]")
    ax2.set_ylim(0, total_daily_load.max()*1.2)
    ax2.legend(loc="upper right")

    ax.plot(total_daily_pv, label="PV production", color="lightblue", lw=3)
    ax.set_ylabel("Daily PV production [kWh/day]")
    ax.set_xlabel("Day")
    ax.set_xlim(0, 8760//grouping)
    ax.set_ylim(0, total_daily_pv.max()*1.2)
    ax.grid()
    ax.legend(loc="upper left")

    plt.tight_layout()
    plt.savefig('theory_figures/load_and_pv.pdf')
    plt.show()


if __name__ == '__main__':
    # plot_yearly_load_profile(save=True)
    # plot_yearly_duration_curve(save=True)
    # plot_daily_load_profile()
    # plot_mean_2030_prices(save=True)
    plot_production_and_load_profile()

