Experiment 1: Ran on corn_earworm
---------------------------------

* Used class=0 as background point.
* Used worldclim average from 1970-2000.
* Used crop data.
* No feature tuning. Kept all bioclim variable.
* Calulcated sample weight for both background and presence point.
* Use checkerboard split to get train and test.
* Train and test set size are equal. ~37k samples in each.
* Unweighted checkerboard AUC score: 0.646
  Weighted checkerboard AUC score: 0.589
* Model performing better than random mode.
* Didn't tested on how the projection will look for future climate conditions.
* After removing uncorr variable, we only have 10 bioclim variable.
* Updated AUC score:
* Unweighted checkerboard AUC score: 0.624
  Weighted checkerboard AUC score: 0.608

![1727967438917](image/track_results/1727967438917.png)
