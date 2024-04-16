import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from modelbuilder import extract_load_profile


months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
month_hours = [m*24 for m in months]
month_hours_cum = [sum(month_hours[:x]) for x in range(12)]
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def month_xticks(ax):
    ax.set_xticks(month_hours_cum)
    ax.set_xticklabels(month_names)


def plot_el_th_demand_profile():
    el_demand, th_demand = extract_load_profile(1743)

    plt.figure()
    plt.plot(el_demand + th_demand)
    plt.grid()
    plt.title("El + Th")
    month_xticks(plt.gca())
    plt.show()

    plt.figure()
    plt.plot(th_demand)
    plt.grid()
    plt.title("Th")
    month_xticks(plt.gca())
    plt.show()

    plt.figure()
    plt.plot(el_demand)
    plt.grid()
    plt.title("El")
    month_xticks(plt.gca())
    plt.show()

    return el_demand, th_demand


def plot_spot_price(filename):
    hist_spot_price = pd.read_csv(filename, index_col=0) * 1e-3
    plt.figure(figsize=(8, 4))
    plt.plot(hist_spot_price.iloc[:, 0])
    plt.grid()
    plt.title(f"Historic spot price {filename}")
    month_xticks(plt.gca())
    plt.ylabel('Spot price [€/kWh]')
    plt.show()

    # Also plot a week
    # week = 10
    # plt.figure()
    # plt.plot(hist_spot_price.iloc[week*24*7:(week+1)*24*7, 0])
    # plt.ylabel('Spot price [€/kWh]')
    # plt.title(f"Historic spot price, week {week+1}")
    # plt.grid()
    # plt.show()


if __name__ == '__main__':
    plot_spot_price("Historic_spot_prices/spot_price_2019.csv")
    plot_spot_price("Historic_spot_prices/spot_price.csv")
    plot_spot_price("Framtidspriser/future_spot_price.csv")
    plot_spot_price("Framtidspriser/future_spot_price_NVE.csv")

