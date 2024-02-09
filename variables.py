# -*- coding: utf-8 -*-
"""
Created on Thu Jan 09 2024

@author: Lill Mari Engan
"""

import pyomo.environ as pyo
import pandas as pd


def pv_vars(m):
    # How much PV is installed on each house
    m.pv_installed_capacity = pyo.Var(m.h, within=pyo.NonNegativeReals, bounds=(0, m.max_pv_capacity))  # [kWp]


def grid_vars(m):
    # Power from and to power market
    m.grid_import = pyo.Var(m.h_t, within=pyo.NonNegativeReals)  # [kWh/h]
    m.grid_export = pyo.Var(m.h_t, within=pyo.NonNegativeReals)  # [kWh/h]

    # Local market
    if m.enable_local_market:
        bounds = (0, None)
    else:
        bounds = (0, 0)
    m.local_import = pyo.Var(m.h_t, within=pyo.NonNegativeReals, bounds=bounds)  # [kWh/h]
    m.local_export = pyo.Var(m.h_t, within=pyo.NonNegativeReals, bounds=bounds)  # [kWh/h]

    # For each household, and each month, its highest hourly electric consumption or production
    m.peak_monthly_house_volume = pyo.Var(m.h, m.months, within=pyo.NonNegativeReals)  # [kWh/h]

    # For each month, the highest hourly electric volume into or leaving the neighbourhood
    m.peak_monthly_total_volume = pyo.Var(m.months, within=pyo.NonNegativeReals)  # [kWh/h]


def stes_vars(m):
    m.stes_capacity = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, m.max_stes_capacity))
    m.stes_soc = pyo.Var(m.t, within=pyo.NonNegativeReals)

    # Heating up the STES
    m.stes_charge_hp_qw = pyo.Var(m.h_t, within=pyo.NonNegativeReals)  # [kWh] of heat energy

    # Heating houses from the STES
    m.stes_discharge_hp_qw = pyo.Var(m.h_t, within=pyo.NonNegativeReals)  # [kWh] of heat energy


def heating_vars(m):
    # A 1:1 conversion from electric energy to heat. No upper bound, but least efficient method
    m.electric_heating = pyo.Var(m.h_t, within=pyo.NonNegativeReals)  # [kWh] of heat energy

    # A more efficient way of heating houses, still using electricity.
    # Upper bounded by house_hp_max_wq
    m.house_hp_qw = pyo.Var(m.h_t, within=pyo.NonNegativeReals)  # [kWh] of heat energy


def dso_vars(m_dso):
    pass
    """
    # additional peak capacity being built [kW]
    m_dso.grid_capacity_investment = pyo.Var(within=pyo.NonNegativeReals)

    m_dso.grid_power_volume = pyo.Var(m_dso.t, within=pyo.NonNegativeReals)

    # Purely derived variables
    m_dso.grid_capacity_cost = pyo.Var(within=pyo.NonNegativeReals)
    m_dso.grid_loss_cost = pyo.Var(within=pyo.NonNegativeReals)
    """
