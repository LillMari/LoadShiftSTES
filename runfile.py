import sys
from ortools.linear_solver import pywraplp
from Countries import NorwayModelbuilder, GermanyModelbuilder, SpainModelbuilder
from solution_writer import *

def lec_scenario(directory, *, country, country_model, enable_house_hp, enable_stes, solver=None):
    global lec_model, builder

    builder = country_model(country=country,
                           enable_house_hp=enable_house_hp,
                           enable_stes=enable_stes)

    lec_model = builder.create_lec_model(solver=solver)
    # lec_model.model.optimize()  # Barrier method
    print(f"Solving with {lec_model.solver.SolverVersion()}")
    lec_model.solver.EnableOutput()
    lec_model.solver.Solve()
    print(f"Problem solved in {lec_model.solver.wall_time()//1000} seconds")
    print(f"Problem solved in {lec_model.solver.iterations()} iterations")

    write_results_to_csv(lec_model, directory)


def main(directory):
    args = sys.argv[1:]
    if len(args) == 1:
        config = args[0]
    elif len(args) == 0:
        config = input("What configuration should be executed? ")
    else:
        raise ValueError("Unexpected number of arguments")

    country, investments = config.split("-")
    if investments == 'base':
        enable_house_hp = False
        enable_stes = False
    elif investments == 'hp':
        enable_house_hp = True
        enable_stes = False
    elif investments == 'stes':
        enable_house_hp = False
        enable_stes = True
    else:
        raise ValueError(f"Unknown investment config: {investments}")

    countries = {'Norway': NorwayModelbuilder, 'Germany': GermanyModelbuilder, 'Spain': SpainModelbuilder}
    if country not in countries.keys():
        raise ValueError(f"Unknown country config: {country}")

    print(f"Running config {config}")
    lec_scenario(country=country,
                 country_model=countries[country],
                 directory=config + directory,
                 enable_house_hp=enable_house_hp,
                 enable_stes=enable_stes,
                 solver=pywraplp.Solver.GUROBI_LINEAR_PROGRAMMING)


if __name__ == "__main__":
    main('_test1')
