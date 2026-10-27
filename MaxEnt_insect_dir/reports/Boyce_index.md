## Example: Step-by-Step Calculation of Boyce Index

Let's walk through an example where we calculate the Boyce Index step-by-step using assumptions for the presence points and predicted suitability values. We will assume:

- A small hypothetical landscape where the species is present in some locations.
- A MaxEnt model predicts suitability values for each location in this landscape.
- We bin the predicted suitability scores and compute the Boyce Index to assess the model's performance.

### Problem Setup:

#### 1. Landscape and Predicted Suitability:

Imagine we have 10 locations in our landscape, and the MaxEnt model provides a predicted suitability score for each location. These scores range from 0 (least suitable) to 1 (most suitable).

Here are the predicted suitability scores for these 10 locations:

| Location    | Suitability Score |
| ----------- | ----------------- |
| Location 1  | 0.1               |
| Location 2  | 0.2               |
| Location 3  | 0.3               |
| Location 4  | 0.4               |
| Location 5  | 0.5               |
| Location 6  | 0.6               |
| Location 7  | 0.7               |
| Location 8  | 0.8               |
| Location 9  | 0.9               |
| Location 10 | 1.0               |

These scores tell us how likely each location is suitable for the species based on the environmental factors used in the model.

#### 2. Observed Presence Points:

Now, let's assume that the species has been observed at some locations. These are the presence points:

- Species observed at locations: 3, 7, 8, 9

So, the observed presence points correspond to locations with the following suitability scores:

| Location   | Suitability Score |
| ---------- | ----------------- |
| Location 3 | 0.3               |
| Location 7 | 0.7               |
| Location 8 | 0.8               |
| Location 9 | 0.9               |

The goal is to calculate the Boyce Index to determine whether the model assigns higher suitability scores to these locations where the species has actually been observed.

### Step-by-Step Calculation of Boyce Index:

#### Step 1: Binning the Predicted Suitability Scores

We'll divide the predicted suitability scores into bins. For simplicity, let's use 3 bins:

- **Bin 1 (Low suitability)**: 0.0 - 0.33
- **Bin 2 (Moderate suitability)**: 0.33 - 0.66
- **Bin 3 (High suitability)**: 0.66 - 1.0

We now assign each location's predicted suitability score to one of these bins:

| Location    | Suitability Score | Bin |
| ----------- | ----------------- | --- |
| Location 1  | 0.1               | 1   |
| Location 2  | 0.2               | 1   |
| Location 3  | 0.3               | 1   |
| Location 4  | 0.4               | 2   |
| Location 5  | 0.5               | 2   |
| Location 6  | 0.6               | 2   |
| Location 7  | 0.7               | 3   |
| Location 8  | 0.8               | 3   |
| Location 9  | 0.9               | 3   |
| Location 10 | 1.0               | 3   |

Step 5: Calculate the Boyce Index
The Boyce Index is calculated using the Spearman rank correlation coefficient between the bin numbers and the observed-to-expected ratios (R(i)).

Here are the bin numbers and their corresponding ratios:

Bin	(R(i)) (Observed-to-Expected Ratio)
1	0.83
2	0
3	1.875
We now calculate the Spearman rank correlation coefficient between the bin numbers ([1, 2, 3]) and the observed-to-expected ratios ([0.83, 0, 1.875]).

In this case, we see that:

As we move from low to high suitability bins (from bin 1 to bin 3), the observed-to-expected ratio increases, which means the model predicts better habitat suitability in areas with more presences.
Step 6: Interpretation of the Boyce Index
A positive Boyce Index (closer to 1) means the model performs well: higher predicted suitability scores correspond to more observed presences.
A zero Boyce Index means the model performs no better than random.
A negative Boyce Index means the model performs poorly, predicting high suitability where the species is not present.
In this case, since the observed-to-expected ratios increase with the predicted suitability bins, the Boyce Index should be positive, indicating that the model predicts suitable habitats well.

#### Step 2: Calculate Observed Frequencies

The **observed frequency** represents the proportion of presence points in each bin.

- **Bin 1 (Low suitability)**: Location 3 has a presence, so the frequency is:

F_obs(1) = 1/4 = 0.25

- **Bin 2 (Moderate suitability)**: There are no presence points, so:

F_obs(2) = 0

- **Bin 3 (High suitability)**: Locations 7, 8, and 9 have presences, so:

F_obs(3) = 3/4 = 0.75

#### Step 3: Calculate Expected Frequencies

The **expected frequency** represents the proportion of total locations in each bin (ignoring where the species is present, just based on the landscape's suitability scores):

- **Bin 1 (Low suitability)**: Locations 1, 2, and 3 fall into this bin, so:

F_exp(1) = 3/10 = 0.3

- **Bin 2 (Moderate suitability)**: Locations 4, 5, and 6 fall into this bin, so:

F_exp(2) = 3/10 = 0.3

- **Bin 3 (High suitability)**: Locations 7, 8, 9, and 10 fall into this bin, so:

F_exp(3) = 4/10 = 0.4

#### Step 4: Calculate Observed-to-Expected Ratios

Now we calculate the ratio between the observed and expected frequencies for each bin:

- **Bin 1 (Low suitability)**:

R(1) = F_obs(1)/F_exp(1) = 0.25/0.3 = 0.83

- **Bin 2 (Moderate suitability)**:

R(2) = F_obs(2)/F_exp(2) = 0/0.3 = 0

- **Bin 3 (High suitability)**:

R(3) = F_obs(3)/F_exp(3) = 0.75/0.4 = 1.875

#### Step 5: Calculate the Boyce Index

The Boyce Index is calculated using the **Spearman rank correlation coefficient** between the bin numbers and the observed-to-expected ratios \(R(i)\).

Here are the bin numbers and their corresponding ratios:

| Bin | \(R(i)\) (Observed-to-Expected Ratio) |
| --- | ------------------------------------- |
| 1   | 0.83                                  |
| 2   | 0                                     |
| 3   | 1.875                                 |

We now calculate the **Spearman rank correlation coefficient** between the bin numbers \([1, 2, 3]\) and the observed-to-expected ratios \([0.83, 0, 1.875]\).

In this case, we see that:

- As we move from low to high suitability bins (from bin 1 to bin 3), the observed-to-expected ratio increases, which means the model predicts better habitat suitability in areas with more presences.

#### Step 6: Interpretation of the Boyce Index

- A **positive Boyce Index** (closer to 1) means the model performs well: higher predicted suitability scores correspond to more observed presences.
- A **zero Boyce Index** means the model performs no better than random.
- A **negative Boyce Index** means the model performs poorly, predicting high suitability where the species is not present.

In this case, since the observed-to-expected ratios increase with the predicted suitability bins, the Boyce Index should be positive, indicating that the model predicts suitable habitats well.

### Code Example for Calculation in Python:

You can implement this example in Python using the following code:

```python
import numpy as np
from scipy.stats import spearmanr

def boyce_index(predicted, observed, n_bins=3):
    bins = np.linspace(min(predicted), max(predicted), n_bins + 1)
    predicted_binned = np.digitize(predicted, bins)
    observed_binned = np.digitize(observed, bins)

    predicted_freq = np.zeros(n_bins)
    observed_freq = np.zeros(n_bins)

    for i in range(1, n_bins + 1):
        predicted_freq[i - 1] = np.sum(predicted_binned == i) / len(predicted)
        observed_freq[i - 1] = np.sum(observed_binned == i) / len(observed)

    return spearmanr(predicted_freq, observed_freq)[0]

# Predicted suitability scores for all locations
predicted = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])

# Observed presence suitability scores
observed = np.array([0.3, 0.7, 0.8, 0.9])

# Calculate Boyce Index
boyce_idx = boyce_index(predicted, observed)
print("Boyce Index:", boyce_idx)
```

In the paper: https://www.sciencedirect.com/science/article/pii/S0304380006002468?via%3Dihub

Create different bins based on max, and min value of prediction on background points.

In each window calculated fraction of P_i and E_i falls.

P_i --> Equation 2. It use the presence points.

E_i --> Equation 3. It use background points.
