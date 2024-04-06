import gurobipy
import pandas as pd
import numpy as np
import gurobipy as gp
import os
import shutil


def evaluate(data):
    """Takes a scalar and evaluates it to a number"""
    if isinstance(data, gurobipy.LinExpr):
        return data.getValue()
    elif isinstance(data, gurobipy.Var):
        return data.X
    return data


def series_from_data(data, name, folder=None):
    data = evaluate(data)
    if isinstance(data, gp.tupledict):
        s = pd.Series(index=data.keys(), data=(evaluate(x) for x in data.values()), name=name)
    elif isinstance(data, np.ndarray) or isinstance(data, list):
        s = pd.Series(data=data, name=name)
    else:
        if not isinstance(data, dict):
            # Assume the value is a single scalar we want to write to a file
            data = {None: data}
        s = pd.Series(data=data, name=name)

    if folder is not None:
        s.to_csv(f'{folder}/{name}.csv', index=len(s) > 1)
    return s


def dataframe_from_data(rows, columns, data):
    if isinstance(data, np.ndarray) or isinstance(data, list):
        df = pd.DataFrame(index=rows, columns=columns, data=data)
    else:
        df = pd.DataFrame(index=rows, columns=columns)
        for (row, col), value in data.items():
            df.loc[row, col] = evaluate(value)

    return df


def write_results_to_csv(m, directory):
    path = f'Results/{directory}'

    # Clear result path
    shutil.rmtree(path, ignore_errors=True)
    os.makedirs(path)

    series_from_data(m.pv_installed_capacity, 'pv_installed_capacity', path)

    dataframe_from_data(m.t, m.h, m.grid_import).sum(axis=1).rename("grid_import").to_csv(f'{path}/grid_import.csv')
    dataframe_from_data(m.t, m.h, m.grid_export).sum(axis=1).rename("grid_export").to_csv(f'{path}/grid_export.csv')

    if m.enable_stes:
        stes_volume = series_from_data(m.stes_volume, 'stes_volume', path)
        stes_soc = series_from_data(m.stes_soc, 'stes_soc', path)
        # TODO: Replace
        stes_temperature = stes_soc / stes_volume[0] / m.volumetric_heat_capacity + m.ground_base_temperature
        stes_temperature.rename("stes_temperature").to_csv(f'{path}/stes_temperature.csv')


        series_from_data(m.stes_charge_qw, "stes_charge_qw", path)
        series_from_data(m.stes_discharge_qc, "stes_discharge_qc", path)
        series_from_data(m.hp_direct_qw, "hp_direct_qw", path)
        series_from_data(m.hp_max_qw, "hp_max_qw", path)

    if m.enable_local_market:
        dataframe_from_data(m.t, m.h,
                            m.local_import).sum(axis=1).rename("local_import").to_csv(f'{path}/local_import.csv')

    dataframe_from_data(m.t, m.h, m.peak_monthly_house_volume).to_csv(f'{path}/peak_monthly_house_volume.csv')
    series_from_data(m.peak_monthly_total_volume, 'peak_monthly_total_volume', path)

    th_demand = dataframe_from_data(m.t, m.h, m.th_demand).sum(axis=1)
    th_demand.rename("th_demand").to_csv(f'{path}/th_demand.csv')
    el_demand = dataframe_from_data(m.t, m.h, m.el_demand).sum(axis=1)
    el_demand.rename("el_demand").to_csv(f'{path}/el_demand.csv')

    total_demand = th_demand + el_demand
    total_demand.rename("total_demand").to_csv(f'{path}/total_demand.csv')

    # sources of heat going to th_demand each hour of the year
    resistive_heating = dataframe_from_data(m.t, m.h, m.electric_heating).sum(axis=1)
    house_hp_heating = dataframe_from_data(m.t, m.h, m.house_hp_qw).sum(axis=1)
    stes_discharge_qc = series_from_data(m.stes_discharge_qc, "stes_discharge_qc")
    stes_discharge_qw = stes_discharge_qc / (1 - 1/m.stes_discharge_cop)
    stes_hp_direct_qw = series_from_data(m.hp_direct_qw, 'hp_direct_qw')
    heating_data = {'resistive_heating': resistive_heating}
    if m.enable_stes:
        heating_data['stes_heating'] = stes_discharge_qw
        heating_data['stes_hp_direct'] = stes_hp_direct_qw
    if m.enable_house_hp:
        heating_data['house_hp_heating'] = house_hp_heating
    heating_sources = pd.DataFrame(index=m.t, data=heating_data)
    heating_sources.to_csv(f'{path}/heating_sources.csv')

    # Extract the value of each linear expression that makes up the total objective function
    series_from_data({name: evaluate(term) for name, term in m.objective_terms.items()}, 'objective_terms', path)
