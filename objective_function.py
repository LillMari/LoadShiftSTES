# -*- coding: utf-8 -*-
"""
Created on Thu Jan 09 2024

@author: Lill Mari Engan
"""

import gurobipy as gp
from gurobipy import GRB


def total_lec_cost_rule(m):
    m.objective_terms = {}

    # PV investment cost (annualized)
    m.objective_terms['pv_investment_cost'] = m.pv_invest_cost * sum(m.pv_installed_capacity[h] for h in m.h)

    # Power market cost (spot price)
    m.objective_terms['power_market_cost'] = sum(m.power_market_price[t] * (m.grid_import[t, h] - m.grid_export[t, h])
                                                 for t in m.t for h in m.h)

    # Electricity tax cost
    m.objective_terms['volume_tax_cost'] = sum(m.tax[t] * (m.grid_import[t, h] + m.local_import[t, h])
                                               for t in m.t for h in m.h)

    # Volumetric grid tariff on power market import, excluding taxes
    grid_volume_import_tariff = sum(m.grid_import[t, h] * m.volume_network_tariff[t] for t in m.t for h in m.h)

    # Volumetric grid tariff on power market export
    grid_volume_export_tariff = sum(m.grid_export[t, h] * m.selling_volume_tariff for t in m.t for h in m.h)

    m.objective_terms['grid_volume_tariff'] = grid_volume_import_tariff + grid_volume_export_tariff

    # Monthly connection base tariff
    connection_cost = m.house_monthly_connection_base * len(m.h) * 12

    # Monthly individual capacity tariff
    individual_capacity_tariff = sum(m.peak_monthly_house_volume[h, month] for h in m.h for month in m.months) \
        * m.peak_individual_monthly_power_tariff

    # Monthly aggregated capacity tariff
    aggregated_capacity_tariff = sum(m.peak_monthly_total_volume[month] for month in m.months) \
        * m.peak_aggregated_monthly_power_tariff

    m.objective_terms['capacity_tariff'] = connection_cost + individual_capacity_tariff + aggregated_capacity_tariff

    # STES investment cost
    m.objective_terms['stes_investment_cost'] = m.stes_capacity * m.cap_investment_cost + m.stes_investment_cost

    return sum(m.objective_terms.values())


def total_cost_objective_function(m):
    m.lec_objective = m.model.setObjective(total_lec_cost_rule(m), GRB.MINIMIZE)
