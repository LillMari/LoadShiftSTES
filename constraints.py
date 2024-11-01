# -*- coding: utf-8 -*-
"""
Created on Thu Jan 09 2024

@author: Lill Mari Engan
"""


def add_constrs(m, constraints, name=None):
    """ Takes a generator of constraints and adds them all to the model m """
    # name is ignored to save RAM
    for constraint in constraints:
        m.solver.Add(constraint)


def el_load_rule(m, t, h):
    """ Electric load is used to cover electric demand and electricity used for thermal demand """
    return (m.el_load[t, h] == m.el_demand[t, h] + m.electric_heating[t, h] + m.house_hp_qw[t, h] / m.house_hp_cop[t]
            + m.stes_el[t, h])

def electric_energy_rule(m, t, h):
    """ The electric demand is covered by the grid, the local market and by its own PV system """
    return m.el_load[t, h] == m.grid_import[t, h] - m.grid_export[t, h] + m.pv_production[t] * m.pv_installed_capacity[h]

def thermal_energy_rule(m, t, h):
    return m.electric_heating[t, h] + m.house_hp_qw[t, h] + m.stes_th[t, h] == m.th_demand[t, h]

def max_import_rule(m, t, h):
    """ Each house can not import more than the electric load in a given hour """
    return m.grid_import[t, h] <= m.el_load[t, h]

def max_export_rule(m, t, h):
    """ Each house can not export more power than surplus power production """
    return (m.grid_export[t, h] <= m.pv_production[t] * m.pv_installed_capacity[h] -
            (m.el_load[t, h] - m.grid_import[t, h]))

def hourly_electricity_cost_rule(m, t, h):
    return m.hourly_grid_cost[t, h] >= m.power_market_price[t] * m.grid_import[t, h] - m.feed_in_tariff[t] * m.grid_export[t, h]

def monthly_electricity_cost_rule(m, h, month):
    hours = m.month_to_hour[month]
    el_bill = sum([m.hourly_grid_cost[t, h] for t in hours])
    return m.monthly_electricity_bill[h, month] >= el_bill

def peak_monthly_individual_volume_rule(m, t, h, sign):
    """ Rule tracking the peak hour of grid volume per household, each month """
    month = m.month_from_hour[t]
    total_consume = m.grid_import[t, h] - m.grid_export[t, h]
    return sign * total_consume <= m.peak_monthly_house_volume[h, month]


def house_hp_max_qw_rule(m, t, h):
    return m.house_hp_qw[t, h] <= m.house_hp_installed_capacity[h]


def stes_el_rule(m, t):
    source = sum(m.stes_el[t, h] for h in m.h)
    sink = m.stes_hp_qw[t] / m.stes_hp_cop[t] + m.stes_discharge_qc[t] / (m.stes_discharge_cop - 1)
    return source == sink


def stes_hp_max_qw_rule(m, t):
    return m.stes_hp_qw[t] <= m.stes_hp_max_qw


def stes_hp_qw_usage_rule(m, t):
    return m.stes_hp_qw[t] == m.stes_charge_qw[t] + m.stes_hp_direct_qw[t]


def stes_th_rule(m, t):
    """ m.stes_th[t, h] is the thermal energy delivered to house h at hour t from the heating loop """
    source = m.stes_hp_direct_qw[t] + m.stes_discharge_qc[t] / (1 - 1/m.stes_discharge_cop)
    sink = sum(m.stes_th[t, h] for h in m.h)
    return source == sink


def stes_soc_evolution_rule(m, t):
    if t > 0:
        last_hour = m.stes_soc[t - 1]
    else:
        last_hour = m.stes_soc[m.t[-1]]

    return m.stes_soc[t] == last_hour * m.heat_retainment + \
        m.stes_charge_qw[t] * m.stes_charge_eta - m.stes_discharge_qc[t] / m.stes_discharge_eta


def stes_charging_rate_rule(m, t):
    temp_increase = m.stes_charge_qw[t] * m.stes_charge_eta / m.volumetric_heat_capacity
    temp_volume = m.ground_base_temperature * m.stes_volume + m.stes_soc[t] / m.volumetric_heat_capacity
    A = m.max_temperature_increase / (m.water_stes_temperature - m.min_stes_temperature)
    B = A * m.water_stes_temperature
    max_temp_increase = -A * temp_volume + B * m.stes_volume
    return temp_increase <= max_temp_increase


def stes_discharging_rate_rule(m, t):
    temp_decrease = m.stes_discharge_qc[t] / m.stes_discharge_eta / m.volumetric_heat_capacity
    temp_volume = m.ground_base_temperature * m.stes_volume + m.stes_soc[t] / m.volumetric_heat_capacity
    A = m.max_temperature_decrease / (m.water_stes_temperature - m.min_stes_temperature)
    B = -A * m.min_stes_temperature
    max_temp_decrease = A * temp_volume + B * m.stes_volume
    return temp_decrease <= max_temp_decrease


def lec_constraints(m):
    add_constrs(m, (el_load_rule(m, t, h) for t in m.t for h in m.h), name='el_load_rule')
    add_constrs(m, (electric_energy_rule(m, t, h) for t in m.t for h in m.h), name="electric_energy_constraint")
    add_constrs(m, (thermal_energy_rule(m, t, h) for t in m.t for h in m.h), name="thermal_energy_constraint")
    add_constrs(m, (max_import_rule(m, t, h) for t in m.t for h in m.h), name='max_import_rule')
    add_constrs(m, (max_export_rule(m, t, h) for t in m.t for h in m.h), name='max_export_rule')
    add_constrs(m, (hourly_electricity_cost_rule(m, t, h) for t in m.t for h in m.h), name='hourly_electricity_cost_rule')

    add_constrs(m, (monthly_electricity_cost_rule(m, h, month) for h in m.h for month in m.months),
                name='monthly_electricity_cost_rule')
    add_constrs(m, (peak_monthly_individual_volume_rule(m, t, h, s) for t in m.t for h in m.h for s in m.sign),
                name="peak_monthly_house_volume_constraint")

    # House hp constraint
    add_constrs(m, (house_hp_max_qw_rule(m, t, h) for t in m.t for h in m.h), name="house_hp_max_qw_constraint")

    # STES constraints
    add_constrs(m, (stes_el_rule(m, t) for t in m.t), name="stes_el_constraint")
    add_constrs(m, (stes_hp_max_qw_rule(m, t) for t in m.t), name="stes_hp_max_qw_constraint")
    add_constrs(m, (stes_hp_qw_usage_rule(m, t) for t in m.t), name="stes_hp_qw_usage_constraint")
    add_constrs(m, (stes_th_rule(m, t) for t in m.t), name="stes_th_constraint")
    add_constrs(m, (stes_soc_evolution_rule(m, t) for t in m.t), name="stes_soc_evolution_constraint")
    add_constrs(m, (stes_charging_rate_rule(m, t) for t in m.t), name="stes_charging_rate_constraint")
    add_constrs(m, (stes_discharging_rate_rule(m, t) for t in m.t), name="stes_discharging_rate_constraint")
