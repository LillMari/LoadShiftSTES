# Reference data set for a Norwegian medium voltage power distribution system

This article describes a reference data set for a representative Norwegian radial, medium voltage (MV) electric power distribution system operated at 22 kV. The data set is developed in the Norwegian research centre CINELDI and will in brief be referred to as the CINELDI MV reference system.  

Data for a real Norwegian distribution system were provided by a distribution grid company. The data have been anonymized and processed to obtain a simplified but still realistic grid model with 124 nodes. The data set consists of the following three parts:
1. *Grid data files* describe the base version of the reference system that represents the present-day state of the grid, including information about topology, electrical parameters, and existing load points.
2. *Load data files* comprise load demand time series for a year with hourly resolution and scenarios for the possible long-term development of peak load. These data describe an extended version of the reference system with information about possible new load points being added to the system in the future.
3. *Reliability data files* contain data necessary for carrying out reliability of supply analyses for the system. 

This work is funded by CINELDI - Centre for Intelligent Electricity Distribution, an 8-year Research Centre under the FME-scheme (Centre for Environment-friendly Energy Research, 257626/E20). The authors gratefully acknowledge the financial support from the Research Council of Norway and the CINELDI partners. 

This readme file gives an overview of the data files below, and more detailed documentation is available in the following data article:
I. B. Sperstad, O. B. Fosso, S. H. Jakobsen, A. O. Eggen, J. H. Evenstuen, and G. Kjølle, “Reference data set for a Norwegian medium voltage
power distribution system,” Data in Brief, 109025, 2023, doi: 10.1016/j.dib.2023.109025.


## Metadata:

Project and grant information:
Centre for Intelligent Electricity Distribution (FME CINELDI), Research Council of Norway Grant no. 257626, Work Package 6
	
Data owner:
SINTEF Energy Research
	
Classification:
Unrestricted 
	
Version:
2023-03-06
	
Digital Object Identifier (DOI):
10.5281/zenodo.7703070
	
Date published:
2023-03-06
	
Data format:
.csv (with copies of some data files in .xls format)
	
Language:
English
	
License:
CC BY 4.0
	
Contact person:
Iver Bakken Sperstad (iver.bakken.sperstad@sintef.no)


## Overview of the data set

The following files of the data set are available on Zenodo both as individual files and collected in the .zip file CINELDI_MV_reference_system_v_2023-03-06.zip.


### Overview of grid data files:

CINELDI_MV_reference_grid_base_bus.csv:
Bus (node) data on the MATPOWER case format, including peak load data for each of the nodes with load points

CINELDI_MV_reference_grid_base_bus_extra.csv:
Extra data fields for the load points (at a subset of the nodes), in addition to the bus data defined in the standard MATPOWER case format: ZIP load model parameters

CINELDI_MV_reference_grid_base_branch.csv:
Data for the branches (distribution lines) on the MATPOWER case format

CINELDI_MV_reference_grid_base_branch_extra.csv:
Extra data fields for the branch data, in addition to those defined in the standard MATPOWER case format: length, type, installation year, and type of location. (The rows have the same indexing as the branches in CINELDI_MV_reference_grid_base_branch.csv.)

CINELDI_MV_reference_grid_base_branch_pf_sol.csv:
Power flow for the base reference system. (The rows have the same indexing as the branches in CINELDI_MV_reference_grid_base_branch.csv.)

CINELDI_MV_reference_grid_base.xls:
Excel file with five spreadsheets containing the same grid data as in the .csv files

standard_underground_cable_types.csv:
Technical and economic data for relevant new underground cables in the reference system

standard_overhead_line_types.csv:
Technical and economic data for relevant new overhead lines in the reference system

standard_substation_types.csv:
Technical and economic data for relevant distribution substations that can be added to the reference system

distribution_line_types_in_reference_grid.csv:
Overview of line types present in the original grid data set


### Overview of load data files:

load_data_CINELDI_MV_reference_system.csv:
Set of 104 normalized hourly load demand time series 

mapping_loads_to_CINELDI_MV_reference_grid.csv:
Mapping of the load time series to nodes in the reference grid data set

share_load_per_customer_type.csv:
Share of load per customer type per load time series in the load data set

time_series_IDs_irregular_load.csv:
List of load time series IDs for load time series that have been defined as irregular in the sense of deviating from common and clearly recognizable seasonal, weekly, and diurnal patterns

time_series_IDs_primarily_residential.csv:
List of load time series IDs for load time series that are primarily residential

scenario_LEC_only.csv:
Scenario for long-term load development with only local energy communities (LECs) as new loads

scenario_LEC_fewer.csv:
Scenario for long-term load development with new LECs but fewer than in scenario LEC_only.csv

scenario_LEC_even_fewer.csv:
Scenario for long-term load development with new LECs but even fewer than in scenario LEC_fewer.csv

scenario_LEC_and_one_FCS.csv:
Scenario for long-term load development with new LECs and one new fast-charging station (FCS)

scenario_LEC_and_FCS.csv:
Scenario for long-term load development with new LECs and two new FCSs

	
### Overview of reliability data files:

CINELDI_MV_reference_system_switchgear.csv:
Data on the location and position of switchgear (disconnectors and circuit breakers) in the reference grid

CINELDI_MV_reference_system_reldata.csv:
Reliability data for lines in the reference grid. (Failure frequencies lambda are in units failures per year; outage times r and sectioning times are in units hours per failure.)

CINELDI_MV_reference_system_load_point.csv:
Load point data for reliability of supply calculations

reldata_for_component_types.csv:
Reliability data statistics for main types of distribution grid components. (Failure frequencies lambda are in units failures per year per 100 km or per 100 components; outage times r are in units hours per failure.)


## Version history

2022-10-13:
First submission

2023-03-06:
Added missing column installation_year in CINELDI_MV_reference_grid_base_branch_extra.csv, changed bus voltage limits from plus/minus 0.06 p.u. to plus/minus 0.05 p.u., corrected years in scenario_LEC_only.csv and scenario_LEC_fewer.csv, added reference to data article published Data in Brief, added specification of indexing and units in readme file.
