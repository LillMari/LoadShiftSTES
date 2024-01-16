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


"""
PARAMETERS
Spot price: Cost of 
Load: Costumer load (per household)
PV production: PV production (per household)
"""
# Antar forbruk ikke blir slått sammen med produksjon, hvis ikke kan den også ta negative verdier


def set_prosumer_params(m, prosumer_params):
    """

    :param m: model
    :param prosumer_params:
    :return:
    """
    m.el_load = pyo.Param(m.h_t,
                          initialize=df_init_wrapper(prosumer_params['el_load']),
                          within=pyo.NonNegativeReals)
    m.th_load = pyo.Param(m.h_t,
                          initialize=df_init_wrapper(prosumer_params['thermal_load']),
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
    m.NM = pyo.Param(initialize=power_market_params['NM'], within=pyo.NonNegativeReals)  # Net metering coefficient


def set_tariff_params(m, tariff_params):
    m.vnt = pyo.Param(initialize=tariff_params['vnt'],
                      within=pyo.NonNegativeReals)  # Volumetric network tariff [EUR/kWh]
    m.cnt = pyo.Param(initialize=tariff_params['cnt'],
                      within=pyo.NonNegativeReals)  # Capacity-based network tariff [EUR/kW]


def set_hp_params(m, hp_params):
    """
    :param m:
    :param hp_params:
    :return:
    """
    # m.hp_cop = pyo.Param(initialize=init_cop, within=pyo.NonNegativeReals)


def set_STES_params(m, stes_params):
    """

    :param m:
    :param STES_params:
    :return:
    """
    # Seasonal thermal energy storage
    m.investment_cost = pyo.Param(initialize=stes_params['investment_cost'], within=pyo.NonNegativeReals)
    m.cap_investment_cost = pyo.Param(initialize=stes_params['cap_investment_cost'], within=pyo.NonNegativeReals)

    m.STES_capacity = pyo.Param(initialize=stes_params['installed_capacity'], within=pyo.NonNegativeReals)
    m.STES_initial_SOC = pyo.Param(initialize=stes_params['init_SOC'], within=pyo.NonNegativeReals)

    m.STES_max_charge = pyo.Param(initialize=stes_params['max_charge'], within=pyo.NonNegativeReals)
    m.STES_max_discharge = pyo.Param(initialize=stes_params['max_discharge'], within=pyo.NonNegativeReals)

    m.eta_charge = pyo.Param(initialize=stes_params['eta_charge'], within=pyo.NonNegativeReals)
    m.eta_discharge = pyo.Param(initialize=stes_params['eta_discharge'], within=pyo.NonNegativeReals)
    m.heat_loss = pyo.Param(initialize=stes_params['heat_loss'], within=pyo.NonNegativeReals)


def set_dso_params(m_dso, dso_params, net_use_params):
    # Existing transmission capacity [kW]
    m_dso.existing_transmission_capacity = pyo.Param(initialize=dso_params['existing_transmission_capacity'],
                                                     within=pyo.NonNegativeReals)

    # Annualized investment cost for additional grid capacity [EUR/kW/year]
    m_dso.grid_invest_cost = pyo.Param(initialize=dso_params['grid_invest_cost'], within=pyo.NonNegativeReals)

    # Transmission loss [%]
    m_dso.transmission_loss = pyo.Param(initialize=dso_params['transmission_loss'], within=pyo.NonNegativeReals)

    # Per house hourly grid import
    m_dso.grid_import = pyo.Param(m_dso.h_t,
                                  initialize=net_use_params['grid_import'],
                                  within=pyo.NonNegativeReals)
    # Per house hourly grid export
    m_dso.grid_export = pyo.Param(m_dso.h_t,
                                  initialize=net_use_params['grid_export'],
                                  within=pyo.NonNegativeReals)

