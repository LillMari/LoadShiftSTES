import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np

NOK2024_TO_EUR = 0.087

DATA = pd.read_csv('results_output_Operational.csv')
DATA = DATA[DATA['Node'] == 'NO1']
DATA = DATA[DATA['Period'] == '2030-2035'].copy()
DATA['Price_EURperkWh'] = DATA['Price_EURperMWh'] * 1e-3

# Prices can at most differ from the week mean by this many std dev
MAX_STD = 2

WEEK_AVERAGES = pd.read_csv('NVE_fremtid_ukesnitt.csv')
WEEK_AVERAGES = WEEK_AVERAGES[WEEK_AVERAGES['Model year'] == 2030]
# NOTE: Week is 1-indexed
WEEK_AVERAGES = WEEK_AVERAGES.set_index('Week')
# Convert mean and std dev to EUR/kWh
WEEK_AVERAGES['Mean'] = WEEK_AVERAGES['Mean'] / 100 * NOK2024_TO_EUR
WEEK_AVERAGES['Std dev'] = WEEK_AVERAGES['Std dev'] / 100 * NOK2024_TO_EUR

# 53 weeks in total, the last winter week gets truncated
WEEK_TO_SEASON = ['winter'] * 9 + ['spring'] * 13 + ['summer'] * 13 + ['fall'] * 13 + ['winter'] * 5

HOURS_PER_YEAR = 8760


def plot_price_profiles(scenario):
    """Plot each week from one of the scenarios from DATA"""
    plt.figure()
    profile = DATA[DATA['Scenario'] == scenario].copy()
    means = profile.groupby('Season')['Price_EURperkWh'].mean()
    stds = profile.groupby('Season')['Price_EURperkWh'].std()

    profile['Normalized'] = (profile['Price_EURperkWh'] - profile['Season'].map(means)) / profile['Season'].map(stds)

    sns.lineplot(profile, x='Hour', y='Normalized', hue='Season')
    plt.title(f'{scenario}')
    plt.show()


def create_yearly_profile(valid_scenarios):
    """
    Creates an hourly price profile, in EUR/kWh
    :param valid_scenarios:
    """
    price = []

    rand = np.random.default_rng(seed=1)
    for week, season in enumerate(WEEK_TO_SEASON):
        scenario = rand.choice(valid_scenarios)
        week_data = DATA[(DATA['Scenario'] == scenario) & (DATA['Season'] == season)]
        assert len(week_data) == 7*24

        week_prices = week_data['Price_EURperkWh'].to_numpy()
        week_prices -= np.mean(week_prices)
        week_prices /= np.std(week_prices)
        week_prices = np.clip(week_prices, -MAX_STD, MAX_STD)

        # WEEK_AVERAGES uses 1-indexed weeks
        if week < 52:
            week += 1
        week_prices *= WEEK_AVERAGES.loc[week, 'Std dev']
        week_prices += WEEK_AVERAGES.loc[week, 'Mean']

        price.extend(week_prices)

    assert len(price) >= HOURS_PER_YEAR
    price = price[:HOURS_PER_YEAR]
    return price

valid_scenarios = ['scenario2', 'scenario4', 'scenario5', 'scenario6', 'scenario7', 'scenario9']

# for scenario in [f'scenario{i+1}' for i in range(10)]:
#    plot_price_profiles(scenario)

profile = create_yearly_profile(valid_scenarios)
series = pd.Series(profile) * 1e3
series.rename('Price [EUR/MWh]', inplace=True)
series.to_csv('future_spot_price.csv')

plt.figure()
sns.lineplot(profile)
plt.title("Generated future profile")
plt.show()
