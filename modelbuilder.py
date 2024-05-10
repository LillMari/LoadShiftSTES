# -*- coding: utf-8 -*-
"""
Created on Thu Jan 05 2024

@author: Lill Mari Engan
"""

import sys
from types import SimpleNamespace

from params import *
from variables import *
from constraints import *
from objective_function import *
from solution_writer import *

"""
Loading data
"""
DEMAND = pd.read_csv('Lastprofiler/demand.csv')  # [kWh/h]
ANSWERS = pd.read_csv('Lastprofiler/answers.csv')
PV_GEN_PROFILE = pd.read_csv('PV_profiler/pv_profil_oslo_2014.csv', skiprows=3)['electricity']  # kW/kWp
EL_TH_RATIO = pd.read_csv('PROFet/el_th_ratio.csv', index_col=0)
SPOT_PRICES = pd.read_csv('Historic_spot_prices/spot_price_2019.csv', index_col=0)  # [EUR/MWh]
FUTURE_SPOT_PRICES = pd.read_csv('Framtidspriser/future_spot_price.csv', index_col=0)  # [EUR/MWh]
NOK2024_TO_EUR = 0.087


def annualize_cost(cost, lifetime=30, interest=0.04, rounding=0):
    annuity_factor = (1 - 1 / (1 + interest) ** lifetime) / interest
    return round(cost / annuity_factor, rounding)


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


def calculate_max_hourly_temperature_diff(resu, T_target, hours_available):
    """
    the maximum temperature increase needed to be able to charge from T_min to T_target in hours_available hours.
    As it gets closer to T_max, maximum temperature increase decreases linearly.
    """
    T_max = resu['max_temperature']
    T_min = resu['min_temperature']
    return (T_target - T_min)/hours_available / (1 - (T_target - T_min)/2/(T_max - T_min))


class ModelBuilder:
    def __init__(self, *, num_houses, enable_house_hp, enable_stes, enable_local_market,
                 enable_export_tariff, use_future_prices, seed=1234):
        self.rng = np.random.default_rng(seed=seed)
        self.hours = range(8760)
        self.months = range(12)
        self.month_from_hour = get_month_from_hour_map()

        # Model settings
        self.city = 4  # Oslo, in the survey
        self.num_houses = num_houses
        self.enable_house_hp = enable_house_hp
        self.enable_stes = enable_stes
        self.enable_local_market = enable_local_market
        self.enable_export_tariff = enable_export_tariff
        self.use_future_prices = use_future_prices

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
        pv_invest_cost = annualize_cost(7000 * NOK2024_TO_EUR)

        return {'pv_production': PV_GEN_PROFILE,
                # Specific investment cost based on 2020 prices [€/kWp]
                'pv_invest_cost': pv_invest_cost,
                # Max installed capacity is limited by available rooftop area
                'max_pv_capacity': 20
                }

    def _get_house_hp_params(self):
        """
        :return:
        """
        result = {'cop': 3,
                  'max_qw': 10,  # [kWh/h]
                  'investment_cost': annualize_cost(25000/4 * NOK2024_TO_EUR, lifetime=20)}

        if not self.enable_house_hp:
            result['max_qw'] = 0

        return result

    def _get_stes_params(self):
        """
        :return:
        """
        resu = {'investment_cost': annualize_cost(124000),  # [EUR/year] cost of any STES
                'volume_investment_cost': annualize_cost(10.5),  # [EUR/year/m3] cost of STES volume
                'min_installed_volume': 1.8 * 1e4,  # [m3] ground
                'max_installed_volume': 7 * 1e4,  # [m3] ground
                'ground_base_temperature': 7,  # [deg C] the temperature at which no losses occur
                'volumetric_heat_capacity': 0.6,  # [kWh / m3K] in ground
                'heat_retainment': 0.60 ** (1 / 8760),  # [1/h] #  Chosen such that total losses are 40-60%
                'max_temperature': 80,  # [deg C]
                'min_temperature': 25,  # [deg C]
                'charge_threshold': 25,  # [deg C]
                'discharge_threshold': 80,  # [deg C]

                # heat pump parameters
                'hp_investment_cost': annualize_cost(400, lifetime=20),  # [EUR/kW of Qw]
                'hp_cop': 3,
                'hp_max_qw_possible': 300,  # [kW]  should be set higher if used by more than 100 houses

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
        if self.use_future_prices:
            prices = FUTURE_SPOT_PRICES  # [EUR/MWh]
        else:
            prices = SPOT_PRICES  # [EUR/MWh]

        return {
            'power_market_price': prices * 1e-3,  # [EUR/kWh]
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
        selling_volume_tariff = -0.05 * NOK2024_TO_EUR

        # How much is paid per household each month as a base rate [EUR]
        house_monthly_connection_base = 95.39 * NOK2024_TO_EUR
        # How much each house pays for its maximum volume each month [EUR/kW]
        peak_individual_monthly_power_tariff = 24.65 * NOK2024_TO_EUR
        # How much the neighborhood pays for its max volume each month [EUR/kW]
        peak_aggregated_monthly_import_tariff = 0
        peak_aggregated_monthly_export_tariff = 0

        if self.enable_export_tariff:
            # With the local market enabled, houses don't pay for their individual peaks
            # Instead the capacity cost is based on the total volume each hour
            # The price is scaled up such that, everything else being identical, the DSO gets the same amount

            individual_peaks, aggregated_peaks = self._get_monthly_peak_demand_sums()
            expected_capacity_cost = peak_individual_monthly_power_tariff * individual_peaks
            peak_aggregated_monthly_import_tariff = expected_capacity_cost / aggregated_peaks
            peak_aggregated_monthly_export_tariff = expected_capacity_cost / aggregated_peaks

            print(expected_capacity_cost / aggregated_peaks)
            # Houses no longer pay for capacity individually
            peak_individual_monthly_power_tariff = 0
            # The DSO no longer pays you for selling to the power market
            selling_volume_tariff = 0.0149 * NOK2024_TO_EUR  # TODO: være med, eller ikke?

        return {'volume_tax': volume_tax,
                'volume_network_tariff': volume_network_tariff,
                'selling_volume_tariff': selling_volume_tariff,
                'house_monthly_connection_base': house_monthly_connection_base,
                'peak_individual_monthly_power_tariff': peak_individual_monthly_power_tariff,
                'peak_aggregated_monthly_import_tariff': peak_aggregated_monthly_import_tariff,
                'peak_aggregated_monthly_export_tariff': peak_aggregated_monthly_export_tariff}

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
        m.enable_house_hp = bool(self.enable_house_hp)
        m.enable_stes = bool(self.enable_stes)
        m.enable_local_market = bool(self.enable_local_market)
        m.use_future_prices = bool(self.use_future_prices)

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


def lec_scenario(directory, *, num_houses, enable_house_hp, enable_stes, enable_local_market, enable_export_tariff, use_future_prices):
    global lec_model, builder

    builder = ModelBuilder(num_houses=num_houses,
                           enable_house_hp=enable_house_hp,
                           enable_stes=enable_stes,
                           enable_local_market=enable_local_market,
                           enable_export_tariff=enable_export_tariff,
                           use_future_prices=use_future_prices)

    lec_model = builder.create_lec_model()
    lec_model.model.optimize()  # Barrier method

    write_results_to_csv(lec_model, directory)


def main():
    args = sys.argv[1:]
    if len(args) == 1:
        config = args[0]
    elif len(args) == 0:
        config = input("What configuration should be executed? ")
    else:
        raise ValueError("Unexpected number of arguments")

    num_houses = 100

    investments, environment = config.split("-")
    if investments == 'base':
        enable_house_hp = False
        enable_stes = False
    elif investments == 'hp':
        enable_house_hp = True
        enable_stes = False
    elif investments == 'stes':
        enable_house_hp = False
        enable_stes = True
    else:
        raise ValueError(f"Unknown investment config: {investments}")

    enable_local_market = False
    if environment == 'now':
        enable_export_tariff = False
        use_future_prices = False
    elif environment == 'exporttariff':
        enable_export_tariff = True
        use_future_prices = False
    elif environment == 'future':
        enable_export_tariff = True
        use_future_prices = True
    else:
        raise ValueError(f"Unknown environment config: {environment}")

    print(f"Running config {config} with {num_houses} houses")
    lec_scenario(num_houses=num_houses, directory=config,
                 enable_house_hp=enable_house_hp, enable_stes=enable_stes,
                 enable_local_market=enable_local_market,
                 enable_export_tariff=enable_export_tariff,
                 use_future_prices=use_future_prices)


if __name__ == "__main__":
    main()
