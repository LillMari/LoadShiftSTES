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
    m.peak_aggregated_monthly_power_tariff = param(tariff_and_tax_params['peak_aggregated_monthly_power_tariff'])


def set_house_hp_params(m, house_hp_params):
    m.house_hp_cop = param(house_hp_params['cop'])
    # Max heating energy delivered by a house's private heatpump
    m.house_hp_max_qw = param(house_hp_params['max_qw'])


def set_stes_params(m, stes_params):
    # Seasonal thermal energy storage
    m.stes_investment_cost = param(stes_params['investment_cost'])
    m.cap_investment_cost = param(stes_params['cap_investment_cost'])

    m.max_stes_capacity = param(stes_params['max_installed_capacity'])
    m.min_stes_capacity = param(stes_params['min_installed_capacity'])

    m.heat_retainment = param(stes_params['heat_retainment'])

    m.stes_charge_eta = param(stes_params['charge_eta'])
    m.stes_charge_hp_cop = param(stes_params['charge_cop'])
    m.stes_charge_hp_max_qw = param(stes_params['charge_max_qw'])

    m.stes_discharge_eta = param(stes_params['discharge_eta'])
    m.stes_discharge_hp_cop = param(stes_params['discharge_cop'])
    m.stes_discharge_hp_max_qw = param(stes_params['discharge_max_qw'])


def set_dso_params(m_dso, dso_params, net_use_params):
    # Existing transmission capacity [kW]
    m_dso.existing_transmission_capacity = param(dso_params['existing_transmission_capacity'])

    # Annualized investment cost for additional grid capacity [EUR/kW/year]
    m_dso.grid_invest_cost = param(dso_params['grid_invest_cost'])

    # Transmission loss [%]
    m_dso.transmission_loss = param(dso_params['transmission_loss'])

    # Per house hourly grid import
    m_dso.grid_el_import = param(net_use_params['grid_el_import'])
    # Per house hourly grid export
    m_dso.grid_export = param(net_use_params['grid_export'])
