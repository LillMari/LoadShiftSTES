# -*- coding: utf-8 -*-
"""
Created on Thu Jan 05 2024

@author: Lill Mari Engan
"""

import pyomo.environ as pyo
import pandas as pd
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


def annualize_cost(cost, lifetime=30, interest=0.05):
    # TODO: sjekk lifetime og interest
    annuity_factor = (1 - 1/(1+interest)**lifetime)/interest
    return cost/annuity_factor


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


class ModelBuilder:
    def __init__(self, num_houses, seed=1234):
        self.rng = np.random.default_rng(seed=seed)
        self.hours = range(8760)

        self.city = 4  # Oslo, in the survey
        self.num_houses = num_houses

        self.load_params = self._get_load_params(self.city, self.num_houses)
        self.pv_params = self._get_pv_params()
        self.stes_params = self._get_stes_params()
        self.hp_params = self._get_hp_params()
        self.power_market_params = self._get_power_market_params()
        self.dso_params = self._get_dso_params()

    def _get_load_profiles(self, city, num_houses):
        # TODO: mulig å ikke gjøre dobbelt opp for thermal og electric?
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
        el_load_profiles_df, th_load_profiles_df = self._get_load_profiles(city, num_houses)
        return {'el_load': el_load_profiles_df,
                'thermal_load': th_load_profiles_df}

    def _get_pv_params(self):
        """
        pv_invest_cost [kr/kWp]
        :return:
        """
        return {'pv_production': PV_GEN_PROFILE,
                'pv_invest_cost': annualize_cost(3000),   # TODO: Finn investeringskostnad
                'max_pv_capacity': 15}   # TODO: Finn fornuftig grense

    def _get_hp_params(self):
        """

        :return:
        """
        # TODO: finn verdier
        return {'air_to_floor_cop': 3, 'air_to_floor_max_heating': 10}

    def _get_stes_params(self):
        """

        :return:
        """
        # TODO: finn greie parameterverdier
        return {'investment_cost': annualize_cost(0),
                'cap_investment_cost': annualize_cost(0),
                'installed_capacity': 0,
                'init_SOC': 0,
                'max_charge': 0,
                'max_discharge': 0,
                'eta_charge': 0,
                'eta_discharge': 0,
                'heat_loss': 0
            }

    def _get_power_market_params(self):
        # TODO: Legg til ordentlige priser
        price = np.sin((np.arange(8760)/8760 + 0.2)*2*np.pi)*.5 + .55

        return {'power_market_price': pd.Series(data=price, index=self.hours),  # EUR/kWh
                'tax': 0,  # TODO
                'NM': 1  # TODO
                }

    def _get_dso_params(self):

        return {
            'existing_transmission_capacity': 100,  # kW TODO: Proper value
            'grid_invest_cost': 10,  # [EUR/kWp] TODO: Proper value
            'transmission_loss': 0.1  # TODO: Proper value
        }

    def create_base_model(self):
        m = pyo.ConcreteModel()

        # Sets
        m.t = pyo.Set(initialize=self.hours)
        m.h = pyo.Set(initialize=range(self.num_houses))
        m.h_t = pyo.Set(initialize=m.h * m.t)
        m.sign = pyo.Set(initialize=[1, -1])

        return m

    def create_lec_model(self, tariff_params):
        """
        Creates a linear model of households with energy and heating needs (parameters).
        Power grid electricity is priced as a parameter, while local market prices are variable.

        :param tariff_params: a dict describing network tariffs, that are paid to the DSO. Contains:
         - 'vnt': volumetric network tariff [EUR/kWh]
         - 'cnt': capacity-based network tariff [EUR/kWp]
        :return: the created model
        """
        m = self.create_base_model()

        # Parameters
        set_load_params(m, self.load_params)
        set_pv_params(m, self.pv_params)
        set_power_market_params(m, self.power_market_params)
        set_STES_params(m, self.stes_params)
        set_hp_params(m, self.hp_params)
        set_tariff_params(m, tariff_params)

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
        """
        pass

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


def lec_scenario():
    builder = ModelBuilder(5)

    opt = pyo.SolverFactory('gurobi_direct')
    lec_model = builder.create_lec_model(tariff_params={'cnt': 0, 'vnt': 0})


def main():
    lec_scenario()


if __name__ == "__main__":
    main()
