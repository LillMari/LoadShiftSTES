import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd

NOK2024_TO_EUR = 0.087

def month_xticks(ax):
    months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    month_hours = [m * 24 for m in months]
    month_hours_cum = [sum(month_hours[:x]) for x in range(12)]
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    ax.set_xticks(month_hours_cum)
    ax.set_xticklabels(month_names)


def find_week_number(start_day, profile):
    for t in range(len(profile)):
        profile.loc[t, 'week'] = int(((t//24) + start_day) % 7)
    return profile


def plot_weekly_el_th_demand():
    el_demand = pd.read_csv('../Results/stes/el_demand.csv', index_col=0)
    th_demand = pd.read_csv('../Results/stes/th_demand.csv', index_col=0)

    el_demand = find_week_number(4, el_demand)
    th_demand = find_week_number(4, th_demand)


def plot_pv_profile(save=False):
    pv_profile = pd.read_csv('../PV_profiler/pv_profil_oslo_2014.csv', skiprows=3)['electricity']  # kW/kWp
    plt.figure(figsize=(8, 4))
    sns.lineplot(pv_profile*10)
    month_xticks(plt.gca())
    plt.ylabel('PV production [kWh/h]')
    plt.xlabel('Time of year')
    plt.ylim(ymin=0, ymax=9)
    plt.margins(x=0)
    plt.tight_layout()
    plt.grid()
    if save:
        plt.savefig('method_figures/pv_profile.pdf')
    plt.show()


def plot_grid_rent(save=False):
    x = [0, 2, 2, 5, 5, 10, 10, 15, 15, 20]
    y_nok = [120, 120, 190, 190, 305, 305, 420, 420, 535, 535]
    y = [i*NOK2024_TO_EUR for i in y_nok]

    x2 = np.linspace(0, 20, 5)
    y2 = x2 * 24.65 * NOK2024_TO_EUR + 95.39 * NOK2024_TO_EUR

    plt.figure(figsize=(8, 5))
    plt.ylim(0, 50)
    plt.plot(x, y, label='Elvia\'s step model')
    plt.plot(x2, y2, label=f'Regression line: {24.65 * NOK2024_TO_EUR:.2f}x + {95.39 * NOK2024_TO_EUR:.2f}')
    plt.xlabel('Maximum hourly power use [kWh/h]')
    plt.ylabel('Fixed fee [€/month]')
    plt.tight_layout()
    plt.margins(x=0)
    plt.gca().set_xticks([0, 2, 5, 10, 15, 20])
    plt.grid()
    plt.legend()
    if save:
        plt.savefig('method_figures/step_model.pdf')
    plt.show()


def main():
    # plot_weekly_el_th_demand()
    # plot_pv_profile(save=True)
    plot_grid_rent(save=True)


if __name__ == '__main__':
    main()
