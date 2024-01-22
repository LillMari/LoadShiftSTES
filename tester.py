import pandas as pd


def hourly_power_volume_cost():
    """

    :return:
    """
    hours = range(8760)
    hour_of_day = [i % 24 for i in hours]
    day_of_week = [(i + 4) % 7 for i in hours]
    return hour_of_day, day_of_week


if __name__ == '__main__':
    a, b = hourly_power_volume_cost()
