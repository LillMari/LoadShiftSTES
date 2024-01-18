# -*- coding: utf-8 -*-
"""
Created on Thu Jan 09 2024

@author: Lill Mari Engan
"""

import pyomo.environ as pyo
import pandas as pd


"""
VARIABLES
"""


def pv_vars(m):
    # TODO: legge til max og min på installert effekt (og curtailment option?)
    """
    :param m:
    :return:
    """
    m.pv_installed_capacity = pyo.Var(m.h, within=pyo.NonNegativeReals)


def grid_vars(m):
    """
    :param m:
    :return:
    """
    # Power from and to power market
    m.grid_import = pyo.Var(m.h_t, within=pyo.NonNegativeReals)  # [kWh/h]
    m.grid_export = pyo.Var(m.h_t, within=pyo.NonNegativeReals)  # [kWh/h]

    # Local market
    m.local_import = pyo.Var(m.h_t, within=pyo.NonNegativeReals)  # [kWh/h]
    m.local_export = pyo.Var(m.h_t, within=pyo.NonNegativeReals)  # [kWh/h]

    m.peak_grid_volume = pyo.Var(within=pyo.NonNegativeReals)  # [kWh/h] max netto grid volume, either import or export


def stes_vars(m):
    """
    :param m:
    :return:
    """
    m.stes_soc = pyo.Var(m.t, within=pyo.NonNegativeReals)
    m.stes_pv_charge = pyo.Var(m.t, within=pyo.NonNegativeReals)
    m.stes_grid_charge = pyo.Var(m.t, within=pyo.NonNegativeReals)
    m.stes_discharge = pyo.Var(m.t, within=pyo.NonNegativeReals)
    m.stes_capacity = pyo.Var(within=pyo.NonNegativeReals)


def heating_vars(m):
    # A 1:1 conversion from electric energy to heat. No upper bound, but least efficient method
    m.electric_heating = pyo.Var(m.h_t, within=pyo.NonNegativeReals)  # [kWh] of heat energy

    # A more efficient way of heating houses, still using electricity.
    # Upper bounded by hp_air_to_floor_max_heating
    m.hp_air_to_floor_heating = pyo.Var(m.h_t, within=pyo.NonNegativeReals)  # [kWh] of heat energy


def dso_vars(m_dso):
    # additional peak capacity being built [kW]
    m_dso.grid_capacity_investment = pyo.Var(within=pyo.NonNegativeReals)

    m_dso.grid_power_volume = pyo.Var(m_dso.t, within=pyo.NonNegativeReals)

    # Purely derived variables
    m_dso.grid_capacity_cost = pyo.Var(within=pyo.NonNegativeReals)
    m_dso.grid_loss_cost = pyo.Var(within=pyo.NonNegativeReals)
