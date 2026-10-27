# Processed data release

Occurrence records after cleaning (positive detections with coordinates inside the contiguous US),
10 km greedy thinning in EPSG:5070 and removal of records on cells without climate data, with the
checkerboard fold (50 km cells; A_train = training colour, B_test = test colour) used by every model fit.
Records outside the established range were removed before thinning: the 71 Washington State spongy moth
detections (eradicated introductions) and the 23 root weevil records from Alabama, Georgia, Mississippi and
South Carolina, where the EPPO Global Database does not list the species as present.
`test_background.csv` is the fixed set of 20,000 uniformly sampled background points used to evaluate
every model (points on cells without climate data are dropped when the predictors are read).

Raw records: EDDMapS (stink bug, corn earworm, spongy moth, spotted lanternfly) and GBIF (Diaprepes root weevil);
see the manuscript, Section 2.2.1. Climate: WorldClim 2.1 (baseline 1970-2000) and CMIP6 ACCESS-CM2,
MPI-ESM1-2-HR, MIROC6, UKESM1-0-LL, EC-Earth3-Veg (2021-2040, 2041-2060, SSP1-2.6/2-4.5/3-7.0/5-8.5), 10 arc-min.

| species | records | train (A) | test (B) | on a grid line (unused) |
|---|---|---|---|---|
| Halyomorpha halys | 1412 | 676 | 734 | 2 |
| Helicoverpa zea | 719 | 351 | 366 | 2 |
| Lymantria dispar | 66 | 29 | 35 | 2 |
| Diaprepes abbreviatus | 170 | 90 | 78 | 2 |
| Lycorma delicatula | 664 | 334 | 328 | 2 |
