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

    m.lm_price = pyo.Var(m.t, within=pyo.NonNegativeReals)  # Local market prices [EUR/kWh]
    m.peak_grid_volume = pyo.Var(m.h, within=pyo.NonNegativeReals)  # Highest grid value, either import or export [kWh/h]


def stes_vars(m):
    """
    :param m:
    :return:
    """
    pass
    # m.stes_soc = pyo.Var(m.t, within=pyo.NonNegativeReals)
    # m.stes_pv_charge = pyo.Var(m.t, within=pyo.NonNegativeReals)
    # m.stes_grid_charge = pyo.Var(m.t, within=pyo.NonNegativeReals)
    # m.stes_discharge = pyo.Var(m.t, within=pyo.NonNegativeReals)


def hp_vars(m):
    # Kan bakes inn i andre variabler?
    pass


def dso_vars(m_dso):
    # additional peak capacity being built [kW]
    m_dso.grid_capacity_investment = pyo.Var(within=pyo.NonNegativeReals)

    m_dso.grid_power_volume = pyo.Var(m_dso.t, within=pyo.NonNegativeReals)

    # Purely derived variables
    m_dso.grid_capacity_cost = pyo.Var(within=pyo.NonNegativeReals)
    m_dso.grid_loss_cost = pyo.Var(within=pyo.NonNegativeReals)
