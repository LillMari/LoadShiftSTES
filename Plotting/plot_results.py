import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd


tot_import_base = pd.read_csv('../Results/BaseScenario/grid_import.csv', index_col=0)
tot_export_base = pd.read_csv('../Results/BaseScenario/grid_export.csv', index_col=0)
net_import_base = tot_import_base['grid_import'] - tot_export_base['grid_export']

tot_import_stes = pd.read_csv('../Results/stes/grid_import.csv', index_col=0)
tot_export_stes = pd.read_csv('../Results/stes/grid_export.csv', index_col=0)
net_import_stes = tot_import_stes['grid_import'] - tot_export_stes['grid_export']

stes_soc = pd.read_csv('../Results/stes/stes_soc.csv', index_col=0)

total_demand = pd.read_csv('../Results/stes/total_demand.csv', index_col=0)


months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
month_hours = [m*24 for m in months]
month_hours_cum = [sum(month_hours[:x]) for x in range(12)]
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def month_xticks(ax):
    ax.set_xticks(month_hours_cum)
    ax.set_xticklabels(month_names)


plt.figure(figsize=(10, 3))
sns.lineplot(net_import_base)
plt.grid()
plt.title('Net grid import, base')
month_xticks(plt.gca())
plt.show()

plt.figure(figsize=(10, 3))
sns.lineplot(net_import_stes)
plt.grid()
plt.title('Net grid import, stes')
month_xticks(plt.gca())
plt.show()

plt.figure(figsize=(10, 3))
sns.lineplot(total_demand, x=total_demand.index, y='total_demand')
plt.grid()
plt.title('Total demand')
month_xticks(plt.gca())
plt.show()

plt.figure(figsize=(10, 3))
sns.lineplot(stes_soc)
plt.grid()
plt.title('STES soc')
month_xticks(plt.gca())
plt.show()
