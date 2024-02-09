# -*- coding: utf-8 -*-
"""
Created on Thu Jan 09 2024

@author: Lill Mari Engan
"""

import pyomo.environ as pyo


def total_lec_cost_rule(m):
    m.objective_terms = {}

    # PV investment cost (annualized)
    m.objective_terms['pv_investment_cost'] = m.pv_invest_cost * sum(m.pv_installed_capacity[h] for h in m.h)

    # Power market cost
    m.objective_terms['power_cost'] = sum(m.power_market_price[t] * (m.grid_import[h, t] - m.grid_export[h, t])
                                          for h, t in m.h_t)

    # Electricity tax cost
    # TODO: Fjerne skatt på local_import?
    m.objective_terms['tax_cost'] = sum(m.tax * (m.grid_import[h, t] + m.local_import[h, t]) for h, t in m.h_t)

    # Volumetric grid tariff on power market import
    m.objective_terms['grid_import_cost'] = sum(m.grid_import[h, t] * m.volume_network_tariff[t] for h, t in m.h_t)

    # Volumetric grid tariff on power market export
    m.objective_terms['grid_export_cost'] = sum(m.grid_export[h, t] * m.selling_volume_tariff for h, t in m.h_t)

    # Monthly connection base tariff
    m.objective_terms['connection_cost'] = m.house_monthly_connection_base * len(m.h) * 12

    # Monthly individual capacity tariff
    m.objective_terms['individual_capacity_tariff'] = sum(m.peak_monthly_house_volume[h, month] for h in m.h for month
                                                          in m.months) * m.peak_individual_monthly_power_tariff

    # Monthly aggregated capacity tariff
    m.objective_terms['aggregated_capacity_tariff'] = sum(m.peak_monthly_total_volume[month] for month in m.months) \
        * m.peak_aggregated_monthly_power_tariff

    # STES investment cost
    m.objective_terms['stes_investment_cost'] = m.stes_capacity * m.cap_investment_cost + m.stes_investment_cost

    return sum(m.objective_terms.values())


def total_cost_objective_function(m):
    m.lec_objective = pyo.Objective(rule=total_lec_cost_rule, sense=pyo.minimize)
