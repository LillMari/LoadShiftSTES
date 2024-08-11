# -*- coding: utf-8 -*-
"""
Created on Thu Jan 09 2024

@author: Lill Mari Engan
"""

import gurobipy as gp
from gurobipy import GRB


def pv_vars(m):
    # How much PV is installed on each house
    m.pv_installed_capacity = m.model.addVars(m.h, ub=m.max_pv_capacity, name="pv_installed_capacity")


def grid_vars(m):
    # Power from and to power market
    m.grid_import = m.model.addVars(m.t, m.h, ub=m.max_grid_import, name="grid_import")  # [kWh/h]
    m.grid_export = m.model.addVars(m.t, m.h, ub=m.max_grid_export, name="grid_export")  # [kWh/h]

    # For each household, and each month, its highest hourly electric consumption or production
    m.peak_monthly_house_volume = m.model.addVars(m.h, m.months, name="peak_monthly_house_volume")  # [kWh/h]

    # For each month, the highest hourly electric volume into and leaving the neighbourhood [kWh/h]
    m.peak_aggregated_monthly_import_volume = m.model.addVars(m.months, name="peak_aggregated_monthly_import_volume")
    m.peak_aggregated_monthly_export_volume = m.model.addVars(m.months, name="peak_aggregated_monthly_export_volume")


def stes_vars(m):
    m.stes_volume = m.model.addVar(lb=m.min_stes_volume, ub=m.max_stes_volume, name="stes_volume")
    m.stes_soc = m.model.addVars(m.t, name="stes_soc")

    m.stes_el = m.model.addVars(m.t, m.h, name="stes_el")
    m.stes_th = m.model.addVars(m.t, m.h, name="stes_th")

    m.stes_hp_max_qw = m.model.addVar(name='stes_hp_max_qw', ub=m.stes_hp_max_qw_possible)  # [kW]
    m.stes_hp_qw = m.model.addVars(m.t, name="stes_hp_qw")  # [kWh] of heat energy
    m.stes_hp_direct_qw = m.model.addVars(m.t, name="stes_hp_direct_qw")  # [kWh] of heat energy
    m.stes_charge_qw = m.model.addVars(m.t, name="stes_charge_qw")  # [kWh] of heat energy
    m.stes_discharge_qc = m.model.addVars(m.t, name="stes_discharge_qc")  # [kWh] of heat energy


def heating_vars(m):
    # A 1:1 conversion from electric energy to heat. No upper bound, but least efficient method
    m.electric_heating = m.model.addVars(m.t, m.h, name="electric_heating")  # [kWh] of heat energy

    # A more efficient way of heating houses, still using electricity.
    m.house_hp_qw = m.model.addVars(m.t, m.h, ub=m.house_hp_max_qw, name="house_hp_qw")  # [kWh] of heat energy
    m.house_hp_installed_capacity = m.model.addVars(m.h, ub=m.house_hp_max_qw, name="house_hp_installed_capacity")
