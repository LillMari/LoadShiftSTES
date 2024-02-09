import os.path

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd


months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
month_hours = [m*24 for m in months]
month_hours_cum = [sum(month_hours[:x]) for x in range(12)]
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def month_xticks(ax):
    ax.set_xticks(month_hours_cum)
    ax.set_xticklabels(month_names)


def plot_run(name, folder):
    tot_import = pd.read_csv(f'{folder}/grid_import.csv', index_col=0)
    tot_export = pd.read_csv(f'{folder}/grid_export.csv', index_col=0)
    net_import = tot_import['grid_import'] - tot_export['grid_export']

    plt.figure(figsize=(10, 3))
    sns.lineplot(net_import)
    plt.grid()
    plt.title(f'Net grid import, {name}')
    month_xticks(plt.gca())
    plt.show()

    if os.path.exists(f'{folder}/stes_soc.csv'):
        stes_soc = pd.read_csv(f'{folder}/stes_soc.csv', index_col=0)
        plt.figure(figsize=(10, 3))
        sns.lineplot(stes_soc)
        plt.grid()
        plt.title(f'STES soc, {name}')
        month_xticks(plt.gca())
        plt.show()


plot_run("base", "../Results/BaseScenario")
plot_run("stes", "../Results/stes")
plot_run("stes_lec", "../Results/stes_lec")

total_demand = pd.read_csv('../Results/stes/total_demand.csv', index_col=0)
plt.figure(figsize=(10, 3))
sns.lineplot(total_demand, x=total_demand.index, y='total_demand')
plt.grid()
plt.title('Total demand')
month_xticks(plt.gca())
plt.show()
