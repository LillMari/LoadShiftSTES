# -*- coding: utf-8 -*-
"""
Created on Thu Jan 09 2024

@author: Lill Mari Engan
"""

import itertools
import numpy as np


def add_var(m, *indices, lb=None, ub=None, name=None):
    """
    Adds a set of variables to the model, indexed by the set(s) provided as indices
    :param m: the model
    :param indices: zero, one or more sets of indices
    :param lb: the lower bound, default is 0.0
    :param ub: the upper bound, default is infinity
    :param name: the name of the variable, for debugging
    :return: a set of variables, indexed using the indices sets if any indices are provided
    """

    if lb is None:
        lb = 0.0
    if ub is None:
        ub = m.solver.infinity()

    # We ignore the name, as it only serves as debugging, and otherwise wastes RAM
    name = ""

    # No index sets provided, just create a single variable
    if len(indices) == 0:
        return m.solver.NumVar(lb, ub, name)

    # A single index set provided, create one variable for each index in the set
    if len(indices) == 1:
        return {i: m.solver.NumVar(lb, ub, name) for i in indices[0]}

    # Multiple index sets provided, use their cartesian product to index variables
    return {i: m.solver.NumVar(lb, ub, name) for i in itertools.product(*indices)}


def pv_vars(m):
    # How much PV is installed on each house
    m.pv_installed_capacity = add_var(m, m.h, ub=m.max_pv_capacity, name="pv_installed_capacity")


def grid_vars(m):
    # Power from and to power market
    m.grid_import = add_var(m, m.t, m.h, ub=m.max_grid_import, name="grid_import")  # [kWh/h]
    m.grid_export = add_var(m, m.t, m.h, ub=m.max_grid_export, name="grid_export")  # [kWh/h]

    m.el_load = add_var(m, m.t, m.h, name="el_load")
    m.hourly_grid_cost = add_var(m, m.t, m.h, lb=-np.inf, name="hourly_grid_cost")             # [EUR/h]

    # For each household, and each month, its highest hourly electric consumption or production
    m.peak_monthly_house_volume = add_var(m, m.h, m.months, name="peak_monthly_house_volume")  # [kWh/h]
    m.monthly_electricity_bill = add_var(m, m.h, m.months, lb=m.el_bill_lb, name="monthly_electricity_bill")  # [EUR/month]


def stes_vars(m):
    m.stes_volume = add_var(m, lb=m.min_stes_volume, ub=m.max_stes_volume, name="stes_volume")
    m.stes_soc = add_var(m, m.t, name="stes_soc")

    m.stes_el = add_var(m, m.t, m.h, name="stes_el")
    m.stes_th = add_var(m, m.t, m.h, name="stes_th")

    m.stes_hp_max_qw = add_var(m, name='stes_hp_max_qw', ub=m.stes_hp_max_qw_possible)  # [kW]
    m.stes_hp_qw = add_var(m, m.t, name="stes_hp_qw")  # [kWh] of heat energy
    m.stes_hp_direct_qw = add_var(m, m.t, name="stes_hp_direct_qw")  # [kWh] of heat energy
    m.stes_charge_qw = add_var(m, m.t, name="stes_charge_qw")  # [kWh] of heat energy
    m.stes_discharge_qc = add_var(m, m.t, name="stes_discharge_qc")  # [kWh] of heat energy


def heating_vars(m):
    # A 1:1 conversion from electric energy to heat. No upper bound, but least efficient method
    m.electric_heating = add_var(m, m.t, m.h, name="electric_heating")  # [kWh] of heat energy

    # A more efficient way of heating houses, still using electricity.
    m.house_hp_qw = add_var(m, m.t, m.h, ub=m.house_hp_max_qw, name="house_hp_qw")  # [kWh] of heat energy
    m.house_hp_installed_capacity = add_var(m, m.h, ub=m.house_hp_max_qw, name="house_hp_installed_capacity")
