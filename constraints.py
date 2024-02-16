# -*- coding: utf-8 -*-
"""
Created on Thu Jan 09 2024

@author: Lill Mari Engan
"""

import gurobipy as gp
from gurobipy import GRB


def electric_energy_rule(m, t, h):
    """
    The electric demand is covered by the grid, the local market and by its own PV system
    """
    el_load = m.el_demand[t, h] + m.electric_heating[t, h] + \
              m.house_hp_qw[t, h] / m.house_hp_cop + \
              m.stes_charge_hp_qw[t, h] / m.stes_charge_hp_cop + \
              m.stes_discharge_hp_qw[t, h] / m.stes_discharge_hp_cop
    return el_load == m.grid_import[t, h] - m.grid_export[t, h] + m.local_import[t, h] - m.local_export[t, h] + \
        m.pv_production[t] * m.pv_installed_capacity[h]


def thermal_energy_rule(m, t, h):
    return m.electric_heating[t, h] + m.house_hp_qw[t, h] + m.stes_discharge_hp_qw[t, h] == m.th_demand[t, h]


def peak_monthly_individual_volume_rule(m, t, h, sign):
    """ Rule tracking the peak hour of grid volume per household, each month """
    month = m.month_from_hour[t]
    total_consume = m.grid_import[t, h] - m.grid_export[t, h]
    return sign * total_consume <= m.peak_monthly_house_volume[h, month]


def peak_monthly_aggregated_volume_rule(m, t, sign):
    """ Rule tracking the peak hour of total grid volume, each month """
    month = m.month_from_hour[t]
    total_consume = sum(m.grid_import[t, h] - m.grid_export[t, h] for h in m.h)
    return sign * total_consume <= m.peak_monthly_total_volume[month]


def pv_curtailment_rule(m, t, h):
    return


def local_market_rule(m, t):
    return sum(m.local_import[t, h] - m.local_export[t, h] * m.local_market_export_eta for h in m.h) == 0


# STES can only deliver thermal energy during winter due to system inertia
DISCHARGING_MONTHS = [0, 1, 10, 11]


def stes_discharging_rule(m):
    return sum(m.stes_discharge_hp_qw[t, h] for h in m.h for t in m.t
               if m.month_from_hour[t] not in DISCHARGING_MONTHS) == 0


def stes_charging_rule(m):
    return sum(m.stes_charge_hp_qw[t, h] for h in m.h for t in m.t
               if m.month_from_hour[t] in DISCHARGING_MONTHS) == 0


def stes_max_charging_rule(m, t):
    # All houses in total can max deliver this amount of heat into the STES
    return sum(m.stes_charge_hp_qw[t, h] for h in m.h) <= m.stes_charge_hp_max_qw


def stes_max_discharging_rule(m, t):
    # All houses in total can max get this much heat of the STES
    return sum(m.stes_discharge_hp_qw[t, h] for h in m.h) <= m.stes_discharge_hp_max_qw


def stes_max_soc_rule(m, t):
    return m.stes_soc[t] <= m.stes_capacity


def stes_soc_evolution_rule(m, t):
    if t > 0:
        last_hour = m.stes_soc[t - 1]
    else:
        last_hour = m.stes_soc[m.t[-1]]

    charge_factor = m.stes_charge_eta
    discharge_factor = (1 - 1 / m.stes_discharge_hp_cop) / m.stes_discharge_eta

    return m.stes_soc[t] == last_hour * m.heat_retainment + \
        sum(m.stes_charge_hp_qw[t, h] * charge_factor - m.stes_discharge_hp_qw[t, h] * discharge_factor for h in m.h)


def lec_constraints(m):
    m.model.addConstrs((electric_energy_rule(m, t, h) for t in m.t for h in m.h), name="electric_energy_constraint")
    m.model.addConstrs((thermal_energy_rule(m, t, h) for t in m.t for h in m.h), name="thermal_energy_constraint")

    m.model.addConstrs((peak_monthly_individual_volume_rule(m, t, h, s) for t in m.t for h in m.h for s in m.sign),
                       name="peak_monthly_house_volume_constraint")
    m.model.addConstrs((peak_monthly_aggregated_volume_rule(m, t, s) for t in m.t for s in m.sign),
                       name="peak_monthly_total_volume_constraint")

    m.model.addConstrs((local_market_rule(m, t) for t in m.t), name="local_market_constraint")

    # STES constraints
    m.model.addConstr(stes_discharging_rule(m), name="stes_discharging_constraint")
    m.model.addConstr(stes_charging_rule(m), name="stes_charging_constraint")
    m.model.addConstrs((stes_max_charging_rule(m, t) for t in m.t), name="stes_max_charging_constraint")
    m.model.addConstrs((stes_max_discharging_rule(m, t) for t in m.t), name="stes_max_discharging_constraint")
    m.model.addConstrs((stes_max_soc_rule(m, t) for t in m.t), name="stes_max_soc_constraint")
    m.model.addConstrs((stes_soc_evolution_rule(m, t) for t in m.t), name="stes_soc_evolution_constraint")


"""
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
"""