import pandas as pd


def convert_from_watt_to_kwh_h(load):
    """
     Convert from average power per minute in watts to kWh/h.
     Energy per minute: (60s * xW) / (60 * 60 s/h * 10^3 Ws/kWh)  --> xW / 60 * 10^3 W/kWh
     Energy per hour: sum of every 60 row
    """
    energy_per_min = load / 60e3
    return energy_per_min.groupby(energy_per_min.index // 60).sum()


def main():
    load_profiles_w = pd.read_csv('ALPG/output/results/Electricity_Profile.csv', sep=';')
    load_profiles_kwh_h = convert_from_watt_to_kwh_h(load_profiles_w)
    load_profiles_kwh_h.to_csv('../../Profiles/Germany/el_demand.csv')


if __name__ == '__main__':
    main()
