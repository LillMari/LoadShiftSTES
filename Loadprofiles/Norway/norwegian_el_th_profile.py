import pandas as pd
import numpy as np

"""
Loading data
"""
DEMAND = pd.read_csv('demand.csv')  # [kWh/h]
ANSWERS = pd.read_csv('answers.csv')
EL_TH_RATIO = pd.read_csv('../../PROFet/el_th_ratio.csv', index_col=0)
OUTSIDE_TEMPERATURES = pd.read_csv('../../Profiles/Norway/temperature_profile.csv',
                                   index_col=0)['temperature [degC]']


def get_household_summary():
    ids = pd.read_csv('household_ids.csv', index_col=0)
    id_counts = ids['IDs'].value_counts()
    households = ANSWERS[ANSWERS['ID'].isin(ids['IDs'])]
    num_household = households.filter(regex='ID|Q17|Q18').copy()
    num_household['children'] = num_household[['Q18_1', 'Q18_2', 'Q18_3', 'Q18_4']].sum(axis=1)
    num_household['adults'] = num_household[['Q18_5', 'Q18_6', 'Q18_7', 'Q18_8']].sum(axis=1)
    # Q18_8: retired
    type = pd.Series()
    for i, row in num_household.iterrows():
        if row['adults'] == 1:
            if row['children'] > 0:
                type[i] = 'FamilySingleWorker'
            elif row['Q18_8'] > 0:
                type[i] = 'SingleRetired'
            else:
                type[i] = 'SingleWorker'
        if row['adults'] > 1:
            if row['children'] > 0:
                type[i] = 'FamilyDualWorker'
            elif row['Q18_8'] > 0:
                type[i] = 'DualRetired'
            else:
                type[i] = 'DualWorker'
    num_household['type'] = type
    num_household.set_index('ID', inplace=True)
    num_household['weight'] = id_counts
    household_type = num_household.groupby('type')['weight'].sum()
    household_type.to_csv('household_types.csv')


def get_valid_household_ids(city):
    """
    :param city:
    :return:
    """

    candidates = ANSWERS
    candidates = candidates[candidates['Q_City'] == city]
    candidates = candidates[candidates['Q7'].isin((2, 3))]  # Gjorde ikke strømsparingstiltak
    candidates = candidates[candidates['Q28'].isin((1, 3))]  # Elektrisk oppvarming av tappevann
    candidates = candidates[candidates['Q27_6'] == 0]  # Oljefyr
    candidates = candidates[candidates['Q27_7'] == 0]  # Fjernvarme
    candidates = candidates[candidates['Q27_5'] == 0]  # Peis
    candidates = candidates[candidates['Q27_3'] == 0]  # Varmepumpe
    candidates = candidates[candidates['Q22'] != 5]   # 'Annet' på type bolig
    candidates = candidates[candidates['ID'].isin(DEMAND['ID'].unique())]
    return candidates['ID']


def find_el_th_ratio(id):
    building_type_map = {1: 'House', 2: 'House', 3: 'House', 4: 'Apartment'}
    answers = ANSWERS[ANSWERS['ID'] == id].iloc[0]
    building = building_type_map[answers['Q22']]  # Type of building
    el_th_ratio = EL_TH_RATIO[building]
    return el_th_ratio


def extract_load_profile(id):
    load_profile = DEMAND[DEMAND['ID'] == id]
    # Demand data contains some hours from 2020 and 2022, so cut them out
    load_profile = load_profile[load_profile['Date'].str.contains('2021')]
    load_profile = load_profile.reset_index(drop=True)['Demand_kWh']

    el_th_ratio = find_el_th_ratio(id).reset_index(drop=True)
    el_load = load_profile * el_th_ratio
    th_load = load_profile * (1 - el_th_ratio)
    return el_load, th_load


def get_load_profiles(city, num_houses, rng, hours):
    all_ids = get_valid_household_ids(city)
    ids = rng.choice(all_ids, size=(num_houses,), replace=True)

    el_load_profiles = {}
    th_load_profiles = {}
    for i, house_id in enumerate(ids):
        el_load, th_load = extract_load_profile(house_id)
        el_load_profiles[i] = el_load
        th_load_profiles[i] = th_load

    el_load_profiles_df = pd.DataFrame(el_load_profiles, index=hours)
    th_load_profiles_df = pd.DataFrame(th_load_profiles, index=hours)
    return el_load_profiles_df, th_load_profiles_df, pd.Series(ids, name='IDs')


def create_load_profiles():
    rng = np.random.default_rng(seed=1234)
    city = 4  # Oslo, in the survey
    num_houses = 100
    hours = range(8760)

    el_demand, th_demand, ids = get_load_profiles(city, num_houses, rng, hours)

    el_demand.to_csv('../../Profiles/Norway/el_demand.csv')
    th_demand.to_csv('../../Profiles/Norway/th_demand.csv')
    ids.to_csv('household_ids.csv')


if __name__ == '__main__':
    # create_load_profiles()
    get_household_summary()
