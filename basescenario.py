# -*- coding: utf-8 -*-
"""
Created on Thu Jan 05 2024

@author: Lill Mari Engan
"""

import pyomo.environ as pyo
import pandas as pd
import os
import numpy as np
from params import *
from variables import *
from constraints import *
from objective_function import *

"""
Loading data
"""
# prices = pd.read_csv('Framtidspriser/results_output_Operational.csv')
DEMAND = pd.read_csv('Lastprofiler_sigurd/demand.csv')
ANSWERS = pd.read_csv('Lastprofiler_sigurd/answers.csv')
PV_GEN_PROFILE = pd.read_csv('PV_profiler/pv_profil_oslo.csv', skiprows=3)['electricity']  # kW/kWp
EL_TH_RATIO = pd.read_csv('PROFet/el_th_ratio.csv', index_col=0)
SPOT_PRICES = pd.read_csv('Historic_spot_prices/spot_price.csv')
NOK2024_TO_EUR = 0.087


def annualize_cost(cost, lifetime=30, interest=0.05):
    annuity_factor = (1 - 1 / (1 + interest) ** lifetime) / interest
    return cost / annuity_factor


def get_valid_household_ids(city):
    """
    :param city:
    :return:
    """

    candidates = ANSWERS
    candidates = candidates[candidates['Q_City'] == city]
    candidates = candidates[candidates['Q28'].isin((1, 3))]
    candidates = candidates[candidates['Q27_6'] == 0]  # Oljefyr
    candidates = candidates[candidates['Q27_7'] == 0]  # Fjernvarme
    candidates = candidates[candidates['Q27_5'] == 0]  # Peis
    candidates = candidates[candidates['Q27_3'] == 0]  # Varmepumpe
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
    load_profile = load_profile[load_profile['Date'].str.contains('2021')]
    load_profile = load_profile.reset_index(drop=True)['Demand_kWh']

    el_th_ratio = find_el_th_ratio(id).reset_index(drop=True)
    el_load = load_profile * el_th_ratio
    th_load = load_profile * (1 - el_th_ratio)
    return el_load, th_load


def hour_month_conversions():
    """
    Gives information about the hours and months of a non-leap year

    First returns a mapping from the 8760 different hours of the year, to the month. Both 0-indexed.

    The next two return values are the first and last hour of the year belonging to each month.
    Example: Month [1], February starts at hour 744 and ends with hour 1415 (inclusive)
    """
    days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    month_from_hour = [month for month, days in enumerate(days_per_month) for _ in range(days * 24)]
    first_hour_in_month = np.cumsum([0] + days_per_month[:-1]) * 24
    last_hour_in_month = np.cumsum(days_per_month) * 24 - 1

    return month_from_hour, first_hour_in_month, last_hour_in_month


def get_hourly_power_volume_tariff(month_from_hour, first_day_of_year=4):
    """
    Gives volume network tariff for each hour of the year, given the first day of the year (friday = 4)
    :return:
    """
    power_volume_tariff = {'volume_tariff_winter_day': 39.54 * NOK2024_TO_EUR,
                         'volume_tariff_winter_night': 32.09 * NOK2024_TO_EUR,
                         'volume_tariff_summer_day': 48.25 * NOK2024_TO_EUR,
                         'volume_tariff_summer_night': 40.75 * NOK2024_TO_EUR
                         }
    hourly_power_volume_tariff = np.zeros(shape=8760)
    for t in range(8760):
        hour_in_day = t % 24
        day_in_week = ((t//24) + first_day_of_year) % 7
        month = month_from_hour[t]
        if month in [0, 1, 2]:                                                              # Winter
            if day_in_week in range(0, 6) and hour_in_day in range(6, 22):                  # Weekday and daytime
                hourly_power_volume_tariff[t] = power_volume_tariff['volume_tariff_winter_day']
            else:                                                                           # Nighttime og weekend
                hourly_power_volume_tariff[t] = power_volume_tariff['volume_tariff_winter_night']
        else:                                                                               # Summer
            if day_in_week in range(0, 6) and hour_in_day in range(6, 22):                  # Weekday and daytime
                hourly_power_volume_tariff[t] = power_volume_tariff['volume_tariff_summer_day']
            else:                                                                           # Nighttime og weekend
                hourly_power_volume_tariff[t] = power_volume_tariff['volume_tariff_summer_night']

        return hourly_power_volume_tariff


class ModelBuilder:
    def __init__(self, num_houses, seed=1234):
        self.rng = np.random.default_rng(seed=seed)
        self.hours = range(8760)
        self.months = range(12)
        self.month_from_hour, self.first_hour_in_month, self.last_hour_in_month = hour_month_conversions()

        self.city = 4  # Oslo, in the survey
        self.num_houses = num_houses

        self.load_params = self._get_load_params(self.city, self.num_houses)
        self.pv_params = self._get_pv_params()
        self.stes_params = self._get_stes_params()
        self.house_hp_params = self._get_house_hp_params()
        self.power_market_params = self._get_power_market_params()
        self.tariff_params = self._get_tariff_params()

    def _get_load_profiles(self, city, num_houses):
        all_ids = get_valid_household_ids(city)
        ids = self.rng.choice(all_ids, size=(num_houses,), replace=True)

        el_load_profiles = {}
        th_load_profiles = {}
        for i, house_id in enumerate(ids):
            el_load, th_load = extract_load_profile(house_id)
            el_load_profiles[i] = el_load
            th_load_profiles[i] = th_load

        el_load_profiles_df = pd.DataFrame(el_load_profiles, index=self.hours)
        th_load_profiles_df = pd.DataFrame(th_load_profiles, index=self.hours)
        return el_load_profiles_df, th_load_profiles_df

    def _get_load_params(self, city, num_houses):
        el_demand_profiles_df, th_demand_profiles_df = self._get_load_profiles(city, num_houses)
        return {'el_demand': el_demand_profiles_df,
                'th_demand': th_demand_profiles_df}

    def _get_pv_params(self):
        """
        pv_invest_cost [kr/kWp]
        :return:
        """
        return {'pv_production': PV_GEN_PROFILE,
                'pv_invest_cost': annualize_cost(450),  # Specific investment cost based on 2020 prices [€/kWp]
                'max_pv_capacity': 15}  # Max installed capacity is limited by available rooftop area

    def _get_house_hp_params(self):
        """
        :return:
        """
        # TODO: finn verdier
        return {'cop': 3,
                'max_qw': 10  # [kWh/h]
                }

    def _get_stes_params(self, max_capacity=400*10**3):
        """
        :return:
        """
        # TODO: finn greie parameterverdier
        return {'investment_cost': annualize_cost(0),  # [EUR/year] cost of any STES
                'cap_investment_cost': annualize_cost(14/20),  # [EUR/year/kWh] cost of STES capacity
                'max_installed_capacity': max_capacity,  # [kWh] of stored heat
                'heat_retainment': 0.85 ** (1 / (6 * 30 * 24)),  # [1/h] # TODO: Value based on size
                'charge_hp_investment_cost': 0,
                'charge_eta': 0.99,
                'charge_cop': 3,
                'charge_max_qw': 100,  # kWh/h TODO: Base on investment?
                'discharge_eta': 0.99,
                'discharge_cop': 100,
                'discharge_max_qw': 100,  # kWh/h TODO: Base on investment?
                }

    def _get_power_market_params(self):
        return {'power_market_price': SPOT_PRICES.iloc[:, 1]*1e-3,  # [EUR/kWh]
                'tax': 16.69 * 1e-2,  # 2021 electricity tax [EUR/kWh]
                'NM': 0,  # Elvia sier 0 nettleie på solgt strøm, men du får ikke noe "negativ" nettleie.
                }

    def _get_tariff_params(self):
        volume_network_tariff = get_hourly_power_volume_tariff(self.month_from_hour)

        return {'peak_power_tariff': 95.39 * NOK2024_TO_EUR,
                'peak_power_base': 24.65 * NOK2024_TO_EUR,
                'volume_network_tariff': volume_network_tariff}

    def create_base_model(self):
        m = pyo.ConcreteModel()

        # Sets
        m.t = pyo.Set(initialize=self.hours)
        m.months = pyo.Set(initialize=self.months)
        m.month_from_hour = pyo.Param(m.t, initialize=self.month_from_hour)
        m.h = pyo.Set(initialize=range(self.num_houses))
        m.h_t = pyo.Set(initialize=m.h * m.t)
        m.sign = pyo.Set(initialize=[1, -1])

        return m

    def create_lec_model(self, enable_stes, enable_local_market):
        """
        Creates a linear model of households with energy and heating needs (parameters).
        Power grid electricity is priced as a parameter, while local market prices are variable.

        :param tariff_params: a dict describing network tariffs, that are paid to the DSO. Contains:
         - 'vnt': volumetric network tariff [EUR/kWh]
         - 'peak_capacity_tariff': capacity-based network tariff [EUR/kWp]
        :return: the created model
        """
        m = self.create_base_model()
        m.enable_stes = pyo.Param(initialize=enable_stes, within=pyo.Boolean)
        m.enable_local_market = pyo.Param(initialize=enable_local_market, within=pyo.Boolean)

        # Parameters
        set_demand_params(m, self.load_params)
        set_pv_params(m, self.pv_params)
        set_power_market_params(m, self.power_market_params)
        set_stes_params(m, self.stes_params)
        set_house_hp_params(m, self.house_hp_params)
        set_tariff_params(m, self.tariff_params)

        # Variables
        pv_vars(m)
        grid_vars(m)
        heating_vars(m)
        stes_vars(m)

        # Constraints
        lec_constraints(m)

        # Objective
        total_cost_objective_function(m)

        return m

    def create_dso_model(self, net_use_params):
        """
        Creates a linear model for optimizing power grid investment for the DSO.
        Takes in net usage for each household, and calculates losses and investment cost.
        Results in tariffs that cover transmission losses and investment cost.
        :param net_use_params: a dict containing net import and export data from a previous solve
         - 'grid_el_import' = (h,t) indexed grid power import per house, per hour [kWh]
         - 'grid_export' = (h,t) indexed grid power export per house, per hour [kWh]
        :return:

        m_dso = self.create_base_model()

        # Parameters
        set_dso_params(m_dso, self.dso_params, net_use_params)
        set_power_market_params(m_dso, self.power_market_params)

        # Variables
        dso_vars(m_dso)

        # Constraints
        dso_constraints(m_dso)

        # Objective function
        dso_objective_function(m_dso)

        return m_dso
        """
        pass


def write_results_to_csv(m, directory):
    if not os.path.exists(f'Results/{directory}'):
        os.makedirs(f'Results/{directory}')

    pv = m.pv_installed_capacity.extract_values()
    pd.DataFrame.from_dict(data=pv, orient='index',
                           columns=['installed_pv_capacity']).to_csv(f'Results/{directory}/installed_pv_capacity.csv')

    grid_import = pd.DataFrame.from_dict(m.grid_import.extract_values(), orient='index', columns=['grid_import'])
    grid_import = grid_import.groupby([grid_import.index.str[1]]).sum()
    grid_import.to_csv(f'Results/{directory}/grid_import.csv')

    grid_export = pd.DataFrame.from_dict(m.grid_export.extract_values(), orient='index', columns=['grid_export'])
    grid_export = grid_export.groupby([grid_export.index.str[1]]).sum()
    grid_export.to_csv(f'Results/{directory}/grid_export.csv')

    local_import = pd.DataFrame.from_dict(m.local_import.extract_values(), orient='index', columns=['local_import'])
    local_import = local_import.groupby([local_import.index.str[1]]).sum()
    local_import.to_csv(f'Results/{directory}/local_import.csv')

    local_export = pd.DataFrame.from_dict(m.local_export.extract_values(), orient='index', columns=['local_export'])
    local_export = local_export.groupby([local_export.index.str[1]]).sum()
    local_export.to_csv(f'Results/{directory}/local_export.csv')

    stes_capacity = m.stes_capacity.extract_values()
    pd.DataFrame.from_dict(data=stes_capacity, orient='index',
                           columns=['stes_capacity']).to_csv(f'Results/{directory}/stes_capacity.csv')

    monthly_peak = m.peak_monthly_volume.extract_values()
    pd.DataFrame.from_dict(data=monthly_peak, orient='index',
                           columns=['monthly_peak']).to_csv(f'Results/{directory}/peak_monthly_volume.csv')

    th_demand = pd.DataFrame.from_dict(m.th_demand.extract_values(), orient='index', columns=['th_demand'])
    th_demand = th_demand.groupby([th_demand.index.str[1]]).sum()
    th_demand.to_csv(f'Results/{directory}/th_demand.csv')

    el_demand = pd.DataFrame.from_dict(m.el_demand.extract_values(), orient='index', columns=['el_demand'])
    el_demand = el_demand.groupby([el_demand.index.str[1]]).sum()
    el_demand.to_csv(f'Results/{directory}/el_demand.csv')

    #el_demand = m.el_demand.extract_values()
    #demand = {i: th_demand[i] + el_demand[i] for i in el_demand.keys()}
    #total_demand = pd.DataFrame.from_dict(demand, orient='index', columns=['total_demand'])
    #total_demand = total_demand.groupby([total_demand.index.str[1]]).sum()
    total_demand = th_demand + el_demand
    total_demand.to_csv(f'Results/{directory}/total_demand.csv')


def lec_scenario(directory, enable_stes, enable_local_market):
    global lec_model

    builder = ModelBuilder(5)

    opt = pyo.SolverFactory('gurobi_direct')
    lec_model = builder.create_lec_model(enable_stes, enable_local_market)
    opt.solve(lec_model, tee=True)

    write_results_to_csv(lec_model, directory)


def main(directory):
    return lec_scenario(directory, enable_stes=True, enable_local_market=False)


if __name__ == "__main__":
    main('BaseScenario')
