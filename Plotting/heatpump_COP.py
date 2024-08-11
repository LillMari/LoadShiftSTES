import matplotlib.pyplot as plt
import pandas as pd
from scipy.special import expit

# from sklearn.linear_model import LogisticRegression

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

# clf = LogisticRegression(C=1e5)

plt.figure()
plt.plot(temp_cop_co2_mitsu.keys(), temp_cop_co2_mitsu.values(), label='mitsu', marker='.')
plt.plot(temp_cop_co2_minetto.keys(), temp_cop_co2_minetto.values(), label='minetto', marker='.')
plt.plot(temp_cop_aa_barrett.keys(), temp_cop_aa_barrett.values(), label='barrett', ls='--', marker='.')
plt.legend()
plt.show()
