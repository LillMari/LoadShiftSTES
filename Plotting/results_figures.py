import matplotlib.pyplot as plt
import numpy as np
from matplotlib import ticker
import pandas as pd
import seaborn as sns

no_lec = {'name': 'no_lec', 'color': 'silver', 'alpha': 1}
base = {'name': 'BaseScenario', 'color': 'green', 'alpha': 1}
stes = {'name': 'stes', 'color': 'royalblue', 'alpha': 1}
stes_lec = {'name': 'stes_lec', 'color': 'tomato', 'alpha': 1}
cases = [base, stes, stes_lec]


def month_xticks(ax):
    months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    month_hours = [m * 24 for m in months]
    month_hours_cum = [sum(month_hours[:x]) for x in range(12)]
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    ax.set_xticks(month_hours_cum)
    ax.set_xticklabels(month_names)


def plot_linelosses():
    no_lec_line_loss = pd.read_csv(f'../Results/no_lec/powerflow/line_summaries.csv')['active_line_losses_mw']

    for case in cases:
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


def plot_lineloss_diff(case):
    base_line_loss = pd.read_csv(f'../Results/no_lec/powerflow/line_summaries.csv')['active_line_losses_mw']
    for case in cases:
        line_loss = pd.read_csv(f'../Results/{case["name"]}/powerflow/line_summaries.csv')['active_line_losses_mw']
        loss_diff = line_loss - base_line_loss
        plt.figure(figsize=(10, 5))
        plt.plot(loss_diff*1000, label=case['name'], color=case['color'])
        month_xticks(plt.gca())
        plt.margins(x=0)
        plt.grid()
        plt.legend()
        plt.ylim(ymin=-5, ymax=27)
        plt.ylabel('Additional line losses [kWh/h]')
        plt.show()


def plot_duration_curve():

    plt.figure(figsize=(8, 4))
    for case in cases:
        load_imp = pd.read_csv(f'../Results/{case["name"]}/grid_import.csv', index_col=0)
        load_exp = pd.read_csv(f'../Results/{case["name"]}/grid_export.csv', index_col=0)
        load = load_imp['grid_import'] - load_exp['grid_export']
        load = load.sort_values(ascending=False, ignore_index=True)
        sns.lineplot(load, label=case['name'], color=case['color'])
    ax = plt.gca()
    length = (len(load)-1)
    ax.set_xticks(np.linspace(0, 1, 11) * length)
    ax.xaxis.set_major_formatter(ticker.PercentFormatter(xmax=length))
    plt.ylabel('Hourly consumption [MWh/h]')
    plt.xlabel('Percentage of year [%]')

    ax = plt.gca()
    plt.margins(x=0)
    plt.tight_layout()
    plt.grid()
    plt.show()


def main():
    plot_linelosses()
    plot_lineloss_diff('BaseScenario')
    plot_duration_curve()


if __name__ == '__main__':
    main()
