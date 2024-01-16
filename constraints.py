# -*- coding: utf-8 -*-
"""
Created on Thu Jan 09 2024

@author: Lill Mari Engan
"""

import pyomo.environ as pyo
import pandas as pd


# =======================
#     LEC constraints
# =======================

def electric_energy_rule(m, h, t):
    """
    The sum of used and exported energy must be equal to the sum of
    imported and generated energy for each household.
    """
    el_load = m.el_load[h, t] + \
        m.electric_heating[h, t] + \
        m.hp_air_to_floor_heating[h, t] / m.hp_air_to_floor_cop

    return m.pv_production[h, t] + m.grid_el_import[h, t] == el_load + m.grid_export[h, t]


#  TODO: alle reglene her må ordnes ordentlig !!

def thermal_energy_rule(m, h, t):
    heat_production = m.electric_heating[h, t] + m.hp_air_to_floor_heating[h, t]
    return heat_production == m.th_load[h, t]


def hp_air_to_floor_max_heating_rule(m, h, t):
    return m.hp_air_to_floor_heating[h, t] <= m.hp_air_to_floor_max_heating[h]


def pv_rule(m, h, t):
    return m.pv_production[t] * m.pv_installed_capacity[h] == m.pv_th_production[h, t] + m.pv_el_production[h, t]


def peak_grid_volume_rule(m, h, t):
    """
    peak_grid_volume[h] tracks the maximum usage of the grid
    """
    return m.grid_el_import[h, t] + m.grid_th_import[h, t] + m.grid_export[h, t] <= m.peak_grid_volume[h]


def max_pv_capacity_rule(m, h):
    return m.pv_installed_capacity[h] <= m.max_pv_capacity


def pv_curtailment_rule(m, h, t):
    return


def local_market_rule(m, t):
    return sum(m.local_import[h, t] - m.local_export[h, t] for h in m.h) == 0


def stes_max_charging_rule(m, t):
    return m.stes_grid_charge[t] + m.stes_pv_charge[t] <= m.STES_max_charge


def stes_discharging_rule(m, t):
    return m.stes_discharge[t] <= m.STES_max_discharge


def stes_max_soc_rule(m, t):
    return m.stes_soc[t] <= m.STES_capacity


def stes_soc_evolution_rule(m, t):
    return m.stes_soc[t] == m.stes_soc[t-1] + \
           (m.stes_grid_charge[t] + m.stes_pv_charge) * m.eta_charge - m.stes_discharge[t] / m.eta_discharge


def lec_constraints(m):
    m.electric_energy_constraint = pyo.Constraint(m.h_t, rule=electric_energy_rule)
    m.peak_load_constraint = pyo.Constraint(m.h_t, rule=peak_grid_volume_rule)
    m.max_pv_capacity_constraint = pyo.Constraint(m.h, rule=max_pv_capacity_rule)
    # m.local_market_rule = pyo.Constraint(m.t, rule=local_market_rule)


# =======================
#     DSO constraints
# =======================

def grid_power_volume_rule(m_dso, t, sign):
    net_import = sum(m_dso.grid_el_import[h, t] - m_dso.grid_export[h, t] for h in m_dso.h)
    net_import = net_import * sign

    return m_dso.grid_power_volume[t] >= net_import


def grid_capacity_rule(m_dso, t):
    return m_dso.existing_transmission_capacity + m_dso.grid_capacity_investment >= m_dso.grid_power_volume[t]


def grid_capacity_cost_rule(m_dso):
    return m_dso.grid_capacity_cost == m_dso.grid_invest_cost * m_dso.grid_capacity_investment


def grid_volume_cost_rule(m_dso):
    return m_dso.grid_loss_cost == \
        sum(m_dso.grid_power_volume[t] * m_dso.transmission_loss * m_dso.power_market_price[t] for t in m_dso.t)


def dso_constraints(m_dso):
    m_dso.sign_set = pyo.Set(initialize=[1, -1])
    m_dso.power_volume_constraint = pyo.Constraint(m_dso.t * m_dso.sign_set, rule=grid_power_volume_rule)
    m_dso.grid_capacity_constraint = pyo.Constraint(m_dso.t, rule=grid_capacity_rule)

    # Calculates derived variables
    m_dso.grid_capacity_cost_constraint = pyo.Constraint(rule=grid_capacity_cost_rule)
    m_dso.grid_volume_cost_constraint = pyo.Constraint(rule=grid_volume_cost_rule)
