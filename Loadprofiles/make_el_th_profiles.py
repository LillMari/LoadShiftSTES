import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


def estimate_el_th_ratio(plot=False):
    temp = pd.read_csv('../Profiles/Norway/temperature_profile.csv')
    el_th_ratio = pd.read_csv('../PROFet/el_th_ratio.csv')

    temp_th_demand = pd.concat([temp['temperature [degC]'], el_th_ratio[['House', 'Apartment']]], axis=1)

    t_min = -15
    t_max = 30

    poly_house = np.polynomial.Polynomial.fit(list(temp_th_demand['temperature [degC]']),
                                              list(temp_th_demand['House']), deg=2, domain=(t_min, t_max))
    poly_apartment = np.polynomial.Polynomial.fit(list(temp_th_demand['temperature [degC]']),
                                                  list(temp_th_demand['Apartment']), deg=2, domain=(t_min, t_max))

    coeffs = {'house': poly_house.convert().coef, 'apartment': poly_apartment.convert().coef}

    if plot:
        plt.figure(figsize=(10, 5))
        sns.scatterplot(data=temp_th_demand, x='temperature [degC]', y='House', label='House')
        sns.scatterplot(data=temp_th_demand, x='temperature [degC]', y='Apartment', label='Apartment')
        xsamples = np.linspace(t_min, t_max)
        x0, x1, x2 = coeffs['house']
        plt.plot(xsamples, poly_house(xsamples), label=f'House: {x0:.4f} + {x1:.4f}x + {x2:.4f}x$^2$', lw=2)
        x0, x1, x2 = coeffs['apartment']
        plt.plot(xsamples, poly_apartment(xsamples), label=f'Apartment: {x0:.4f} + {x1:.4f}x + {x2:.4f}x$^2$', lw=2,
                 color='sienna')
        plt.legend()
        plt.xlabel('Temperature [C]')
        plt.ylabel('Demand ratio $\\frac{el}{th + el}$')
        plt.savefig('../Plotting/preliminary_plots/general_el_th_ratio.pdf')
        plt.grid()
        plt.show()

    return coeffs


def estimate_thermal_demand(el_load, temperature):
    coeffs = estimate_el_th_ratio()
    coeff = coeffs['apartment']
    el_ratio = pd.Series([coeff[0] + coeff[1] * x + coeff[2] * x**2 if x <= 23 else 0.82 for x in temperature])

    total_demand = el_load.div(el_ratio, axis='index')
    th_ratio = 1 - el_ratio
    th_load = total_demand.mul(th_ratio, axis='index')
    return th_load


def main():
    country = 'Spain'
    el_load = pd.read_csv(f'../Profiles/{country}/el_demand.csv', index_col=0)
    temperature = pd.read_csv(f'../Profiles/{country}/temperature_profile.csv')['temperature [degC]']
    th_load = estimate_thermal_demand(el_load, temperature)

    el_load = el_load.rename(columns={col: str(i) for i, col in enumerate(el_load.columns)})
    th_load = th_load.rename(columns={col: str(i) for i, col in enumerate(th_load.columns)})

    el_load.to_csv(f'../Profiles/{country}/el_demand.csv')
    th_load.to_csv(f'../Profiles/{country}/th_demand.csv')


if __name__ == '__main__':
    main()
    # estimate_el_th_ratio(plot=True)
