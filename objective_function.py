# -*- coding: utf-8 -*-
"""
Created on Thu Jan 09 2024

@author: Lill Mari Engan
"""

import pyomo.environ as pyo


def total_lec_cost_rule(m):
    # PV investment cost (annualized)
    pv_investment_cost = m.pv_invest_cost * sum(m.pv_installed_capacity[h] for h in m.h)

    # Power market cost
    power_cost = sum(m.power_market_price[t] * (m.grid_import[h, t] - m.grid_export[h, t]) for h, t in m.h_t)

    # Electricity tax cost
    tax_cost = sum(m.tax * (m.grid_import[h, t] + m.local_import[h, t]) for h, t in m.h_t)

    # Volumetric grid charges
    grid_volume_cost = sum((m.grid_import[h, t] - m.NM * m.grid_export[h, t]
                            + m.local_import[h, t] - m.NM * m.local_export[h, t]) *
                           m.volume_network_tariff[t] for h, t in m.h_t)

    # Monthly capacity cost for each household
    grid_capacity_cost = sum(m.peak_monthly_volume[h, month] for h in m.h for month in m.months) * \
        m.peak_capacity_tariff + 12 * len(m.h) * m.capacity_tariff_base

    # TODO: Elvia's -5 øre per kWh exported

    # STES investment cost
    if m.enable_stes:
        stes_investment_cost = m.stes_capacity * m.cap_investment_cost + m.stes_investment_cost
    else:
        stes_investment_cost = 0

    return pv_investment_cost + power_cost + tax_cost + grid_volume_cost + grid_capacity_cost + stes_investment_cost


def total_cost_objective_function(m):
    m.lec_objective = pyo.Objective(rule=total_lec_cost_rule, sense=pyo.minimize)
