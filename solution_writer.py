import pandas as pd
import os
import shutil
import pyomo.environ as pyo


def series_from_dict(values, name, folder=None):
    if type(values) != dict:
        values = values.extract_values()
    s = pd.Series(data=values, name=name)
    if folder is not None:
        s.to_csv(f'{folder}/{name}.csv', index=len(s) > 1)
    return s


def dataframe_from_dict(values):
    if type(values) != dict:
        values = values.extract_values()
    df = pd.DataFrame()
    for (col, row), value in values.items():
        df.loc[row, col] = value
    return df


def write_results_to_csv(m, directory):
    path = f'Results/{directory}'

    # Clear result path
    shutil.rmtree(path, ignore_errors=True)
    os.makedirs(path)

    series_from_dict(m.pv_installed_capacity, 'pv_installed_capacity', path)

    dataframe_from_dict(m.grid_import).sum(axis=1).to_csv(f'{path}/grid_import.csv')
    dataframe_from_dict(m.grid_export).sum(axis=1).to_csv(f'{path}/grid_export.csv')
    dataframe_from_dict(m.local_import).sum(axis=1).to_csv(f'{path}/local_import.csv')

    series_from_dict(m.stes_capacity, 'stes_capacity', path)
    series_from_dict(m.stes_soc, 'stes_soc', path)

    dataframe_from_dict(m.stes_charge_hp_qw).sum(axis=1).to_csv(f'{path}/stes_charge.csv')
    dataframe_from_dict(m.peak_monthly_house_volume).to_csv(f'{path}/peak_monthly_volume.csv')

    th_demand = dataframe_from_dict(m.th_demand).sum(axis=1)
    th_demand.to_csv(f'{path}/th_demand.csv')
    el_demand = dataframe_from_dict(m.el_demand).sum(axis=1)
    el_demand.to_csv(f'{path}/el_demand.csv')

    total_demand = th_demand + el_demand
    total_demand.to_csv(f'{path}/total_demand.csv')

    series_from_dict({None: pyo.value(m.lec_objective)}, 'total_cost', path)
