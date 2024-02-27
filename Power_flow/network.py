import pandas as pd
import pandapower as pp
import numpy as np

from pandapower.timeseries import DFData, OutputWriter
from pandapower.timeseries.run_time_series import run_timeseries
from pandapower.control import ConstControl


def _read_grid(mpc_file):
    grid = pp.converter.from_mpc(mpc_file)

    # Give buses names, to recognize them even after merging and re-indexing
    grid.bus['name'] = 'MV' + (grid.bus.index + 1).astype(str)
    # Give loads names identical to the bus they belong to
    grid.load['name'] = 'MV' + (grid.load['bus'] + 1).astype(str)

    # Set voltage limits for voltage violation detection
    grid.bus['min_vm_pu'] = 0.95
    grid.bus['max_vm_pu'] = 1.05

    return grid


def _timeseries_id_to_bus_name(load_mapping_file):
    """
    Loads the mapping file between time_series_ID and bus_name
    Creates a dict from tsID -> bus name
    """
    mapping = pd.read_csv(load_mapping_file, sep=';')
    mapping.query('existing_load', inplace=True)  # Only keep existing_load=True
    mapping['bus_name'] = 'MV' + mapping['bus_i'].astype(str)
    return dict(zip(mapping.time_series_ID.astype(str), mapping.bus_name))


class Network:
    def __init__(self, mpc_file, load_file, load_mapping_file, lec_load_profiles):
        self.grid = _read_grid(mpc_file)

        # Create a mapping from time series ID to bus name
        self.ts_ID_to_bus_name = _timeseries_id_to_bus_name(load_mapping_file)

        # Ps and Qs are dataframes with bus name as column names
        # Describing the loads at hour intervals
        self.Ps, self.Qs = self._extract_loads(load_file)

        self._add_lec(lec_load_profiles)

    def _extract_loads(self, load_file):
        """
        Extracts load values from the load_file.
        The "time_series_ID" get replaced with bus_i, using the provided mapping file.

        :returns: (Ps, Qs) - dataframes where column names are bus_i,
                             and values are MW or Mvar
        """

        load_series = pd.read_csv(load_file, sep=';')
        # Ignore specific times, assume a year starting at Jan 01
        load_series = load_series.loc[:, load_series.columns != 'Time']

        # Only keep columns of the load_series DF we actually use in the mapping
        load_series = load_series[self.ts_ID_to_bus_name.keys()]

        # Columns should be named after their bus name, not the time series ID
        load_series.rename(columns=self.ts_ID_to_bus_name, inplace=True)

        max_loads = self.grid.load[['name', 'p_mw', 'q_mvar']].copy()
        max_loads.set_index('name', inplace=True)

        # At this point the load_series has one column for each bus
        # Multiply all the values in the column, by the bus' max load
        p_series = load_series.mul(max_loads['p_mw'])
        q_series = load_series.mul(max_loads['q_mvar'])

        return p_series, q_series

    def _add_lec(self, lec_load_profiles):
        for bus_i, load_profile in lec_load_profiles.items():
            bus_name = f'MV{bus_i}'
            Ps = load_profile
            Qs = load_profile * np.sqrt(1 - 0.95**2)  # pf = 0.95

            self.Ps[bus_name] = Ps
            self.Qs[bus_name] = Qs

            new_load = self.grid.load.iloc[0, :]
            new_load['name'] = bus_name
            new_load['bus'] = int(bus_i - 1)

            self.grid.load.loc[len(self.grid.load)] = new_load

    def _create_controllers(self):
        """
        Combines the time series for the loads.
        Creates controllers to every existing load in the net, using the datasources.
        Replaces any existing controllers on the loads.
        """

        ps_dfdata = DFData(self.Ps)
        qs_dfdata = DFData(self.Qs)

        for i in self.grid.load.index:
            name = self.grid.load['name'][i]
            ConstControl(self.grid, element='load', variable='p_mw', element_index=i,
                         data_source=ps_dfdata, profile_name=name, drop_same_existing_ctrl=True)
            ConstControl(self.grid, element='load', variable='q_mvar', element_index=i,
                         data_source=qs_dfdata, profile_name=name, drop_same_existing_ctrl=True)

    def _create_output_writer(self, time_steps):
        # Output write without a file output, storing everything in np arrays
        ow = OutputWriter(self.grid, time_steps, log_variables=[])

        # Bus voltages
        ow.log_variable('res_bus', 'vm_pu')

        # Line losses
        ow.log_variable('res_line', 'pl_mw')
        ow.log_variable('res_line', 'ql_mvar')
        return ow

    def run_time_series(self, time_steps):
        """
        Runs a year of powerflow analysis, hour by hour.

        Takes a PV generation time series as a dataframe.
        Each column must be named after a bus, and have 8760 rows.
        Only buses with loads can have pv generation

        :param time_steps: a range() of the hours of the year to run powerflow on

        :returns: a dictionary of different result structures
        """
        self._create_controllers()
        ow = self._create_output_writer(time_steps)
        run_timeseries(self.grid, time_steps)


