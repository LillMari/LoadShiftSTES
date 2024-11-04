import numpy as np
import pandas as pd
from modelbuilder import ModelBuilder

NOK2024_TO_EUR = 0.087

""" NORWAY """
class NorwayModelbuilder(ModelBuilder):
    def __init__(self, *, country, enable_house_hp, enable_stes):
        super().__init__(country=country, enable_house_hp=enable_house_hp, enable_stes=enable_stes)
        self.country = country

    def _get_hourly_power_volume_tariff(self, first_day_of_year=4):
        winter_day = .3954 * NOK2024_TO_EUR
        winter_night = .3209 * NOK2024_TO_EUR
        summer_day = .4825 * NOK2024_TO_EUR
        summer_night = .4075 * NOK2024_TO_EUR

        hourly_power_volume_tariff = np.zeros(shape=len(self.month_from_hour))

        for t, month in enumerate(self.month_from_hour):
            hour_in_day = t % 24
            day_in_week = ((t // 24) + first_day_of_year) % 7

            is_winter = month in [0, 1, 2]  # January - March
            is_weekday = day_in_week in range(0, 5)  # Mon - Fri
            is_daytime = hour_in_day in range(6, 22)  # 06:00 - 22:00

            if is_winter:
                if is_weekday and is_daytime:
                    hourly_power_volume_tariff[t] = winter_day
                else:
                    hourly_power_volume_tariff[t] = winter_night
            else:
                if is_weekday and is_daytime:
                    hourly_power_volume_tariff[t] = summer_day
                else:
                    hourly_power_volume_tariff[t] = summer_night
        volume_taxes = self._get_volume_taxes()
        return hourly_power_volume_tariff - volume_taxes

    def _get_volume_taxes(self):
        hourly_power_volume_tax = np.zeros(shape=len(self.month_from_hour))  # [EUR/kWh]

        # From https://www.elvia.no/nettleie/alt-om-nettleiepriser/nettleiepriser-for-privatkunder/
        winter_tax = 0.0951 * NOK2024_TO_EUR
        summer_tax = 0.1644 * NOK2024_TO_EUR

        for t, month in enumerate(self.month_from_hour):
            is_winter = month in [0, 1, 2]  # January - March
            hourly_power_volume_tax[t] = (winter_tax if is_winter else summer_tax)
        return hourly_power_volume_tax

    def _get_feed_in_tax(self):
        return -0.05 * NOK2024_TO_EUR  # [EUR/kWh]

    def _get_house_monthly_connection_base(self):
        return 95.39 * NOK2024_TO_EUR

    def _get_peak_individual_monthly_power_tariff(self):
        return 24.65 * NOK2024_TO_EUR

    def _get_vat(self):
        return 0.25


""" GERMANY """
class GermanyModelbuilder(ModelBuilder):
    def __init__(self, *, country, enable_house_hp, enable_stes):
        super().__init__(country=country, enable_house_hp=enable_house_hp, enable_stes=enable_stes)
        self.country = country

    def _get_hourly_power_volume_tariff(self, first_day_of_year=4):
        hourly_power_volume_tariff = np.zeros(shape=len(self.month_from_hour))  # [EUR/kWh]

        for t, month in enumerate(self.month_from_hour):
            hourly_power_volume_tariff[t] = 0.0559  # [EUR/kWh]
        return hourly_power_volume_tariff

    def _get_volume_taxes(self):
        hourly_power_volume_tax = np.zeros(shape=len(self.month_from_hour))  # [EUR/kWh]

        for t, month in enumerate(self.month_from_hour):
            hourly_power_volume_tax[t] = 0.0205  # [EUR/kWh]
        return hourly_power_volume_tax

    def _get_feed_in_tariff(self):
        return pd.DataFrame([0.082] * len(self.spot_price))

    def _get_peak_individual_monthly_power_tariff(self):
        return 22.24  # [EUR/kWh]

    def _get_vat(self):
        return 0.19


""" SPAIN """
class SpainModelbuilder(ModelBuilder):
    def __init__(self, *, country, enable_house_hp, enable_stes):
        super().__init__(country=country, enable_house_hp=enable_house_hp, enable_stes=enable_stes)
        self.country = country


    def _get_hourly_power_volume_tariff(self, first_day_of_year=4):
        hourly_power_volume_tariff = np.zeros(shape=len(self.month_from_hour))
        peak = 0.00135
        flat = 0.00042
        valley = 0.00006
        for t, month in enumerate(self.month_from_hour):
            hour_in_day = t % 24
            day_in_week = ((t // 24) + first_day_of_year) % 7

            is_weekend = day_in_week in range(6, 8)  # Fri - Sun
            is_peak = (hour_in_day in range(10, 14) or hour_in_day in range(18, 22))
            is_valley = hour_in_day in range(0, 8)

            if is_weekend or is_valley:
                hourly_power_volume_tariff[t] = valley
            elif is_peak:
                hourly_power_volume_tariff[t] = peak
            else:
                hourly_power_volume_tariff[t] = flat
        return hourly_power_volume_tariff

    def _get_volume_taxes(self):
        hourly_power_volume_tax = np.zeros(shape=len(self.month_from_hour))  # [EUR/kWh]

        for t, month in enumerate(self.month_from_hour):
            hourly_power_volume_tax[t] = 0.0511  # [per kWh]
        return hourly_power_volume_tax

    def _get_import_price(self):
        # Export price was on average 46% of import price + access tariff in 2018.
        # TODO: skal elavgift også regnes med?
        spot_price = pd.read_csv(f'Profiles/{self.country}/spot_price.csv', index_col=0) * 1e-3  # [EUR/kWh]
        return spot_price / 0.46 - self._get_hourly_power_volume_tariff()

    def _get_vat(self):
        return 0.21  # TODO: 10 for most residential consumers (?)

    def _get_electricity_bill_lb(self):
        return 0




