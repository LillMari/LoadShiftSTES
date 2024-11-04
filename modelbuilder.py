# -*- coding: utf-8 -*-
"""
Created on Thu Jan 05 2024

@author: Lill Mari Engan
"""
import sys
from types import SimpleNamespace
from ortools.linear_solver import pywraplp

from params import *
from variables import *
from constraints import *
from objective_function import *
from solution_writer import *

"""
Loading data
"""
NOK2024_TO_EUR = 0.087


def annualize_cost(cost, lifetime=30, interest=0.04, rounding=0):
    annuity_factor = (1 - 1 / (1 + interest) ** lifetime) / interest
    return round(cost / annuity_factor, rounding)


def get_month_from_hour_map():
    """
    Gives information about the hours and months of a non-leap year.
    :return: a mapping from the 8760 different hours of the year, to the month. Both 0-indexed.
    """
    days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    month_from_hour = [month for month, days in enumerate(days_per_month) for _ in range(days * 24)]

    return month_from_hour


def get_month_to_hour_map():
    month_from_hour = get_month_from_hour_map()
    month_to_hour = {month: [i for i, x in enumerate(month_from_hour) if x == month] for month in range(0, 12)}
    return month_to_hour


def calculate_max_hourly_temperature_diff(resu, T_target, hours_available):
    """
    the maximum temperature increase needed to be able to charge from T_min to T_target in hours_available hours.
    As it gets closer to T_max, maximum temperature increase decreases linearly.
    """
    T_max = resu['max_temperature']
    T_min = resu['min_temperature']
    return (T_target - T_min)/hours_available / (1 - (T_target - T_min)/2/(T_max - T_min))


def get_heatpump_cop_from_temperature(temperature):
    """
    Given the outside temperature, estimates the COP of an air source heat pump
    TODO:  velg cop-formel
    6.08 - 0.0941*dT + 0.000464*dT^2  (https://doi.org/10.1016/j.apenergy.2024.123647)
    2.375 + 1.59166667 * temperature + 0.29166667 * temperature ** 2   From Plotting/heatpump_COP.py
    """
    # return 6.08 - 0.0941 * (T_sink - temperature) + 0.000464 * (T_sink - temperature)**2
    if temperature > 22:
        temperature = 22
    elif temperature < -13:
        temperature = -13
    # Polynomial fit from papers
    return 2.49917178e+00 + 6.45541257e-02 * temperature + 4.46479209e-04 * temperature ** 2


class ModelBuilder:
    def __init__(self, *, country, enable_house_hp, enable_stes, seed=1234):
        self.rng = np.random.default_rng(seed=seed)
        self.hours = range(8760)
        self.months = range(12)
        self.month_from_hour = get_month_from_hour_map()
        self.month_to_hour = get_month_to_hour_map()
        self.available_countries = ['Norway', 'Germany', 'Spain']
        self.country = country

        # Model settings
        self.enable_house_hp = enable_house_hp
        self.enable_stes = enable_stes

        # Profiles
        self.el_demand_profiles = pd.read_csv(f'Profiles/{country}/el_demand.csv', index_col=0)
        self.th_demand_profiles = pd.read_csv(f'Profiles/{country}/th_demand.csv', index_col=0)
        self.pv_profile = pd.read_csv(f'Profiles/{country}/pv_profile.csv', skiprows=3)['electricity']  # kW/kWp
        self.temperature_profile = pd.read_csv(f'Profiles/{country}/temperature_profile.csv', index_col=0)[
            'temperature [degC]']
        self.spot_price = self._get_import_price()

        self.num_houses = len(self.el_demand_profiles.columns)
        self.load_params = self._get_load_params()
        self.pv_params = self._get_pv_params()
        self.stes_params = self._get_stes_params()
        self.house_hp_params = self._get_house_hp_params()
        self.power_market_params = self._get_power_market_params()
        self.tariff_and_tax_params = self._get_tariff_and_tax_params()

    def _get_import_price(self):
        return pd.read_csv(f'Profiles/{self.country}/spot_price.csv', index_col=0) * 1e-3  # [EUR/kWh]

    def _get_hourly_power_volume_tariff(self, first_day_of_year=4):
        """ volume tariff for grid import [EUR/kWh] """
        pass

    def _get_volume_taxes(self):
        pass

    def _get_feed_in_tariff(self):
        """ PV feed in remuneration [EUR/kWh]"""
        return self.spot_price

    def _get_feed_in_tax(self):
        return 0

    def _get_house_monthly_connection_base(self):
        return 0

    def _get_peak_individual_monthly_power_tariff(self):
        return 0

    def _get_vat(self):
        """ Value added tax """
        pass

    def _get_electricity_bill_lb(self):
        """ Lower bound on monthly electricity bill """
        return -np.inf

    def _get_load_params(self):
        return {'el_demand': self.el_demand_profiles,
                'th_demand': self.th_demand_profiles}

    def _get_pv_params(self):
        pv_invest_cost = annualize_cost(7000 * NOK2024_TO_EUR)  # [EUR/kWp]

        return {'pv_production': self.pv_profile,
                # Specific investment cost based on 2020 prices [EUR/kWp]
                'pv_invest_cost': pv_invest_cost,
                # Max installed capacity is limited by available rooftop area [kWp]
                'max_pv_capacity': 20
                }

    def _get_cop_per_hour(self):
        """ Calculates an estimated COP for a heat pump operating at each hour of the year """
        return [get_heatpump_cop_from_temperature(t) for t in self.temperature_profile]

    def _get_house_hp_params(self):
        """
        :return:
        """
        result = {'cop': self._get_cop_per_hour(),  # Air temperature delivered by the heat pump
                  'max_qw': 10,  # [kWh/h]
                  'investment_cost': annualize_cost(25000/4 * NOK2024_TO_EUR, lifetime=20)}

        if not self.enable_house_hp:
            result['max_qw'] = 0

        return result

    def _get_stes_params(self):
        """
        :return:
        """
        water_temp = 70  # [deg C]
        resu = {'investment_cost': annualize_cost(124000),  # [EUR/year] cost of any STES
                'volume_investment_cost': annualize_cost(10.5),  # [EUR/year/m3] cost of STES volume
                'min_installed_volume': 1.8 * 1e4,  # [m3] ground
                'max_installed_volume': 7 * 1e4,  # [m3] ground
                'ground_base_temperature': 7,  # [deg C] the temperature at which no losses occur
                'volumetric_heat_capacity': 0.6,  # [kWh / m3K] in ground
                'heat_retainment': 0.60 ** (1 / 8760),  # [1/h] #  Chosen such that total losses are 40-60%
                'water_temperature': water_temp,
                'max_temperature': 60,  # [deg C] (not really used to limit the STES, only to calculate charge rate)
                'min_temperature': 25,  # [deg C]

                # STES heat pump parameters
                'hp_investment_cost': annualize_cost(400, lifetime=20),  # [EUR/kW of Qw]
                'hp_cop': self._get_cop_per_hour(),
                'hp_max_qw_possible': 500,  # [kW]  should be set higher if used by more than 100 houses

                # In and out of STES parameters
                'charge_eta': 0.99,
                'discharge_eta': 0.99,
                'discharge_cop': 750,  # Discharging is not actually using a heat pump, so the "COP" is very high
                }

        max_temp_diff = calculate_max_hourly_temperature_diff(resu, T_target=60, hours_available=200)
        resu['max_temperature_increase'] = max_temp_diff
        resu['max_temperature_decrease'] = max_temp_diff

        if not self.enable_stes:
            resu['investment_cost'] = 0
            resu['min_installed_volume'] = 0
            resu['max_installed_volume'] = 0
            resu['hp_max_qw_possible'] = 0

        return resu

    def _get_power_market_params(self):
        return {
            'power_market_price': self.spot_price,  # [EUR/kWh]
            'max_grid_import': 3 * 63 * 230 / 1000,  # [kWh/h]
            'max_grid_export': 3 * 63 * 230 / 1000  # [kWh/h]
            }

    def _get_tariff_and_tax_params(self):
        # Tax (Elavgift) per volume of power [EUR/kWh]
        volume_tax = self._get_volume_taxes()
        # Value added tax
        vat = self._get_vat()
        # Tariff paid per kW each hour of the year [EUR/kWh]
        volume_network_tariff = self._get_hourly_power_volume_tariff()
        # Tariff paid per kWh of power sold to the power market. [EUR/kWh]
        feed_in_tariff = self._get_feed_in_tariff()
        # Tax paid per kWh of power sold to the power market. [EUR/kWh]
        feed_in_tax  = self._get_feed_in_tax()
        # Lower bound on monthly electricity bill
        el_bill_lb = self._get_electricity_bill_lb()

        # How much is paid per household each month as a base rate [EUR]
        house_monthly_connection_base = self._get_house_monthly_connection_base()
        # How much each house pays for its maximum volume each month [EUR/kW]
        peak_individual_monthly_power_tariff = self._get_peak_individual_monthly_power_tariff()

        return {'volume_tax': volume_tax,
                'vat': vat,
                'volume_network_tariff': volume_network_tariff,
                'feed_in_tariff': feed_in_tariff,
                'feed_in_tax': feed_in_tax,
                'el_bill_lb': el_bill_lb,
                'house_monthly_connection_base': house_monthly_connection_base,
                'peak_individual_monthly_power_tariff': peak_individual_monthly_power_tariff}

    def create_base_model(self, solver=None):
        m = SimpleNamespace()
        # m.model = gp.Model("stes_model")

        if solver is None:
            solver = pywraplp.Solver.GLOP_LINEAR_PROGRAMMING
        m.solver = pywraplp.Solver("stes_model", solver)

        # Sets
        m.t = list(self.hours)
        m.months = list(self.months)
        m.h = list(range(self.num_houses))
        m.sign = [1, -1]

        # Useful conversions
        m.month_from_hour = list(self.month_from_hour)
        m.month_to_hour = self.month_to_hour

        # Configuration
        m.enable_house_hp = bool(self.enable_house_hp)
        m.enable_stes = bool(self.enable_stes)

        return m

    def create_lec_model(self, solver=None):
        """
        Creates a linear model of households with energy and heating needs (parameters).
        Power grid electricity is priced as a parameter, while local market prices are variable.
        """

        m = self.create_base_model(solver=solver)

        # Parameters
        set_demand_params(m, self.load_params)
        set_pv_params(m, self.pv_params)
        set_power_market_params(m, self.power_market_params)
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


