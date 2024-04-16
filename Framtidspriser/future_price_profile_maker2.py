import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np

NOK2024_TO_EUR = 0.087


WEEK_AVERAGES = pd.read_csv('NVE_fremtid_ukesnitt.csv')
WEEK_AVERAGES = WEEK_AVERAGES[WEEK_AVERAGES['Model year'] == 2030]
# NOTE: Week is 1-indexed
WEEK_AVERAGES = WEEK_AVERAGES.set_index('Week')
# Convert mean and std dev to EUR/MWh
WEEK_AVERAGES['Mean'] = WEEK_AVERAGES['Mean'] / 100 * 1000 * NOK2024_TO_EUR
WEEK_AVERAGES['Std dev'] = WEEK_AVERAGES['Std dev'] / 100 * 1000 * NOK2024_TO_EUR

PRESENT_DAY_COST_PROFILE = pd.read_csv('../Historic_spot_prices/spot_price_2019.csv', index_col=0)

HOURS_PER_YEAR = 8760

def create_yearly_profile():
    """
    Creates an hourly price profile, in EUR/MWh
    """
    price = np.array([])
    for week in range(1, 52+1):
        firsthour = (week-1)*7*24
        lasthour = week*7*24
        if week == 52:
            lasthour = len(PRESENT_DAY_COST_PROFILE)

        week_data = PRESENT_DAY_COST_PROFILE.iloc[firsthour:lasthour, 0].to_numpy()
        week_data -= week_data.mean()
        week_data /= week_data.std()

        week_data *= WEEK_AVERAGES.loc[week, 'Std dev']
        week_data += WEEK_AVERAGES.loc[week, 'Mean']

        price = np.concatenate((price, week_data))

    assert len(price) >= HOURS_PER_YEAR
    price = price[:HOURS_PER_YEAR]

    price[price < 0] = 0
    return price

profile = create_yearly_profile()
series = pd.Series(profile)
series.rename('Price [EUR/MWh]', inplace=True)
series.to_csv('future_spot_price.csv')

plt.figure()
sns.lineplot(profile)
plt.title("Generated future profile")
plt.show()
