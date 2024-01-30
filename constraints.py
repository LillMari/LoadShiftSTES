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
    The electric demand is covered by the grid, the local market and by its own PV system
    """
    el_load = m.el_demand[h, t] + m.electric_heating[h, t] + \
              m.house_hp_qw[h, t] / m.house_hp_cop + \
              m.stes_charge_hp_qw[h, t] / m.stes_charge_hp_cop + \
              m.stes_discharge_hp_qw[h, t] / m.stes_discharge_hp_cop
    return el_load == m.grid_import[h, t] - m.grid_export[h, t] + m.local_import[h, t] - m.local_export[h, t] + \
        m.pv_production[t] * m.pv_installed_capacity[h]


def thermal_energy_rule(m, h, t):
    return m.electric_heating[h, t] + m.house_hp_qw[h, t] + m.stes_discharge_hp_qw[h, t] == m.th_demand[h, t]


def house_hp_max_heating_rule(m, h, t):
    return m.house_hp_qw[h, t] <= m.house_hp_max_qw


def peak_monthly_house_volume_rule(m, h, t, sign):
    month = m.month_from_hour[t]
    total_consume = m.grid_import[h, t] - m.grid_export[h, t]
    return sign * total_consume <= m.peak_monthly_house_volume[h, month]


def peak_monthly_total_volume_rule(m, t, sign):
    month = m.month_from_hour[t]
    total_consume = sum(m.grid_import[h, t] - m.grid_export[h, t] for h in m.h)
    return sign * total_consume <= m.peak_monthly_total_volume[month]


def pv_curtailment_rule(m, h, t):
    return


def local_market_rule(m, t):
    return sum(m.local_import[h, t] - m.local_export[h, t] for h in m.h) == 0


def stes_discharging_rule(m):
    discharging_months = [0, 1, 10, 11]  # STES can only deliver thermal energy during
                                         # winter due to system inertia
    return sum(m.stes_discharge_hp_qw[h, t] for h, t in m.h_t
               if m.month_from_hour[t] not in discharging_months) == 0


def stes_charging_rule(m):
    discharging_months = [0, 1, 10, 11]  # STES can only deliver thermal energy during
                                         # winter due to system inertia
    return sum(m.stes_charge_hp_qw[h, t] for h, t in m.h_t
               if m.month_from_hour[t] in discharging_months) == 0


def stes_max_charging_rule(m, t):
    # All houses in total can max deliver this amount of heat into the STES
    return sum(m.stes_charge_hp_qw[h, t] for h in m.h) <= m.stes_charge_hp_max_qw


def stes_max_discharging_rule(m, t):
    # All houses in total can max get this much heat of the STES
    return sum(m.stes_discharge_hp_qw[h, t] for h in m.h) <= m.stes_discharge_hp_max_qw


def stes_max_soc_rule(m, t):
    return m.stes_soc[t] <= m.stes_capacity


def stes_soc_evolution_rule(m, t):
    if t > 0:
        last_hour = m.stes_soc[t - 1]
    else:
        last_hour = m.stes_soc[m.t.at(-1)]

    charge_factor = m.stes_charge_eta
    discharge_factor = (1 - 1 / m.stes_discharge_hp_cop) / m.stes_discharge_eta

    return m.stes_soc[t] == last_hour * m.heat_retainment + \
        sum(m.stes_charge_hp_qw[h, t] * charge_factor - m.stes_discharge_hp_qw[h, t] * discharge_factor for h in m.h)


def lec_constraints(m):
    m.electric_energy_constraint = pyo.Constraint(m.h_t, rule=electric_energy_rule)
    m.thermal_energy_constraint = pyo.Constraint(m.h_t, rule=thermal_energy_rule)
    m.house_hp_max_heating_constraint = pyo.Constraint(m.h_t, rule=house_hp_max_heating_rule)

    m.peak_monthly_house_volume_constraint = pyo.Constraint(m.h_t, m.sign, rule=peak_monthly_house_volume_rule)
    m.peak_monthly_total_volume_constraint = pyo.Constraint(m.t, m.sign, rule=peak_monthly_total_volume_rule)

    m.local_market_constraint = pyo.Constraint(m.t, rule=local_market_rule)

    # STES constraints
    m.stes_discharging_constraint = pyo.Constraint(rule=stes_discharging_rule)
    m.stes_charging_constraint = pyo.Constraint(rule=stes_charging_rule)
    m.stes_max_charging_constraint = pyo.Constraint(m.t, rule=stes_max_charging_rule)
    m.stes_max_discharging_constraint = pyo.Constraint(m.t, rule=stes_max_discharging_rule)
    m.stes_max_soc_constraint = pyo.Constraint(m.t, rule=stes_max_soc_rule)
    m.stes_soc_evolution_constraint = pyo.Constraint(m.t, rule=stes_soc_evolution_rule)


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
    m_dso.power_volume_constraint = pyo.Constraint(m_dso.t * m_dso.sign, rule=grid_power_volume_rule)
    m_dso.grid_capacity_constraint = pyo.Constraint(m_dso.t, rule=grid_capacity_rule)

    # Calculates derived variables
    m_dso.grid_capacity_cost_constraint = pyo.Constraint(rule=grid_capacity_cost_rule)
    m_dso.grid_volume_cost_constraint = pyo.Constraint(rule=grid_volume_cost_rule)
