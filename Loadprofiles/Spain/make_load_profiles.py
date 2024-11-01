import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def month_xticks(ax):
    months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    month_hours = [m * 24 for m in months]
    month_hours_cum = [sum(month_hours[:x]) for x in range(12)]
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    ax.set_xticks(month_hours_cum)
    ax.set_xticklabels(month_names)


def find_week_number(start_day, profile):
    for t in range(len(profile)):
        profile.loc[t, 'week'] = int(((t//24) + start_day) % 7)
    return profile


def find_user_ids(city, start, end):
    user_data = pd.read_csv('metadata.csv')
    user_data = user_data[user_data['province'] == city]
    user_data = user_data[user_data['cnae'].astype(str).str.startswith('98')]
    user_data = user_data[(user_data['self_consumption_type'].isna()) | (user_data['self_consumption_type'] == '0')]
    user_data = user_data.loc[user_data['start_date'] <= start]
    user_data = user_data.loc[user_data['end_date'] >= end]
    user_data = user_data.loc[user_data['missing_samples_pct'] <= 0.1]

    # Users with electric heating
    el_heating_user_ids = pd.read_csv('el_heating_user_ids.csv', index_col=0).iloc[:, 0].to_list()
    user_data = user_data.loc[~user_data['user'].isin(el_heating_user_ids)]
    return user_data['user']


def select_ids(seed, num_houses, city, start, end):
    rng = np.random.default_rng(seed=seed)
    all_ids = find_user_ids(city, start, end)
    ids = rng.choice(all_ids, size=(num_houses,), replace=False)
    return ids


def _remove_el_heating_columns(ids):
    el_heating_user_id = pd.read_csv('el_heating_user_ids.csv').iloc[:, 1]
    el_ids = []
    el_ids = pd.Series(ids[el_ids])
    all_el_ids = pd.concat([el_heating_user_id, el_ids], ignore_index=True)
    all_el_ids.drop_duplicates(inplace=True)
    all_el_ids.to_csv('el_heating_user_ids.csv')


def get_all_profiles_df(seed, num_houses, city, start, end, year):
    ids = select_ids(seed, num_houses, city, start, end)
    load_profiles = []
    for i, id in enumerate(ids):
        load = pd.read_csv(f'imp-pre/goi4_pre/imp_csv/{id}.csv', index_col=0)['kWh']
        load = load.rename(i)
        load = load.filter(like=year, axis=0)
        load_profiles.append(load)
    return pd.concat(load_profiles, axis=1)


def plot_load_profiles(agg=False):
    load_profiles = pd.read_csv('demand.csv', index_col=0).reset_index(drop=True)
    plt.figure(figsize=(9, 5))
    if agg:
        load_profiles = load_profiles.sum(axis=1)
    else:
        load_profiles = load_profiles.iloc[:, 50:]
        grouping = 8760 // 12
        load_profiles = load_profiles.groupby(load_profiles.index // grouping).sum()
        load_profiles.index = ((load_profiles.index + 0.5) * grouping).astype(int)
    sns.lineplot(load_profiles)
    plt.xlabel('Hour [h]')
    plt.ylabel('Load [kWh]')
    plt.show()


def create_load_profiles():
    seed = 123
    num_houses = 100
    city = 'Madrid'
    start = '2019-01-01'
    end = '2020-01-01'
    year = '2019'

    load_profiles = get_all_profiles_df(seed, num_houses, city, start, end, year)
    load_profiles.reset_index(drop=True, inplace=True)
    load_profiles.to_csv('../../Profiles/Spain/el_demand.csv')


def main():
    create_load_profiles()
    # plot_load_profiles(agg=True)


if __name__ == '__main__':
    main()
