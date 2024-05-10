import pandas as pd
from Power_flow.network import Network


def set_up_lec_sim(lec_load_profiles):
    """

    :param lec_bus_profiles: dictionary mapping lec bus to a load profile
    :return:
    """
    case_file = '../CINELDI_MV_reference_system/casecineldi124_new.m'
    load_file = '../CINELDI_MV_reference_system/load_data_CINELDI_MV_reference_system.csv'
    load_mapping_file = '../CINELDI_MV_reference_system/mapping_loads_to_CINELDI_MV_reference_grid.csv'

    lec_sim = Network(case_file, load_file, load_mapping_file, lec_load_profiles)

    return lec_sim


def find_net_load(folder):
    tot_import = pd.read_csv(f'../Results/{folder}/grid_import.csv', index_col=0) * 1e-3
    tot_export = pd.read_csv(f'../Results/{folder}/grid_export.csv', index_col=0) * 1e-3
    return tot_import['grid_import'] - tot_export['grid_export']



