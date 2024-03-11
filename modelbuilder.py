# -*- coding: utf-8 -*-
"""
Created on Thu Jan 05 2024

@author: Lill Mari Engan
"""

import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import numpy as np
from types import SimpleNamespace

from params import *
from variables import *
from constraints import *
from objective_function import *
from solution_writer import *

"""
Loading data
"""
# prices = pd.read_csv('Framtidspriser/results_output_Operational.csv')
DEMAND = pd.read_csv('Lastprofiler_sigurd/demand.csv')
ANSWERS = pd.read_csv('Lastprofiler_sigurd/answers.csv')
PV_GEN_PROFILE = pd.read_csv('PV_profiler/pv_profil_oslo.csv', skiprows=3)['electricity']  # kW/kWp
EL_TH_RATIO = pd.read_csv('PROFet/el_th_ratio.csv', index_col=0)
SPOT_PRICES = pd.read_csv('Historic_spot_prices/spot_price.csv', index_col=0)  # [EUR/MWh]
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
    load_profile = load_profile[load_profile['Date'].str.contains('2021')]
    load_profile = load_profile.reset_index(drop=True)['Demand_kWh']

    el_th_ratio = find_el_th_ratio(id).reset_index(drop=True)
    el_load = load_profile * el_th_ratio
    th_load = load_profile * (1 - el_th_ratio)
    return el_load, th_load


def get_month_from_hour_map():
    """
    Gives information about the hours and months of a non-leap year.
    :return: a mapping from the 8760 different hours of the year, to the month. Both 0-indexed.
    """
    days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    month_from_hour = [month for month, days in enumerate(days_per_month) for _ in range(days * 24)]

    return month_from_hour


def get_hourly_power_volume_tariff(month_from_hour, first_day_of_year=4):
    """
    Gives volume network tariff for each hour of the year, given the first day of the year (friday = 4)
    Taken from https://www.elvia.no/nettleie/alt-om-nettleiepriser/nettleiepriser-for-privatkunder/
    Includes taxes
    """
    # volume tariff for grid import [EUR/kWh]
    winter_day = .3954 * NOK2024_TO_EUR
    winter_night = .3209 * NOK2024_TO_EUR
    summer_day = .4825 * NOK2024_TO_EUR
    summer_night = .4075 * NOK2024_TO_EUR

    hourly_power_volume_tariff = np.zeros(shape=len(month_from_hour))  # [EUR/kWh]
    for t, month in enumerate(month_from_hour):
        hour_in_day = t % 24
        day_in_week = ((t//24) + first_day_of_year) % 7

        is_winter = month in [0, 1, 2]              # January - March
        is_weekday = day_in_week in range(0, 5)     # Mon - Fri
        is_daytime = hour_in_day in range(6, 22)    # 06:00 - 22:00

        if is_winter:
            if is_weekday and is_daytime:
                hourly_power_volume_tariff[t] = winter_day
            else:
                hourly_power_volume_tariff[t] = winter_night
        else:
            if is_weekday and is_daytime:
                hourly_power_volume_tariff[t] = summer_day
            else:
                hourly_power_volume_tariff[t] = summer_night

    return hourly_power_volume_tariff


def get_volume_taxes(month_from_hour):
    """
    Only the tax part (Elavgift) of the volume tariff
    Taken from https://www.elvia.no/nettleie/alt-om-nettleiepriser/nettleiepriser-for-privatkunder/
    """
    winter_tax = 0.0951 * NOK2024_TO_EUR
    summer_tax = 0.1644 * NOK2024_TO_EUR

    hourly_power_volume_tax = np.zeros(shape=len(month_from_hour))  # [EUR/kWh]
    for t, month in enumerate(month_from_hour):
        is_winter = month in [0, 1, 2]  # January - March
        hourly_power_volume_tax[t] = (winter_tax if is_winter else summer_tax)
    return hourly_power_volume_tax


class ModelBuilder:
    def __init__(self, *, num_houses, enable_stes, enable_local_market, seed=1234):
        self.rng = np.random.default_rng(seed=seed)
        self.hours = range(8760)
        self.months = range(12)
        self.month_from_hour = get_month_from_hour_map()

        # Model settings
        self.city = 4  # Oslo, in the survey
        self.num_houses = num_houses
        self.enable_stes = enable_stes
        self.enable_local_market = enable_local_market

        self.el_demand_profiles, self.th_demand_profiles = self._get_load_profiles()
        self.load_params = self._get_load_params()
        self.pv_params = self._get_pv_params()
        self.stes_params = self._get_stes_params()
        self.house_hp_params = self._get_house_hp_params()
        self.power_market_params = self._get_power_market_params()
        self.local_market_params = self._get_local_market_params()
        self.tariff_and_tax_params = self._get_tariff_and_tax_params()

    def _get_load_profiles(self):
        all_ids = get_valid_household_ids(self.city)
        ids = self.rng.choice(all_ids, size=(self.num_houses,), replace=True)

        el_load_profiles = {}
        th_load_profiles = {}
        for i, house_id in enumerate(ids):
            el_load, th_load = extract_load_profile(house_id)
            el_load_profiles[i] = el_load
            th_load_profiles[i] = th_load

        el_load_profiles_df = pd.DataFrame(el_load_profiles, index=self.hours)
        th_load_profiles_df = pd.DataFrame(th_load_profiles, index=self.hours)
        return el_load_profiles_df, th_load_profiles_df

    def _get_load_params(self):
        return {'el_demand': self.el_demand_profiles,
                'th_demand': self.th_demand_profiles}

    def _get_monthly_peak_demand_sums(self):
        """
        Calculates the sum of peak demand for each month in two ways.
        The first adds up the individual peak monthly demands per house,
        while the second aggregates all demands first, and then finds the monthly peak.
        The first value probably higher than the second, and never lower.
        """
        total_demand = self.el_demand_profiles + self.th_demand_profiles
        total_demand['lec'] = total_demand.sum(axis=1)
        total_demand['month'] = self.month_from_hour
        monthly_peaks = total_demand.groupby('month').max()

        individual_monthly_peak_sum = monthly_peaks.iloc[:, 0:self.num_houses].sum().sum()
        aggregated_monthly_peak_sum = monthly_peaks.loc[:, 'lec'].sum()

        return individual_monthly_peak_sum, aggregated_monthly_peak_sum

    def _get_pv_params(self):
        """
        pv_invest_cost [EUR/kWp]
        :return:
        """
        pv_invest_cost = annualize_cost(21000 * NOK2024_TO_EUR)
        if self.enable_stes:
            pv_invest_cost = annualize_cost(18000 * NOK2024_TO_EUR)

        return {'pv_production': PV_GEN_PROFILE,
                # Specific investment cost based on 2020 prices [€/kWp]
                'pv_invest_cost': pv_invest_cost,
                # Max installed capacity is limited by available rooftop area
                'max_pv_capacity': 15
                }

    def _get_house_hp_params(self):
        """
        :return:
        """
        # TODO: finn verdier
        return {'cop': 3,
                'max_qw': 0  # [kWh/h]
                }

    def _get_stes_params(self):
        """
        :return:
        """
        # TODO: Ta med investering i pumpe og størrelse
        resu = {'investment_cost': annualize_cost(195000),  # [EUR/year] cost of any STES
                'cap_investment_cost': annualize_cost(8.9 / 20),  # [EUR/year/kWh] cost of STES capacity
                'min_installed_capacity': 4 * 1e5,  # [kWh] of stored heat
                'max_installed_capacity': 1.3 * 1e6,  # [kWh] of stored heat
                'heat_retainment': 0.60 ** (1 / (6 * 30 * 24)),  # [1/h] #
                'charge_hp_investment_cost': 0,
                'charge_eta': 0.99,
                'charge_cop': 3,
                'charge_max_qw': 250,  # kWh/h TODO: Base on investment?
                'discharge_eta': 0.99,
                'discharge_cop': 100,
                'discharge_max_qw': 250,  # kWh/h TODO: Base on investment?
                }

        if not self.enable_stes:
            resu['investment_cost'] = 0
            resu['min_installed_capacity'] = 0
            resu['max_installed_capacity'] = 0

        return resu


    def _get_power_market_params(self):
        return {
            'power_market_price': SPOT_PRICES * 1e-3,  # [EUR/kWh]
            'max_grid_import': 3 * 63 * 230 / 1000,  # [kWh/h]
            'max_grid_export': 3 * 63 * 230 / 1000  # [kWh/h]
            }

    def _get_local_market_params(self):
        return {'export_eta': 0.995}

    def _get_tariff_and_tax_params(self):

        # Values based on today's tariff from Elvia, and today's Elavgift

        # Tax (Elavgift) per volume of power [EUR/kWh]
        volume_tax = get_volume_taxes(self.month_from_hour)

        # Tariff paid per kW each hour of the year [EUR/kWh]
        volume_network_tariff = get_hourly_power_volume_tariff(self.month_from_hour)
        # The volume tariff includes taxes, so remove them to make the values separate
        volume_network_tariff = volume_network_tariff - volume_tax
        # Tariff paid per kW of power sold to the power market. [EUR/kW]
        selling_volume_tariff = -0.05 * NOK2024_TO_EUR  # TODO: MVA

        # How much is paid per household each month as a base rate [EUR]
        house_monthly_connection_base = 24.65 * NOK2024_TO_EUR
        # How much each house pays for its maximum volume each month [EUR/kW]
        peak_individual_monthly_power_tariff = 95.39 * NOK2024_TO_EUR
        # How much the neighborhood pays for its max volume each month [EUR/kW]
        peak_aggregated_monthly_power_tariff = 0

        if self.enable_local_market:
            # With the local market enabled, houses don't pay for their individual peaks
            # Instead the capacity cost is based on the total volume each hour
            # The price is scaled up such that, everything else being identical, the DSO gets the same amount
            individual_peaks, aggregated_peaks = self._get_monthly_peak_demand_sums()
            expected_capacity_cost = peak_individual_monthly_power_tariff * individual_peaks
            peak_aggregated_monthly_power_tariff = expected_capacity_cost / aggregated_peaks
            # Houses no longer pay for capacity individually
            peak_individual_monthly_power_tariff = 0

            # The DSO no longer pays you for selling to the power market
            selling_volume_tariff = 0

        return {'volume_tax': volume_tax,
                'volume_network_tariff': volume_network_tariff,
                'selling_volume_tariff': selling_volume_tariff,
                'house_monthly_connection_base': house_monthly_connection_base,
                'peak_individual_monthly_power_tariff': peak_individual_monthly_power_tariff,
                'peak_aggregated_monthly_power_tariff': peak_aggregated_monthly_power_tariff,
                }

    def create_base_model(self):
        m = SimpleNamespace()
        m.model = gp.Model("stes_model")

        # Sets
        m.t = list(self.hours)
        m.months = list(self.months)
        m.h = list(range(self.num_houses))
        m.sign = [1, -1]

        # Useful conversions
        m.month_from_hour = list(self.month_from_hour)

        # Configuration
        m.enable_stes = bool(self.enable_stes)
        m.enable_local_market = bool(self.enable_local_market)

        return m

    def create_lec_model(self):
        """
        Creates a linear model of households with energy and heating needs (parameters).
        Power grid electricity is priced as a parameter, while local market prices are variable.
        """

        m = self.create_base_model()

        # Parameters
        set_demand_params(m, self.load_params)
        set_pv_params(m, self.pv_params)
        set_power_market_params(m, self.power_market_params)
        set_local_market_params(m, self.local_market_params)
        set_stes_params(m, self.stes_params)
        set_house_hp_params(m, self.house_hp_params)
        set_tariff_and_tax_params(m, self.tariff_and_tax_params)

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


def lec_scenario(directory, *, num_houses=5, enable_stes, enable_local_market):
    global lec_model, builder

    builder = ModelBuilder(num_houses=num_houses,
                           enable_stes=enable_stes,
                           enable_local_market=enable_local_market)

    lec_model = builder.create_lec_model()
    lec_model.model.optimize()

    write_results_to_csv(lec_model, directory)


def main():
    lec_scenario(num_houses=100, directory='BaseScenario', enable_stes=False, enable_local_market=False)
    # lec_scenario(num_houses=100, directory='stes', enable_stes=True, enable_local_market=False)
    # lec_scenario(num_houses=100, directory='stes_lec', enable_stes=True, enable_local_market=True)


if __name__ == "__main__":
    main()
