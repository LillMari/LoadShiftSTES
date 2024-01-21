# -*- coding: utf-8 -*-
"""
Created on Thu Jan 04 2024

@author: Lill Mari Engan
"""

import pyomo.environ as pyo
import pandas as pd

model = pyo.ConcreteModel()

model.x = pyo.Var([1, 2], within=pyo.NonNegativeReals)


def constrain_rule1(model):
    return model.x[1] + model.x[2] <= 2


def constraint_rule2(model):
    return 2*model.x[1] + model.x[2] <= 3


model.rule1 = pyo.Constraint(rule=constrain_rule1)
model.rule2 = pyo.Constraint(rule=constraint_rule2)


def objective_function(model):
    return 4*model.x[1] + model.x[2]


model.objective = pyo.Objective(rule=objective_function, sense=pyo.maximize)

opt = pyo.SolverFactory('gurobi_direct')
res = opt.solve(model, tee=True)

print(f"x[1]: {model.x[1].value}, x[2]: {model.x[2].value}")