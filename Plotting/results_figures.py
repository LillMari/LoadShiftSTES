import matplotlib.pyplot as plt
import numpy as np
from matplotlib import ticker
import pandas as pd
import seaborn as sns

no_lec = {'name': 'no_lec', 'color': 'silver', 'alpha': 1}

cases = [
    {'name': 'base-now', 'legend': '2020 Base', 'color': 'royalblue', 'alpha': 1, 'linestyle': ':'},
    {'name': 'hp-now', 'legend': '2020 HP', 'color': 'green', 'alpha': 1, 'linestyle': '--'},
    {'name': 'stes-now', 'legend': '2020 STES', 'color': 'tomato', 'alpha': 1, 'linestyle': '-'},
    {'name': 'base-future', 'legend': '2030 Base', 'color': 'royalblue', 'alpha': 1, 'linestyle': ':'},
    {'name': 'hp-future', 'legend': '2030 HP', 'color': 'green', 'alpha': 1, 'linestyle': '--'},
    {'name': 'stes-future', 'legend': '2030 STES', 'color': 'tomato', 'alpha': 1, 'linestyle': '-'},
]


def month_xticks(ax):
    months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    month_hours = [m * 24 for m in months]
    month_hours_cum = [sum(month_hours[:x]) for x in range(12)]
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    ax.set_xticks(month_hours_cum)
    ax.set_xticklabels(month_names)


def energy_ylims(ax):
    ax.set_ylim((-420, 420))


def plot_linelosses():
    no_lec_line_loss = pd.read_csv(f'../Results/no_lec/powerflow/line_summaries.csv')['active_line_losses_mw']

    for case in cases:
        if case["name"] == "no_lec":
            continue

        plt.figure(figsize=(10, 5))
        line_loss = pd.read_csv(f'../Results/{case["name"]}/powerflow/line_summaries.csv')['active_line_losses_mw']
        plt.plot(line_loss, label=case['name'], color=case['color'], alpha=case['alpha'])
        plt.plot(no_lec_line_loss, label=no_lec['name'], color=no_lec['color'], alpha=no_lec['alpha'])
        plt.legend()
        plt.ylim(ymax=0.16)
        month_xticks(plt.gca())
        plt.margins(x=0)
        plt.ylabel('Linelosses [MWh/h]')
        plt.show()


def plot_lineloss_diff(cases, compare=False):
    base_line_loss = pd.read_csv(f'../Results/no_lec/powerflow/line_summaries.csv')['active_line_losses_mw']
    for case in cases:
        if case["name"] == "no_lec":
            continue

        line_loss = pd.read_csv(f'../Results/{case["name"]}/powerflow/line_summaries.csv')['active_line_losses_mw']
        loss_diff = line_loss - base_line_loss
        plt.figure(figsize=(6, 3))
        plt.hlines(y=0, xmin=0, xmax=8760, colors='gray')
        if compare:
            case2 = case['name'].replace('future', 'now')
            line_loss2 = pd.read_csv(f'../Results/{case2}/powerflow/line_summaries.csv')['active_line_losses_mw']
            loss_diff2 = line_loss2 - base_line_loss
            plt.plot(loss_diff2 * 1000, label=case['legend'].replace('2030', '2020'), color=case['color'], alpha=0.27)
        plt.plot(loss_diff * 1000, label=case['legend'], color=case['color'], alpha=1)
        month_xticks(plt.gca())
        plt.margins(x=0)
        plt.grid()
        plt.legend(loc="lower right")
        plt.ylim(ymin=-17, ymax=27)
        plt.ylabel('Additional line losses [kWh/h]')
        plt.xlabel('Month')
        plt.tight_layout()
        plt.savefig(f'results_figures/line_loss_difference_{case["name"]}.pdf')
        plt.show()


def plot_duration_curve(selected_cases, name):

    plt.figure(figsize=(7, 3))
    plt.hlines(y=0, xmin=0, xmax=8760, colors='gray')
    # reference = pd.read_csv('../Results/base-now/total_demand.csv', index_col=0)
    # reference = reference.sort_values(ascending=False, ignore_index=True)
    # sns.lineplot(reference, label='No PV', color='gray')
    for case in selected_cases:
        load_imp = pd.read_csv(f'../Results/{case["name"]}/grid_import.csv', index_col=0)
        load_exp = pd.read_csv(f'../Results/{case["name"]}/grid_export.csv', index_col=0)
        load = load_imp['grid_import'] - load_exp['grid_export']
        load = load.sort_values(ascending=False, ignore_index=True)
        sns.lineplot(load, label=case['legend'], color=case['color'], ls=case['linestyle'], lw=2)

    ax = plt.gca()
    length = (len(load)-1)
    ax.set_xticks(np.linspace(0, 1, 11) * length)
    ax.xaxis.set_major_formatter(ticker.PercentFormatter(xmax=length))
    plt.ylabel('Net power import [kWh/h]')
    plt.xlabel('Percentage of year [%]')
    plt.ylim((-450, 400))
    ax = plt.gca()
    plt.margins(x=0)
    plt.tight_layout()
    plt.grid()
    plt.savefig(f'results_figures/duration_curves_{name}.pdf')
    plt.show()


def find_total_load_community():
    total_load = {}
    for case in cases:
        tot_import = pd.read_csv(f'../Results/{case["name"]}/grid_import.csv', index_col=0)
        tot_export = pd.read_csv(f'../Results/{case["name"]}/grid_export.csv', index_col=0)
        net_import = tot_import['grid_import'] - tot_export['grid_export']
        total_load[case['name']] = net_import.sum()
    return total_load


def find_total_load_grid():
    load = pd.read_csv('../Results/no_lec/powerflow/total_load.csv', index_col=0)
    new_load = {}
    for case in cases:
        case_load = pd.read_csv(f'../Results/{case["name"]}/powerflow/total_load.csv', index_col=0)
        new_load[case["name"]] = [case_load.iloc[0, 0], (case_load/load).iloc[0, 0]]

    return new_load


def find_peak_load_grid():
    peak = pd.read_csv('../Results/no_lec/powerflow/P_max.csv', index_col=0)
    new_peak = {}
    for case in cases:
        case_peak = pd.read_csv(f'../Results/{case["name"]}/powerflow/P_max.csv', index_col=0)
        new_peak[case["name"]] = [case_peak.iloc[0, 0], (case_peak/peak).iloc[0, 0]]

    return new_peak


def plot_net_grid_import(selected_cases, compare=False):
    for case in selected_cases:
        tot_import = pd.read_csv(f'../Results/{case["name"]}/grid_import.csv', index_col=0)
        tot_export = pd.read_csv(f'../Results/{case["name"]}/grid_export.csv', index_col=0)
        net_import = tot_import['grid_import'] - tot_export['grid_export']

        plt.figure(figsize=(6, 3))
        plt.hlines(y=0, xmin=0, xmax=8760, colors='gray')
        sns.lineplot(net_import, label=case['legend'], color=case['color'])
        if compare:
            case2 = case['name'].replace('future', 'now')
            tot_import = pd.read_csv(f'../Results/{case2}/grid_import.csv', index_col=0)
            tot_export = pd.read_csv(f'../Results/{case2}/grid_export.csv', index_col=0)
            net_import = tot_import['grid_import'] - tot_export['grid_export']
            sns.lineplot(net_import, label=case['legend'].replace('2030', '2020'), color=case['color'], alpha=0.27                         )
        plt.grid()
        plt.legend(loc='lower right')
        plt.ylabel("Net power import [kWh/h]")
        plt.xlabel('Month')
        month_xticks(plt.gca())
        energy_ylims(plt.gca())
        plt.tight_layout()
        plt.margins(x=0)
        plt.savefig(f'results_figures/net_grid_import_{case["name"]}.pdf')
        plt.show()


def plot_heating_sources(case, name):
    for scenario, year in {'now': '2020', 'future': '2030'}.items():
        heating_sources = pd.read_csv(f'../Results/{case}-{scenario}/heating_sources.csv', index_col=0)
        heating_sources['week'] = heating_sources.index // (7 * 24) + 1
        heating_sources = heating_sources.groupby('week').sum()
        fig, ax = plt.subplots(figsize=(7, 3))
        heating_sources.rename(columns={'resistive_heating': 'Panel Oven',
                                        'stes_heating': 'STES',
                                        'stes_hp_direct': 'Shared HP',
                                        'house_hp_heating': 'Individual HP'}, inplace=True)
        heating_sources.plot(kind='bar', stacked=True, ax=ax)
        ax.set_ylabel("Thermal demand [kWh/week]")
        ax.set_xlabel("Week")
        ax.set_xticks([0] + list(range(4, 51, 5)) + [51])
        plt.legend(title=f'{year} {name}')
        plt.tight_layout()
        plt.savefig(f'results_figures/heating_sources_{case}-{scenario}.pdf')
        plt.show()


def plot_stes_soc():
    plt.figure(figsize=(7, 3))
    stes_soc_now = pd.read_csv(f'../Results/stes-now/stes_soc.csv', index_col=0)
    stes_soc_future = pd.read_csv(f'../Results/stes-future/stes_soc.csv', index_col=0)

    ax = plt.gca()
    ax.plot(stes_soc_now, label='2020')
    ax.plot(stes_soc_future, label='2030')
    plt.grid()
    plt.ylabel("State of Charge [kWh]")

    stes_temperature_now = pd.read_csv(f'../Results/stes-now/stes_temperature.csv', index_col=0)
    stes_temperature_future = pd.read_csv(f'../Results/stes-future/stes_temperature.csv', index_col=0)
    ax2 = plt.gca().twinx()
    line, = ax2.plot(stes_temperature_now, label="_")
    line2, = ax2.plot(stes_temperature_future, label="_")
    ax2.set_ylabel("Average temperature [°C]")

    month_xticks(ax)
    plt.xlim(0, 8760)
    ax.set_xlabel("Month")
    plt.tight_layout()
    ax.legend(loc='upper left', title='SOC case 3 (STES)')
    plt.savefig(f'results_figures/stes_soc.pdf')
    plt.show()


def plot_objective_terms():
    data = pd.DataFrame()

    grouping = {'stes_investment_cost': 'STES',
                'stes_hp_investment_cost': 'STES',
                'house_hp_investment_cost': 'House HP',
                'pv_investment_cost': 'PV',
                'aggregated_capacity_import_tariff': 'Grid tariff',
                'aggregated_capacity_export_tariff': 'Grid tariff',
                'individual_capacity_tariff': 'Grid tariff',
                'connection_cost': 'Grid tariff',
                'grid_volume_tariff': 'Grid tariff',
                'volume_tax_cost': 'Grid tariff',
                'power_market_cost': 'Electricity'}

    for case in cases:
        costs = pd.read_csv(f"../Results/{case['name']}/objective_terms.csv", index_col=0)
        costs = costs.groupby(grouping).sum()
        costs = costs.transpose()
        costs["Scenario + Case"] = case['legend']
        costs = costs.set_index("Scenario + Case", drop=True)
        data = pd.concat([data, costs], axis="rows")

    data = data.loc[:, ["Electricity", "Grid tariff", "PV", "House HP", "STES"]]

    fig = plt.figure(figsize=(7, 4))
    ax = plt.gca()
    data.plot(kind='bar', stacked=True, ax=ax)

    for i, patch in enumerate(ax.containers[-1].patches):
        # find last box with non-0 size:
        last_box = [c for c in ax.containers if c.datavalues[i] > 0][-1]
        if last_box.patches[i] != patch:
            (_, _), (_, y1) = last_box.patches[i].get_bbox().get_points()
            patch.xy = (patch.xy[0], y1)
    ax.bar_label(ax.containers[-1], fmt="{:.0f}")

    ax.set_ylabel("Cost [EUR]")
    ax.set_ylim(top=220000)
    for tick in ax.get_xticklabels():
        tick.set_rotation(0)
    fig.tight_layout()
    plt.savefig('results_figures/cost_terms.pdf')
    plt.show()


def main():
    # plot_linelosses()
    # plot_lineloss_diff(cases[:3], compare=False)
    # plot_lineloss_diff(cases[3:], compare=True)
    # plot_duration_curve(cases[:3], name='now')
    # plot_duration_curve(cases[3:], name='future')
    # print(f'Total load: {find_total_load_grid()}')
    # print(f'Peak load: {find_peak_load_grid()}')
    # plot_net_grid_import(cases[:3], compare=False)
    # plot_net_grid_import(cases[3:], compare=True)
    plot_heating_sources(case='stes', name='Case 3 (STES)')
    plot_heating_sources(case='hp', name='Case 2 (HP)')
    # plot_stes_soc()
    # plot_objective_terms()
    # print(find_total_load_community())


if __name__ == '__main__':
    main()
