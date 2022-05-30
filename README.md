# SimQuality Evaluation Scripts
This repository contains all the python evaluation scripts for the SimQuality-Suite (https://simquality.de/). It also produces all necessairy data for the SimQuality-Dashboard (https://github.com/hirseboy/SimQuality-Dashboard).

For each of the test cases a reference is defined and several statistival methods are compared with specific weight factors. In the end each Tools gets a SimQuality badge with regard to its agreement to the reference.

## Folder structure

* **data** - _Contains all the simulation data from the SimQuality test suite provided by the specified tools._
* **doc** - _Contains all the necessairy information about how the data has to be strucuted to be evaluated by the scripts._
* **scripts** - _Contains all the python scripts that are needed for the statistical evaluation of the tools._

## Evaluation procedure

The following batches can be awarded by the different tools:
If the SimQuality-Score is:
-  <b>> 90 %</b>: Green-Badge
-  <b>> 80 %</b>: Yellow-Badge
-  <b>< 80 %</b>: Red-Badge, failed
  
## Test cases 
  
* **TF 01** - _sun position model_
* **TF 02** - _solar radiation load_
* **TF 03** - _heat transmission_
* **TF 04** - _heat transmission/storage_
* **TF 05** - _ventilation_
* **TF 06** - _solar radiation + heat transmission/storage_
* **TF 07** - _window_
* **TF 08** - _internal loads_
* **TF 09** - _shading factos_
* **TF 10** - _conditioning_
* **TF 10** - _summer heat protection_
* **TF 12** - _complex building_
