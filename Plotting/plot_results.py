import os.path

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
month_hours = [m*24 for m in months]
month_hours_cum = [sum(month_hours[:x]) for x in range(12)]
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


scenarios = {
    "base-now": "../Results/base-now",
    "hp-now": "../Results/hp-now",
    "stes-now": "../Results/stes-now",
    # "base-exporttariff": "../Results/base-exporttariff",
    # "hp-exporttariff": "../Results/hp-exporttariff",
    # "stes-exporttariff": "../Results/stes-exporttariff",
    "base-future": "../Results/base-future",
    "hp-future": "../Results/hp-future",
    "stes-future": "../Results/stes-future",
}


def month_xticks(ax):
    ax.set_xticks(month_hours_cum)
    ax.set_xticklabels(month_names)


def energy_ylims(ax):
    ax.set_ylim((-420, 420))


def plot_run(name, folder):
    tot_import = pd.read_csv(f'{folder}/grid_import.csv', index_col=0)
    tot_export = pd.read_csv(f'{folder}/grid_export.csv', index_col=0)
    net_import = tot_import['grid_import'] - tot_export['grid_export']

    plt.figure(figsize=(10, 3))
    sns.lineplot(net_import)
    plt.grid()
    plt.title(f'Net grid import, {name}')
    plt.ylabel("Grid volume [kWh/h]")
    month_xticks(plt.gca())
    energy_ylims(plt.gca())
    plt.tight_layout()
    plt.show()
    print(f"Max net grid volume, {name}: {net_import.max()}")
    print(f"Min net grid volume, {name}: {net_import.min()}")
    print(f"Total grid volume, {name}: {net_import.abs().sum()}")
    print(f"RMS grid volume, {name}: {np.sqrt(net_import.pow(2).mean())}")

    heating_sources = pd.read_csv(f'{folder}/heating_sources.csv', index_col=0)
    heating_sources['week'] = heating_sources.index // (7*24)
    heating_sources = heating_sources.groupby('week').sum()
    fig, ax = plt.subplots(figsize=(10, 3))
    heating_sources.plot(kind='bar', stacked=True, ax=ax)
    fig.suptitle(f'Heating sources, {name}')
    ax.set_ylabel("Heat provided [kWh]")
    ax.set_xlabel("Week")
    plt.tight_layout()
    plt.show()

    if os.path.exists(f'{folder}/stes_soc.csv'):
        stes_soc = pd.read_csv(f'{folder}/stes_soc.csv', index_col=0)
        plt.figure(figsize=(10, 3))
        sns.lineplot(stes_soc)
        plt.grid()
        plt.title(f'STES soc, {name}')
        month_xticks(plt.gca())

        stes_volume = pd.read_csv(f'{folder}/stes_temperature.csv', index_col=0)
        ax2 = plt.gca().twinx()
        ax2.plot(stes_volume)

        plt.tight_layout()
        plt.show()

    if os.path.exists(f'{folder}/stes_charge_qw.csv') and os.path.exists(f'{folder}/stes_discharge_qc.csv'):
        stes_charge = pd.read_csv(f'{folder}/stes_charge_qw.csv', index_col=0)
        stes_discharge = pd.read_csv(f'{folder}/stes_discharge_qc.csv', index_col=0)
        stes_net_energy = stes_charge['stes_charge_qw'] - stes_discharge['stes_discharge_qc']
        stes_net_energy = np.cumsum(stes_net_energy.values)

        plt.figure(figsize=(10, 3))
        miny = np.min(stes_net_energy)
        maxy = np.max(stes_net_energy)
        lasty = stes_net_energy[-1]
        plt.axhline(y=miny, color='red')
        plt.text(x=np.argmin(stes_net_energy), y=miny, s=f'{miny:.0f}', color='red', va="top")
        plt.axhline(y=maxy, color='red')
        plt.text(x=np.argmax(stes_net_energy), y=maxy, s=f'{maxy:.0f}', color='red', va="bottom")
        plt.axhline(y=lasty, color='red')
        plt.text(x=len(stes_net_energy), y=lasty, s=f'{lasty:.0f}', color='red', va="bottom")

        sns.lineplot(stes_net_energy)

        loss = 1 - (stes_discharge['stes_discharge_qc'].sum() / stes_charge['stes_charge_qw'].sum())

        plt.grid()
        plt.title(f'STES net energy, {name}, total loss={loss*100:.2f}%')
        month_xticks(plt.gca())
        plt.tight_layout()
        plt.show()

    if os.path.exists(f'{folder}/local_import.csv'):
        local_import = pd.read_csv(f'{folder}/local_import.csv', index_col=0)
        plt.figure(figsize=(10, 3))
        sns.lineplot(local_import)
        plt.grid()
        plt.title(f'local import, {name}')
        plt.ylabel("Power volume [kWh/h]")
        month_xticks(plt.gca())
        energy_ylims(plt.gca())
        plt.tight_layout()
        plt.show()

    if os.path.exists(f'{folder}/pv_installed_capacity.csv'):
        pv_installed_capacity = pd.read_csv(f'{folder}/pv_installed_capacity.csv', index_col=0)
        print(f"PV installed capacity, {name}:", pv_installed_capacity.sum().values, "kWp")


for name, path in scenarios.items():
    plot_run(name, path)


el_demand = pd.read_csv('../Results/base-now/el_demand.csv', index_col=0)
plt.figure(figsize=(10, 3))
sns.lineplot(el_demand, x=el_demand.index, y='el_demand')
plt.grid()
plt.title('Electric demand')
plt.ylabel("Electric demand [kWh/h]")
month_xticks(plt.gca())
energy_ylims(plt.gca())
plt.tight_layout()
plt.show()

th_demand = pd.read_csv('../Results/base-now/th_demand.csv', index_col=0)
plt.figure(figsize=(10, 3))
sns.lineplot(th_demand, x=th_demand.index, y='th_demand')
plt.grid()
plt.title('Thermal demand')
plt.ylabel("Heating demand [kWh/h]")
month_xticks(plt.gca())
energy_ylims(plt.gca())
plt.tight_layout()
plt.show()

total_demand = pd.read_csv('../Results/base-now/total_demand.csv', index_col=0)
plt.figure(figsize=(10, 3))
sns.lineplot(total_demand, x=total_demand.index, y='total_demand')
plt.grid()
plt.title('Total demand')
month_xticks(plt.gca())
energy_ylims(plt.gca())
plt.tight_layout()
plt.show()


def plot_objective_terms(scenarios):
    data = pd.DataFrame()
    for name, path in scenarios.items():
        costs = pd.read_csv(f"{path}/objective_terms.csv", index_col=0)
        costs = costs.transpose()
        costs.index = [name]

        data = pd.concat([data, costs], axis="rows")

    fig, ax = plt.subplots()
    data.plot(kind='bar', stacked=True, ax=ax)
    ax.set_ylabel("Cost [EUR]")
    ax.set_ylim(top=500000)
    for tick in ax.get_xticklabels():
        tick.set_rotation(0)
    fig.suptitle("Cost terms")
    fig.tight_layout()
    plt.show()


plot_objective_terms(scenarios)
