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
    el_load = m.el_demand[t, h] + m.electric_heating[t, h] + m.house_hp_qw[t, h] / m.house_hp_cop + m.stes_el[t, h]

    return el_load == m.grid_import[t, h] - m.grid_export[t, h] + m.local_import[t, h] - m.local_export[t, h] + \
        m.pv_production[t] * m.pv_installed_capacity[h]


def thermal_energy_rule(m, t, h):
    return m.electric_heating[t, h] + m.house_hp_qw[t, h] + m.stes_th[t, h] == m.th_demand[t, h]


def peak_monthly_individual_volume_rule(m, t, h, sign):
    """ Rule tracking the peak hour of grid volume per household, each month """
    month = m.month_from_hour[t]
    total_consume = m.grid_import[t, h] - m.grid_export[t, h]
    return sign * total_consume <= m.peak_monthly_house_volume[h, month]


def peak_monthly_aggregated_volume_rule(m, t, sign):
    """ Rule tracking the peak hour of total grid volume, each month """
    month = m.month_from_hour[t]
    total_consume = sum(m.grid_import[t, h] - m.grid_export[t, h] for h in m.h)
    if sign > 0:
        return total_consume <= m.peak_aggregated_monthly_import_volume[month]
    else:
        return -total_consume <= m.peak_aggregated_monthly_export_volume[month]


def local_market_rule(m, t):
    return sum(m.local_import[t, h] - m.local_export[t, h] * m.local_market_export_eta for h in m.h) == 0


def house_hp_max_qw_rule(m, t, h):
    return m.house_hp_qw[t, h] <= m.house_hp_installed_capacity[h]


def stes_el_rule(m, t):
    source = sum(m.stes_el[t, h] for h in m.h)
    sink = m.hp_qw[t] / m.stes_hp_cop + m.stes_discharge_qc[t] / (m.stes_discharge_cop - 1)
    return source == sink


def stes_hp_max_qw_rule(m, t):
    return m.hp_qw[t] <= m.hp_max_qw


def stes_hp_qw_usage_rule(m, t):
    return m.hp_qw[t] == m.stes_charge_qw[t] + m.hp_direct_qw[t]


def stes_th_rule(m, t):
    source = m.hp_direct_qw[t] + m.stes_discharge_qc[t] / (1 - 1/m.stes_discharge_cop)
    sink = sum(m.stes_th[t, h] for h in m.h)
    return source == sink


def stes_soc_evolution_rule(m, t):
    if t > 0:
        last_hour = m.stes_soc[t - 1]
    else:
        last_hour = m.stes_soc[m.t[-1]]

    return m.stes_soc[t] == last_hour * m.heat_retainment + \
        m.stes_charge_qw[t] * m.stes_charge_eta - m.stes_discharge_qc[t] / m.stes_discharge_eta


def stes_charging_rule(m, t):
    energy_in = m.stes_charge_qw[t] * m.stes_charge_eta
    energy_max = m.volumetric_heat_capacity * m.max_temperature_increase * m.stes_volume
    return energy_in <= energy_max


def stes_charging_cutoff_rule(m, t):
    energy_in = m.stes_charge_qw[t] * m.stes_charge_eta
    temp_volume = m.ground_base_temperature * m.stes_volume + m.stes_soc[t] / m.volumetric_heat_capacity
    A = m.volumetric_heat_capacity * m.max_temperature_increase / (m.max_stes_temperature - m.charge_threshold)
    B = A * m.max_stes_temperature * m.stes_volume
    energy_max = -A * temp_volume + B
    return energy_in <= energy_max


def stes_discharging_rule(m, t):
    energy_out = m.stes_discharge_qc[t] / m.stes_discharge_eta
    energy_max = m.volumetric_heat_capacity * m.max_temperature_decrease * m.stes_volume
    return energy_out <= energy_max


def stes_discharging_cutoff_rule(m, t):
    energy_out = m.stes_discharge_qc[t] / m.stes_discharge_eta
    temp_volume = m.ground_base_temperature * m.stes_volume + m.stes_soc[t] / m.volumetric_heat_capacity
    A = m.volumetric_heat_capacity * m.max_temperature_decrease / (m.discharge_threshold - m.min_stes_temperature)
    B = -A * m.min_stes_temperature * m.stes_volume
    energy_max = A * temp_volume + B
    return energy_out <= energy_max


def lec_constraints(m):
    m.model.addConstrs((electric_energy_rule(m, t, h) for t in m.t for h in m.h), name="electric_energy_constraint")
    m.model.addConstrs((thermal_energy_rule(m, t, h) for t in m.t for h in m.h), name="thermal_energy_constraint")

    m.model.addConstrs((peak_monthly_individual_volume_rule(m, t, h, s) for t in m.t for h in m.h for s in m.sign),
                       name="peak_monthly_house_volume_constraint")
    m.model.addConstrs((peak_monthly_aggregated_volume_rule(m, t, s) for t in m.t for s in m.sign),
                       name="peak_monthly_total_volume_constraint")

    m.model.addConstrs((local_market_rule(m, t) for t in m.t), name="local_market_constraint")

    # House hp constraint
    m.model.addConstrs((house_hp_max_qw_rule(m, t, h) for t in m.t for h in m.h), name="house_hp_max_qw_constraint")

    # STES constraints
    m.model.addConstrs((stes_el_rule(m, t) for t in m.t), name="stes_el_constraint")
    m.model.addConstrs((stes_hp_max_qw_rule(m, t) for t in m.t), name="stes_hp_max_qw_constraint")
    m.model.addConstrs((stes_hp_qw_usage_rule(m, t) for t in m.t), name="stes_hp_qw_usage_constraint")
    m.model.addConstrs((stes_th_rule(m, t) for t in m.t), name="stes_th_constraint")
    m.model.addConstrs((stes_soc_evolution_rule(m, t) for t in m.t), name="stes_soc_evolution_constraint")
    m.model.addConstrs((stes_charging_rule(m, t) for t in m.t), name="stes_charging_constraint")
    m.model.addConstrs((stes_charging_cutoff_rule(m, t) for t in m.t), name="stes_charging_cutoff_constraint")
    m.model.addConstrs((stes_discharging_rule(m, t) for t in m.t), name="stes_discharging_constraint")
    m.model.addConstrs((stes_discharging_cutoff_rule(m, t) for t in m.t), name="stes_discharging_cutoff_constraint")
