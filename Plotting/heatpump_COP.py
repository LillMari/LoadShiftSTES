import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# https://www.mitsubishi-les.info/database/servicemanual/files/201803_ATW_DATABOOK.pdf
temp_cop_co2_mitsu = {2: 1.76,
                      7: 1.99,
                      12: 2.89,
                      15: 3.10,
                      20: 3.81}

# https://doi.org/10.1016/j.ijrefrig.2010.12.018
temp_cop_co2_minetto = {-5: 2.7,
                        0: 2.9,
                        5: 3.1,
                        10: 3.4,
                        15: 3.6,
                        20: 4.0,
                        25: 4.3}

# DOI: 10.1109/JPETS.2018.2810783
temp_cop_aa_barrett = {-13: 1.1,
                       -8: 1.4,
                       -3: 1.7,
                       2: 2.1,
                       7: 2.6,
                       12: 3.2,
                       17: 3.7,
                       22: 4.2}


# https://www.proffvarmepumper.no/varmepumpe/luft-til-luft-varmepumper/panasonic-nz35vke-72-kw/
temp_cop_aa_panasonic = {-7: 2.79,
                         -15: 2.50,
                         -20: 2.24,
                         -25: 1.91}

# https://ctc.no/produkter/luft-vann-varmepumper/ctc-ecoair-700m (manual)
temp_cop_aw_CTC_708M = {12: 8.71 / 1.82,
                        7: 6.96 / 1.72,
                        2: 5.66 / 1.62,
                        -7: 5.51 / 1.75,
                        -15: 4.13 / 1.62}

temp_cop_aw_CTC_712M = {12: 11.23 / 2.60,
                        7: 9.04 / 2.63,
                        2: 7.36 / 2.54,
                        -7: 7.11 / 2.08,
                        -15: 6.24 / 2.74}

# https://www.abkqviller.no/globalassets/inriver/resources/r521272-datablad-energietikett-nibe-s2125-12-smo.pdf
temp_cop_aw_nibe = {12: 5.87,
                    7: 5.12,
                    2: 3.83,
                    -7: 2.17}

temp_cop_aw_lg = {12: 6.56,
                  7: 4.80,
                  2: 3.10,
                  -7: 2.28}

# https://www.toshiba-aircon.co.uk/wp-content/uploads/2023/02/27019908_00_Riello_NXHM-018-030_EN_TechSheet_UK.pdf
temp_cop_aw_tosh1 = {35: 3.81,
                     20: 3.44,
                     15: 3.22,
                     12: 2.90,
                     7: 2.75,
                     2: 2.15,
                     -7: 1.18}

temp_cop_aw_panasonic = {7: 2.25,
                         -7: 1.64,
                         -15: 1.32}

# https: // doi.org / 10.1111 / jiec.12166
temp_cop_mattinen = {7: 3.2,
                     2: 2.8,
                     -7: 2.6,
                     -15: 2.2}


def empirical_cop_jesper(dT, T_out):
    """
    10.1016/j.rser.2020.110646
    For large-scale HP, og bruker ikke luft som heat source
    """
    a = 1.4480 * 1e12
    b = 88.730
    c = -4.9460
    d = 0
    return a * (dT + 2 * b) ** c * (T_out + b) ** d  # # Water-source


def find_cop_polynomial(cop_list):
    temp = []
    cop = []
    for cop_dict in cop_list:
        temp.append(list(cop_dict.keys()))
        cop.append(list(cop_dict.values()))
    # Flatten lists
    temp = [i for list_i in temp for i in list_i]
    cop = [i for list_i in cop for i in list_i]
    return np.polynomial.polynomial.Polynomial.fit(temp, cop, deg=2, domain=(-15, 30))


def european_cop(t_source, t_sink):
    # https://doi.org/10.1038/s41597-019-0199-y
    # TODO: skal ha en min temp diff på 15
    return {t: (0.85 * (6.08 - 0.09 * (t_sink - t) + 0.0005 * (t_sink - t) ** 2)) for t in t_source}


def carnot_cop(t_source, t_sink):
    # Carnot efficiency of 0.4
    return {t: 0.4 * (t_sink + 273)/(t_sink - t) for t in t_source}


def plot_cop_temp(temp_cop_dict, name, regression=False):
    plt.figure()
    plt.grid()
    plt.title(f'{name}')
    plt.ylabel('COP')
    plt.xlabel('Temperature [C]')
    plt.ylim(ymin=0, ymax=7)
    for temp_cop_list in temp_cop_dict:
        plt.plot(temp_cop_list.keys(), temp_cop_list.values(), label='', marker='.', lw=.5)
    if regression:
        xsamples = np.linspace(-15, 30)
        poly = find_cop_polynomial(temp_cop_dict)
        print(f'{name}: {poly.convert().coef}')
        x0, x1, x2 = poly.convert().coef
        plt.plot(xsamples, poly(xsamples), label=f'{x0:.4f} + {x1:.4f}x + {x2:.4f}x$^2$', lw=2)
        plt.legend()
        return poly
    plt.savefig(f'method_figures/cop_{name}.pdf')


temp_range = range(-15, 26)
t_sink_water = 60
t_sink_air = 30

datablad = [temp_cop_co2_mitsu, temp_cop_aa_panasonic, temp_cop_aw_CTC_708M, temp_cop_aw_CTC_712M, temp_cop_aw_nibe,
            temp_cop_aw_lg, temp_cop_aw_tosh1, temp_cop_aw_panasonic]

artikler = [temp_cop_co2_minetto, temp_cop_aa_barrett, temp_cop_mattinen]

european = [european_cop(t_source=temp_range, t_sink=t_sink_water),
            european_cop(t_source=temp_range, t_sink=t_sink_air)]

carnot = [carnot_cop(t_source=temp_range, t_sink=t_sink_water), carnot_cop(t_source=temp_range, t_sink=t_sink_air)]

datablad_reg = plot_cop_temp(datablad, 'datablad', regression=True)
artikler_reg = plot_cop_temp(artikler, 'artikler', regression=True)

xsamples = np.linspace(-15, 30)
plt.figure(figsize=(10, 5))
plt.title('Ulike COP-metoder')
plt.ylim(ymin=1, ymax=5)
plt.plot(xsamples, datablad_reg(xsamples), label='Datablad')
plt.plot(xsamples, artikler_reg(xsamples), label='Artikler')
plt.plot(european[0].keys(), european[0].values(), label='Europa a-w', ls='--')
plt.plot(european[1].keys(), european[1].values(), label='Europa a-a', ls=':')
plt.plot(carnot[0].keys(), carnot[0].values(), label='Carnot a-w', ls='--')
plt.plot(carnot[1].keys(), carnot[1].values(), label='Carnot a-a', ls=':')
plt.legend()
plt.xlabel('Temperature [C]')
plt.ylabel('COP')
plt.grid()

plt.show()
