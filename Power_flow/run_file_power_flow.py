import power_flow as pf


def main():
    global lec_sim
    cases = ['base-now', 'hp-now', 'stes-now', 'base-future', 'hp-future', 'stes-future', 'no_lec']
    for case in cases:
        if case != 'no_lec':
            lec_profiles = {89: pf.find_net_load(case)}  # LEC bus_i: 89, 104, 65, 30, 38
        else:
            lec_profiles = {}
        lec_sim = pf.set_up_lec_sim(lec_profiles)

        time_steps = range(8760)
        lec_sim.run_time_series(time_steps)
        lec_sim.write_results_to_folder(f'../Results/{case}/powerflow')


if __name__ == '__main__':
    main()
