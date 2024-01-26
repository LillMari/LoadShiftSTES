import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd


net_import = pd.read_csv('../Results/stes/grid_import.csv', index_col=0)
total_demand = pd.read_csv('../Results/stes/total_demand.csv', index_col=0)

plt.figure()
sns.lineplot(net_import, x=net_import.index, y='grid_import')
plt.show()

plt.figure()
sns.lineplot(total_demand, x=total_demand.index, y='total_demand')
plt.show()
