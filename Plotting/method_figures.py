import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd
from sklearn.linear_model import LinearRegression


NOK2024_TO_EUR = 0.087


def month_xticks(ax):
    months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    month_hours = [m * 24 for m in months]
    month_hours_cum = [sum(month_hours[:x]) for x in range(12)]
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    ax.set_xticks(month_hours_cum)
    ax.set_xticklabels(month_names)


def energy_ylims(ax):
    ax.set_ylim((-420, 420))


def find_week_number(start_day, profile):
    for t in range(len(profile)):
        profile.loc[t, 'week'] = int(((t//24) + start_day) % 7)
    return profile


def plot_pv_profile(save=False):
    pv_profile = pd.read_csv('../PV_profiler/pv_profil_oslo_2014.csv', skiprows=3)['electricity']  # kW/kWp
    pv_profile = pv_profile * 10  # 10 kW_p system

    plt.figure(figsize=(6, 3))
    plt.grid()
    sns.lineplot(pv_profile, label='Hourly')
    month_xticks(plt.gca())
    plt.ylabel('PV production [kWh/h]')
    plt.xlabel('Month')
    plt.ylim(ymin=0, ymax=9)
    plt.legend(loc="upper left")
    ax2 = plt.twinx()
    grouping = 8760//12
    pv_sum = pv_profile.groupby(pv_profile.index // grouping).sum()
    pv_sum.index = ((pv_sum.index + 0.5) * grouping).astype(int)
    sns.lineplot(pv_sum, ax=ax2, color='darkorange', lw=3, label='Monthly')
    ax2.set_ylabel('PV production [kWh/month]')
    ax2.set_ylim(0, 1420)
    plt.xlim(0, 8760)
    plt.tight_layout()
    ax2.legend(loc="upper right")
    if save:
        plt.savefig('method_figures/pv_profile.pdf')
    plt.show()


def plot_temperature_profile():
    temp_profile = pd.read_csv('../Temperaturprofiler/temperatur_blindern2021.csv')['temperature [degC]']
    plt.figure(figsize=(7, 3))
    plt.plot(temp_profile)
    month_xticks(plt.gca())
    plt.grid()
    plt.ylabel('Outside temperature [$^\circ$C]')
    plt.xlabel('Month')
    plt.margins(x=0)
    plt.tight_layout()
    plt.savefig('method_figures/temperature_profile.pdf')
    plt.show()


def plot_grid_rent(save=False):
    x = [0, 2, 2, 5, 5, 10, 10, 15, 15, 20]
    y_nok = [120, 120, 190, 190, 305, 305, 420, 420, 535, 535]
    y = [i*NOK2024_TO_EUR for i in y_nok]

    x2 = np.linspace(0, 20, 5)
    y2 = x2 * 24.65 * NOK2024_TO_EUR + 95.39 * NOK2024_TO_EUR

    plt.figure(figsize=(7, 3))
    plt.ylim(0, 50)
    plt.grid()
    plt.plot(x, y, label='Elvia\'s step model', lw=3)
    plt.plot(x2, y2, label=f'{24.65 * NOK2024_TO_EUR:.1f}' +
                           r' $\frac{€}{kWh/h}$ x +' + f'{95.39 * NOK2024_TO_EUR:.1f} €', lw=3)
    plt.xlabel('Maximum hourly power use [kWh/h]')
    plt.ylabel('Capacity grid tariff [€]')
    plt.tight_layout()
    plt.margins(x=0)
    plt.gca().set_xticks([0, 2, 5, 10, 15, 20])
    plt.legend()
    if save:
        plt.savefig('method_figures/step_model.pdf')
    plt.show()


def plot_el_th_profile(save=False):
    el_demand = pd.read_csv('../Results/base-now/el_demand.csv', index_col=0)
    th_demand = pd.read_csv('../Results/base-now/th_demand.csv', index_col=0)

    fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, sharex='all', sharey='all', figsize=(8, 5))
    plt.ylabel("Electric demand [kWh/h]")
    ax1.plot(el_demand.index, el_demand['el_demand'], label='Electric demand')
    ax1.grid(True)
    ax1.set_ylabel("Electric demand [kWh/h]")
    month_xticks(plt.gca())
    ax1.margins(x=0)

    ax2.plot(th_demand.index, th_demand['th_demand'], label='Thermal demand')
    ax2.grid(True)
    ax2.set_ylabel("Thermal demand [kWh/h]")
    month_xticks(plt.gca())
    ax2.margins(x=0)
    plt.tight_layout()
    if save:
        plt.savefig('method_figures/el_and_th_demand.pdf')
    plt.show()


def plot_CINELDI_total_load():
    from Power_flow.power_flow import set_up_lec_sim

    network = set_up_lec_sim({})
    load_profile = network.Ps

    fig, ax1 = plt.subplots(figsize=(7, 3))

    ax1.plot(load_profile.sum(axis=1))
    ax1.set_ylim(0, 5.5)
    month_xticks(ax1)
    ax1.margins(x=0)
    ax1.grid()
    ax1.set_ylabel("Total demand [MWh/h]")
    plt.tight_layout()
    plt.savefig('method_figures/cineldi_total_demand.pdf')
    plt.show()


def plot_spot_price(name):
    if name == '2019':
        filename = '../Historic_spot_prices/spot_price_2019.csv'
    elif name == '2030':
        filename = '../Framtidspriser/future_spot_price_NVE_mean_only.csv'
    else:
        ValueError('Ugyldig prisprofil')

    hist_spot_price = pd.read_csv(filename, index_col=0) * 1e-3
    plt.figure(figsize=(7, 3))
    plt.plot(hist_spot_price.iloc[:, 0])
    plt.grid()
    month_xticks(plt.gca())
    plt.ylabel('Spot price [€/kWh]')
    plt.xlabel('Month')
    plt.margins(x=0)
    plt.tight_layout()
    plt.ylim(0, 0.12)
    plt.savefig(f'method_figures/spot_price_{name}.pdf')
    plt.show()


def plot_stes_cost():
    stes_cost_volume = {'DLSC': [542203.9, 34000],
                        'Brædstrup': [321368.21, 19000],
                        'Aberdeen': [491265.93, 34000],
                        'Camborne': [491265.93, 34000],
                        'Ontario': [320791.05, 19500],
                        'Crailsheim': [520000, 37500],
                        'Neckarsulm-1': [450000, 20000],
                        'Neckarsulm-2': [749000, 63000],
                        'Andalucia': [154826.1, 18000],
                        }
    # Based on simulations with very low borehole cost
    # 'Anneberg': [165414.83, 60000]

    stes_cost = pd.DataFrame.from_dict(stes_cost_volume, orient='index',
                                       columns=['Investment cost [€]', 'Ground volume [m3]'])

    lr = LinearRegression()
    x = stes_cost['Ground volume [m3]'].values.reshape(-1, 1)
    y = stes_cost['Investment cost [€]'].values.reshape(-1, 1)
    lr.fit(x, y)

    m = lr.coef_[0][0]  # STES capacity cost
    b = lr.intercept_[0]  # STES investment cost
    fig, ax = plt.subplots(figsize=(7, 4))
    plt.grid()
    plt.margins(x=0.01)
    sns.regplot(stes_cost, x=f'Ground volume [m3]', y='Investment cost [€]', ax=ax)
    ax.set_xlabel(f'Ground volume [m$^3$]')
    ax.lines[0].set_label(f'{m:.1f}' + r'$\frac{€}{m^3}$ x +' + f'{b/1000:.0f}' + r'$\cdot 10^3 €$')
    ax.legend(loc='upper left')
    ax2 = ax.twiny()
    volume_to_energy = lambda v: 20 * v
    ax2.set_xlim(map(volume_to_energy, ax.get_xlim()))
    ax2.set_xlabel(f"Estimated ground heat capacity [kWh]")
    fig.tight_layout()
    plt.savefig('method_figures/BTES_investment_cost.pdf')
    plt.show()


def main():
    # plot_weekly_el_th_demand()
    # plot_pv_profile(save=True)
    # plot_grid_rent(save=True)
    # plot_el_th_profile(save=True)
    # plot_CINELDI_total_load()
    # plot_temperature_profile()
    # plot_spot_price('2019')
    # plot_spot_price('2030')
    plot_stes_cost()


if __name__ == '__main__':
    main()
