# -*- coding: utf-8 -*-
"""
Created on Thu Jan 09 2024

@author: Lill Mari Engan
"""

import pandas as pd
import numpy as np


def param(data):
    if isinstance(data, pd.DataFrame):
        if len(data.columns) == 1:
            return param(data.iloc[:, 0])
        return data.values
    if isinstance(data, pd.Series):
        return data.values
    if isinstance(data, list):
        return np.array(data)
    return data


def set_demand_params(m, demand_params):
    m.el_demand = param(demand_params['el_demand'])
    m.th_demand = param(demand_params['th_demand'])


def set_pv_params(m, pv_params):
    m.pv_production = param(pv_params['pv_production'])
    m.pv_invest_cost = param(pv_params['pv_invest_cost'])
    m.max_pv_capacity = param(pv_params['max_pv_capacity'])


def set_power_market_params(m, power_market_params):
    m.power_market_price = param(power_market_params['power_market_price'])
    m.max_grid_import = param(power_market_params['max_grid_import'])
    m.max_grid_export = param(power_market_params['max_grid_export'])


def set_local_market_params(m, local_market_params):
    m.local_market_export_eta = param(local_market_params['export_eta'])


def set_tariff_and_tax_params(m, tariff_and_tax_params):
    # Taxes (Elavgift) paid per unit of energy [EUR/kWh]
    m.tax = param(tariff_and_tax_params['volume_tax'])

    # Tariff volume cost per kWh, excluding taxes, indexed by hour [EUR/kWh]
    m.volume_network_tariff = param(tariff_and_tax_params['volume_network_tariff'])

    # Tariff volume cost of selling to the power market. Can be negative if selling is incentivized [EUR/kWh]
    m.selling_volume_tariff = param(tariff_and_tax_params['selling_volume_tariff'])

    # What each house pays monthly [EUR]
    m.house_monthly_connection_base = param(tariff_and_tax_params['house_monthly_connection_base'])

    # capacity tariff, based on individual peak each month [EUR/kW]
    m.peak_individual_monthly_power_tariff = param(tariff_and_tax_params['peak_individual_monthly_power_tariff'])

    # shared capacity tariff, based on aggregated peak each month [EUR/kW]
    m.peak_aggregated_monthly_import_tariff = param(tariff_and_tax_params['peak_aggregated_monthly_import_tariff'])

    # shared capacity export tariff, based on aggregated peak each year [EUR/kW]
    m.peak_aggregated_monthly_export_tariff = param(tariff_and_tax_params['peak_aggregated_monthly_export_tariff'])


def set_house_hp_params(m, house_hp_params):
    m.house_hp_cop = param(house_hp_params['cop'])
    # Max heating energy delivered by a house's private heatpump
    m.house_hp_max_qw = param(house_hp_params['max_qw'])
    m.house_hp_investment_cost = param(house_hp_params['investment_cost'])


def set_stes_params(m, stes_params):
    # Seasonal thermal energy storage
    m.stes_investment_cost = param(stes_params['investment_cost'])
    m.stes_volume_investment_cost = param(stes_params['volume_investment_cost'])

    m.max_stes_volume = param(stes_params['max_installed_volume'])
    m.min_stes_volume = param(stes_params['min_installed_volume'])

    m.ground_base_temperature = param(stes_params['ground_base_temperature'])
    m.volumetric_heat_capacity = param(stes_params['volumetric_heat_capacity'])
    m.heat_retainment = param(stes_params['heat_retainment'])

    m.water_stes_temperature = param(stes_params['water_temperature'])
    m.min_stes_temperature = param(stes_params['min_temperature'])

    m.max_temperature_increase = param(stes_params['max_temperature_increase'])
    m.max_temperature_decrease = param(stes_params['max_temperature_decrease'])

    m.stes_hp_investment_cost = param(stes_params['hp_investment_cost'])
    m.stes_hp_cop = param(stes_params['hp_cop'])
    m.stes_hp_max_qw_possible = param(stes_params['hp_max_qw_possible'])

    m.stes_charge_eta = param(stes_params['charge_eta'])
    m.stes_discharge_eta = param(stes_params['discharge_eta'])
    m.stes_discharge_cop = param(stes_params['discharge_cop'])
