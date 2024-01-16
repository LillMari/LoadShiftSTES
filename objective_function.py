# -*- coding: utf-8 -*-
"""
Created on Thu Jan 09 2024

@author: Lill Mari Engan
"""

import pyomo.environ as pyo
import pandas as pd


def total_lec_cost_rule(m):
    # Investment cost
    investment_cost = m.pv_invest_cost * sum(m.pv_installed_capacity[h] for h in m.h)

    # Power market cost
    power_cost = sum(m.power_market_price[t] * (m.grid_el_import[h, t] - m.grid_export[h, t]) for h, t in m.h_t)

    # Local market cost
    lm_cost = sum(m.lm_price[t] * (m.local_import[h, t] - m.local_export[h, t]) for h, t in m.h_t)

    # Electricity tax cost
    tax_cost = sum(m.tax * (m.grid_el_import[h, t] + m.local_import[h, t]) for h, t in m.h_t)

    # Grid charges
    grid_charge_cost = sum((m.grid_el_import[h, t] - m.NM * m.grid_export[h, t]) * m.vnt + m.peak_grid_volume[h] * m.cnt for h, t in m.h_t)

    return investment_cost + power_cost + lm_cost + tax_cost + grid_charge_cost


def total_cost_objective_function(m):
    m.lec_objective = pyo.Objective(rule=total_lec_cost_rule, sense=pyo.minimize)


def dso_cost_rule(m_dso):
    return m_dso.grid_capacity_cost + m_dso.grid_loss_cost


def dso_objective_function(m):
    m.dso_objective = pyo.Objective(rule=dso_cost_rule, sense=pyo.minimize)

