import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np

NOK2024_TO_EUR = 0.087


WEEK_AVERAGES = pd.read_csv('NVE_fremtid_ukesnitt.csv')
WEEK_AVERAGES = WEEK_AVERAGES[WEEK_AVERAGES['Model year'] == 2030]
# NOTE: Week is 1-indexed
WEEK_AVERAGES = WEEK_AVERAGES.set_index('Week')
# Convert mean and std dev from øre/kWh to EUR/MWh
WEEK_AVERAGES['Mean'] = WEEK_AVERAGES['Mean'] / 100 * 1000 * NOK2024_TO_EUR
# WEEK_AVERAGES['Std dev'] = WEEK_AVERAGES['Std dev'] / 100 * 1000 * NOK2024_TO_EUR

# Unit: øre/kWh
WEEK_PROFILES = pd.read_csv('NVE_fremtid_ukeprofiler.csv')
SUMMER_WEEK_PROFILE = WEEK_PROFILES['Døgnvariasjon sommer 2030']
WINTER_WEEK_PROFILE = WEEK_PROFILES['Døgnvariasjon vinter 2030']

# Convert to EUR/MWh
SUMMER_WEEK_PROFILE = SUMMER_WEEK_PROFILE / 100 * 1000 * NOK2024_TO_EUR
WINTER_WEEK_PROFILE = WINTER_WEEK_PROFILE / 100 * 1000 * NOK2024_TO_EUR

HOURS_PER_YEAR = 8760

def create_yearly_profile():
    """
    Creates an hourly price profile, in EUR/MWh
    """
    price = np.array([])
    for week in range(1, 53+1):
        # week 1 and week 53 have summerness 0
        # week 27 has summerness 1
        summerness = np.cos((week - (53+1)/2) / (53-1) * 2 * np.pi)/2 + 0.5

        # Average between summer and winter, weighted by summerness
        week_data = SUMMER_WEEK_PROFILE * summerness + WINTER_WEEK_PROFILE * (1 - summerness)

        week_data -= week_data.mean()

        if week > 52:
            week = 52
        week_data += WEEK_AVERAGES.loc[week, 'Mean']

        price = np.concatenate((price, week_data))

    assert len(price) >= HOURS_PER_YEAR
    price = price[:HOURS_PER_YEAR]

    # Cap negative prices to 0
    price[price < 0] = 0
    return price

profile = create_yearly_profile()
series = pd.Series(profile)
series.rename('Price [EUR/MWh]', inplace=True)
series.to_csv('future_spot_price_NVE_mean_only.csv')

plt.figure()
sns.lineplot(profile)
plt.title("Generated future profile")
plt.show()
