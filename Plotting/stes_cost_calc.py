import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression

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
# 'Anneberg': [165414.83, 60000],
# 'Andalucia': [154826.1, 18000],

stes_cost = pd.DataFrame.from_dict(stes_cost_volume, orient='index',
                                   columns=['Investment cost [€]', 'Ground volume [m3]'])

lr = LinearRegression()
x = stes_cost['Ground volume [m3]'].values.reshape(-1, 1)
y = stes_cost['Investment cost [€]'].values.reshape(-1, 1)
lr.fit(x, y)

m = lr.coef_[0][0]  # STES capacity cost
b = lr.intercept_[0]  # STES investment cost
fig, ax = plt.subplots(figsize=(6, 4))
sns.regplot(stes_cost, x=f'Ground volume [m3]', y='Investment cost [€]', ax=ax)
ax.set_xlabel(f'Ground volume [m$^3$]')
ax.lines[0].set_label(f'{m:.1f}' + r'$\frac{€}{m^3}$ x +' + f'{b/1000:.0f}' + r'$\cdot 10^3 €$')
ax.legend(loc='upper left')
ax2 = ax.twiny()
volume_to_energy = lambda v: 20 * v
ax2.set_xlim(map(volume_to_energy, ax.get_xlim()))
ax2.set_xlabel("Estimated ground heat capacity [kWh]")
fig.tight_layout()
plt.savefig('method_figures/BTES_investment_cost.pdf')
plt.show()
