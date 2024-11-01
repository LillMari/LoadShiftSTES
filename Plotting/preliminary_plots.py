import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

SAVE_PATH = 'preliminary_plots'

# TODO: Forenkle
cases = {
    'Norway': [
        {'name': 'base-now-Norway', 'legend': 'Base', 'color': 'royalblue', 'alpha': 1, 'linestyle': ':'},
        {'name': 'hp-now-Norway', 'legend': 'HP', 'color': 'green', 'alpha': 1, 'linestyle': '--'},
        {'name': 'stes-now-Norway', 'legend': 'STES', 'color': 'tomato', 'alpha': 1, 'linestyle': '-'}],
    'Germany': [
        {'name': 'base-now-Germany', 'legend': 'Base', 'color': 'royalblue', 'alpha': 1, 'linestyle': ':'},
        {'name': 'hp-now-Germany', 'legend': 'HP', 'color': 'green', 'alpha': 1, 'linestyle': '--'},
        {'name': 'stes-now-Germany', 'legend': 'STES', 'color': 'tomato', 'alpha': 1, 'linestyle': '-'}],
    'Spain': [
        {'name': 'base-now-Spain', 'legend': 'Base', 'color': 'royalblue', 'alpha': 1, 'linestyle': ':'},
        {'name': 'hp-now-Spain', 'legend': 'HP', 'color': 'green', 'alpha': 1, 'linestyle': '--'},
        {'name': 'stes-now-Spain', 'legend': 'STES', 'color': 'tomato', 'alpha': 1, 'linestyle': '-'}]
}


def month_xticks(ax):
    months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    month_hours = [m * 24 for m in months]
    month_hours_cum = [sum(month_hours[:x]) for x in range(12)]
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    ax.set_xticks(month_hours_cum)
    ax.set_xticklabels(month_names)


def get_countries():
    return ['Norway', 'Germany', 'Spain']


def plot_duration_curve(selected_cases, name, peak=False, nhours=None):
    file_name = f'duration_curves_{name}'
    y_min = -450
    y_max = 400
    x_max = 8760
    plt.figure(figsize=(9, 4))
    for case in selected_cases:
        load_imp = pd.read_csv(f'../Results/{case["name"]}/grid_import.csv', index_col=0)
        load_exp = pd.read_csv(f'../Results/{case["name"]}/grid_export.csv', index_col=0)
        load = load_imp['grid_import'] - load_exp['grid_export']
        if peak:
            peak_hours_df = pd.read_csv(f'../Profiles/{name}/peak_hours_{nhours}.csv', index_col=0)
            peak_hours_df['DateUTC'] = pd.to_datetime(peak_hours_df['DateUTC'], dayfirst=True)
            peak_hours = [(time.dayofyear - 1) * 24 + time.hour for time in peak_hours_df['DateUTC']]
            load = load.iloc[peak_hours]
            y_min = None
            y_max = None
            x_max = nhours
            file_name = f'duration_curves_{name}_peak_{nhours}'
        load = load.sort_values(ascending=False, ignore_index=True)
        sns.lineplot(load, label=case['legend'], color=case['color'], ls=case['linestyle'], lw=2)
    plt.hlines(y=0, xmin=0, xmax=x_max, colors='gray')
    plt.ylabel('Net power import [kWh/h]')
    plt.xlabel('Hours [h]')
    plt.ylim((y_min, y_max))
    plt.margins(x=0)
    plt.grid()
    plt.title(name)

    plt.savefig(f'{SAVE_PATH}/{file_name}.pdf')
    plt.show()


def plot_all_duration_curves():
    for country in get_countries():
        plot_duration_curve(selected_cases=cases[country], name=country, peak=False)
        plot_duration_curve(selected_cases=cases[country], name=country, peak=True, nhours=50)
        plot_duration_curve(selected_cases=cases[country], name=country, peak=True, nhours=100)


def plot_temperature_profile():
    plt.figure(figsize=(7, 3))
    for country in get_countries():
        temp_profile = pd.read_csv(f'../Profiles/{country}/temperature_profile.csv')['temperature [degC]']
        plt.plot(temp_profile, label=country)
    month_xticks(plt.gca())
    plt.legend()
    plt.ylabel('Outside temperature [$^\\circ$C]')
    plt.xlabel('Month')
    plt.margins(x=0)
    plt.tight_layout()
    plt.savefig(f'{SAVE_PATH}/temperature_profiles.pdf')
    plt.show()


def plot_spot_price_profile():
    plt.figure(figsize=(7, 3))
    for country in get_countries():
        spot_price = pd.read_csv(f'../Profiles/{country}/spot_price.csv', index_col=0)
        plt.plot(spot_price, label=country, alpha=0.7)
    month_xticks(plt.gca())
    plt.legend()
    plt.ylabel('Spot prices [€/MWh]')
    plt.xlabel('Month')
    plt.margins(x=0)
    plt.tight_layout()
    plt.savefig(f'{SAVE_PATH}/spot_price_profiles.pdf')
    plt.show()


def plot_pv_profile():
    grouping = 8760 // 12
    plt.figure(figsize=(7, 3))
    for country in get_countries():
        pv_profile = pd.read_csv(f'../Profiles/{country}/pv_profile.csv', skiprows=3)['electricity']  # kW/kWp
        pv_profile = pv_profile * 10  # 10 kW_p system
        pv_sum = pv_profile.groupby(pv_profile.index // grouping).sum()
        pv_sum.index = ((pv_sum.index + 0.5) * grouping).astype(int)
        sns.lineplot(pv_sum, lw=3, label=country)
    month_xticks(plt.gca())
    plt.ylabel('PV production [kWh/h]')
    plt.xlabel('Month')
    plt.ylim(ymin=0)
    plt.legend(loc="upper left")

    plt.xlim(0, 8760)
    plt.savefig(f'{SAVE_PATH}/pv_profile.pdf')
    plt.show()


def plot_el_profile():
    plt.figure(figsize=(7, 3))
    for country in get_countries():
        el_demand = pd.read_csv(f'../Profiles/{country}/el_demand.csv', index_col=0).sum(axis=1)
        plt.plot(el_demand.index, el_demand, label=country)
    plt.ylabel("Electric demand [kWh/h]")
    month_xticks(plt.gca())
    plt.margins(x=0)
    plt.legend()
    plt.savefig(f'{SAVE_PATH}/el_demand.pdf')
    plt.show()


def plot_th_profile():
    plt.figure(figsize=(7, 3))
    for country in get_countries():
        th_demand = pd.read_csv(f'../Profiles/{country}/th_demand.csv', index_col=0).sum(axis=1)
        plt.plot(th_demand.index, th_demand, label=country)
    plt.ylabel("Thermal demand [kWh/h]")
    month_xticks(plt.gca())
    plt.margins(x=0)
    plt.legend()
    plt.savefig(f'{SAVE_PATH}/th_demand.pdf')
    plt.show()


def plot_total_demand_profile():
    plt.figure(figsize=(7, 3))
    for country in get_countries():
        el_demand = pd.read_csv(f'../Profiles/{country}/el_demand.csv', index_col=0).sum(axis=1)
        th_demand = pd.read_csv(f'../Profiles/{country}/th_demand.csv', index_col=0).sum(axis=1)
        total_demand = th_demand + el_demand
        plt.plot(total_demand.index, total_demand, label=country)
    plt.ylabel("Total energy demand [kWh/h]")
    month_xticks(plt.gca())
    plt.margins(x=0)
    plt.legend()
    plt.savefig(f'{SAVE_PATH}/total_demand.pdf')
    plt.show()


def plot_stes_soc():
    plt.figure(figsize=(7, 3))
    soc_dict = {}
    temp_dict = {}
    for country in get_countries():
        soc_dict[country] = pd.read_csv(f'../Results/stes-now-{country}/stes_soc.csv', index_col=0)
        temp_dict[country] = pd.read_csv(f'../Results/stes-now-{country}/stes_temperature.csv', index_col=0)

    ax = plt.gca()
    for country, soc in soc_dict.items():
        ax.plot(soc, label=country)
    plt.grid()
    plt.ylabel("State of Charge [kWh]")

    ax2 = plt.gca().twinx()
    for country, temp in temp_dict.items():
        line, = ax2.plot(temp, label="_")
    ax2.set_ylabel("Average temperature [°C]")

    month_xticks(ax)
    plt.xlim(0, 8760)
    ax.set_xlabel("Month")
    plt.tight_layout()
    ax.legend(loc='upper left', title='STES SOC')
    plt.savefig(f'{SAVE_PATH}/stes_soc.pdf')
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
    for country in get_countries():
        for case in cases[country]:
            costs = pd.read_csv(f"../Results/{case['name']}/objective_terms.csv", index_col=0)
            costs = costs.groupby(grouping).sum()
            costs = costs.transpose()
            costs["Scenario + Case"] = case['legend']
            costs = costs.set_index("Scenario + Case", drop=True)
            data = pd.concat([data, costs], axis="rows")

    data = data.loc[:, ["Electricity", "Grid tariff", "PV", "House HP", "STES"]]

    fig = plt.figure(figsize=(10, 4))
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
    plt.savefig(f'{SAVE_PATH}/cost_terms.pdf')
    plt.show()


def plot_heating_sources():
    for country in get_countries():
        heating_sources = pd.read_csv(f'../Results/stes-now-{country}/heating_sources.csv', index_col=0)
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
        plt.tight_layout()
        plt.legend(title=country)
        plt.savefig(f'{SAVE_PATH}/heating_sources_{country}.pdf')
        plt.show()


def plot_all_spot_prices():
    for country in get_countries():
        plt.figure(figsize=(9, 4))
        for year in ['19', '20', '21', '22', '23']:
            spot_price = pd.read_csv(f'../Historic_spot_prices/spot_price_{country}_20{year}.csv')
            plt.plot(spot_price.index, spot_price.iloc[:, 1], label=f'20{year}', alpha=0.8)
        month_xticks(plt.gca())
        plt.xlabel('Month')
        plt.ylabel('€/MWh')
        plt.legend(title=country)
        plt.savefig(f'{SAVE_PATH}/spot_prices_{country}_2019_2023.pdf')
        plt.show()


def main():
    # plot_el_profile()
    # plot_th_profile()
    # plot_pv_profile()
    # plot_temperature_profile()
    # plot_total_demand_profile()
    plot_all_duration_curves()
    # plot_stes_soc()
    # plot_objective_terms()
    # plot_spot_price_profile()
    # plot_heating_sources()
    # plot_all_spot_prices()


if __name__ == '__main__':
    main()
