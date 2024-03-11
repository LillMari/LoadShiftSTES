import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

from modelbuilder import extract_load_profile, get_valid_household_ids

DEMAND = pd.read_csv('Lastprofiler_sigurd/demand.csv')


def get_one_load_profile(id):
    load_profile = DEMAND[DEMAND['ID'] == id]
    load_profile = load_profile[load_profile['Date'].str.contains('2021')]
    return load_profile.reset_index(drop=True)['Demand_kWh']


def get_demand_profile(candidates):
    demand = 0
    for id in candidates:
        demand += get_one_load_profile(id)
    demand /= len(candidates)
    return demand


def plot_demand_profile_year(profile):
    plt.figure(figsize=(10, 5))
    plt.plot(profile)
    plt.title('Average yearly load profile')
    plt.show()

"""
def plot_demand_profile_day(profile):
    day_profile = profile[day*24: day*24 + 24].reset_index(drop=True)
    plt.figure(figsize=(10, 5))
    plt.plot(day_profile)

    plt.title(f'Average daily profile, day {day}')
    plt.show()
"""

def plot_duration_curve():
    pass


def main():
    candidates = get_valid_household_ids(4)
    demand_profile = get_demand_profile(candidates)
    plot_demand_profile_year(demand_profile)
    #plot_demand_profile_day(demand_profile)


if __name__ == '__main__':
    main()
