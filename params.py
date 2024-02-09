# -*- coding: utf-8 -*-
"""
Created on Thu Jan 09 2024

@author: Lill Mari Engan
"""

import pyomo.environ as pyo
import pandas as pd


def df_init_wrapper(array):
    def init_rule(m, col, row):
        return array.iloc[row, col]
    return init_rule


def array_init_wrapper(array):
    def init_rule(m, idx):
        return array[idx]
    return init_rule


#
#
#

def set_demand_params(m, demand_params):
    """

    :param m: model
    :param demand_params:
    :return:
    """
    m.el_demand = pyo.Param(m.h_t,
                            initialize=df_init_wrapper(demand_params['el_demand']),
                            within=pyo.NonNegativeReals)
    m.th_demand = pyo.Param(m.h_t,
                            initialize=df_init_wrapper(demand_params['th_demand']),
                            within=pyo.NonNegativeReals)


def set_pv_params(m, pv_params):
    """
    :param m:
    :param pv_params:
    :return:
    """
    m.pv_production = pyo.Param(m.t,
                                initialize=array_init_wrapper(pv_params['pv_production']),
                                within=pyo.NonNegativeReals)
    m.pv_invest_cost = pyo.Param(initialize=pv_params['pv_invest_cost'],
                                 within=pyo.NonNegativeReals)
    m.max_pv_capacity = pyo.Param(initialize=pv_params['max_pv_capacity'],
                                  within=pyo.NonNegativeReals)


def set_power_market_params(m, power_market_params):
    """
    :param m:
    :param power_market_params:
    :param tariff_params:
    :return:
    """
    m.power_market_price = pyo.Param(m.t,
                                     initialize=array_init_wrapper(power_market_params['power_market_price']),
                                     within=pyo.Reals)

    m.tax = pyo.Param(initialize=power_market_params['tax'], within=pyo.NonNegativeReals)


def set_local_market_params(m, local_market_params):
    m.local_market_export_eta = local_market_params['export_eta']


def set_tariff_params(m, tariff_params):
    # Tariff volume cost per kW, indexed by hour [EUR/kW]
    m.volume_network_tariff = pyo.Param(m.t, initialize=tariff_params['volume_network_tariff'],
                                        within=pyo.NonNegativeReals)

    # Tariff volume cost of selling to the power market. Can be negative if selling is incentivized [EUR/kW]
    m.selling_volume_tariff = pyo.Param(initialize=tariff_params['selling_volume_tariff'])

    # What each house pays monthly [EUR]
    m.house_monthly_connection_base = pyo.Param(initialize=tariff_params['house_monthly_connection_base'],
                                                within=pyo.NonNegativeReals)

    # capacity tariff, based on individual peak each month [EUR/kW]
    m.peak_individual_monthly_power_tariff = pyo.Param(initialize=tariff_params['peak_individual_monthly_power_tariff'],
                                                       within=pyo.NonNegativeReals)

    # shared capacity tariff, based on aggregated peak each month [EUR/kW]
    m.peak_aggregated_monthly_power_tariff = pyo.Param(initialize=tariff_params['peak_aggregated_monthly_power_tariff'],
                                                       within=pyo.NonNegativeReals)


def set_house_hp_params(m, house_hp_params):
    m.house_hp_cop = pyo.Param(initialize=house_hp_params['cop'], within=pyo.NonNegativeReals)
    # Max delivered heat to all houses at once [kWh/h]
    m.house_hp_max_qw = pyo.Param(initialize=house_hp_params['max_qw'], within=pyo.NonNegativeReals)


def set_stes_params(m, stes_params):
    """

    :param m:
    :param STES_params:
    :return:
    """
    # Seasonal thermal energy storage
    m.stes_investment_cost = pyo.Param(initialize=stes_params['investment_cost'], within=pyo.NonNegativeReals)
    m.cap_investment_cost = pyo.Param(initialize=stes_params['cap_investment_cost'], within=pyo.NonNegativeReals)

    m.max_stes_capacity = pyo.Param(initialize=stes_params['max_installed_capacity'], within=pyo.NonNegativeReals)
    # m.stes_initial_soc = pyo.Param(initialize=stes_params['init_SOC'], within=pyo.NonNegativeReals)

    m.heat_retainment = pyo.Param(initialize=stes_params['heat_retainment'], within=pyo.NonNegativeReals)

    m.stes_charge_eta = pyo.Param(initialize=stes_params['charge_eta'], within=pyo.NonNegativeReals)
    m.stes_charge_hp_cop = pyo.Param(initialize=stes_params['charge_cop'], within=pyo.NonNegativeReals)
    m.stes_charge_hp_max_qw = pyo.Param(initialize=stes_params['charge_max_qw'], within=pyo.NonNegativeReals)

    m.stes_discharge_eta = pyo.Param(initialize=stes_params['discharge_eta'], within=pyo.NonNegativeReals)
    m.stes_discharge_hp_cop = pyo.Param(initialize=stes_params['discharge_cop'], within=pyo.NonNegativeReals)
    m.stes_discharge_hp_max_qw = pyo.Param(initialize=stes_params['discharge_max_qw'], within=pyo.NonNegativeReals)


def set_dso_params(m_dso, dso_params, net_use_params):
    # Existing transmission capacity [kW]
    m_dso.existing_transmission_capacity = pyo.Param(initialize=dso_params['existing_transmission_capacity'],
                                                     within=pyo.NonNegativeReals)

    # Annualized investment cost for additional grid capacity [EUR/kW/year]
    m_dso.grid_invest_cost = pyo.Param(initialize=dso_params['grid_invest_cost'], within=pyo.NonNegativeReals)

    # Transmission loss [%]
    m_dso.transmission_loss = pyo.Param(initialize=dso_params['transmission_loss'], within=pyo.NonNegativeReals)

    # Per house hourly grid import
    m_dso.grid_el_import = pyo.Param(m_dso.h_t,
                                     initialize=net_use_params['grid_el_import'],
                                     within=pyo.NonNegativeReals)
    # Per house hourly grid export
    m_dso.grid_export = pyo.Param(m_dso.h_t,
                                  initialize=net_use_params['grid_export'],
                                  within=pyo.NonNegativeReals)

