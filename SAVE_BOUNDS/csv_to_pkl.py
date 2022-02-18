import pandas as pd
import time

from utils import replace_extension

AGE_MIN=1
AGE_MAX=101

col_names=['structure'] + [f'age_{i}_{suffixe}' for i in range(AGE_MIN, AGE_MAX+1) for suffixe in ['lower', 'upper']]

for filename in ["female_vb_bounds.csv", "male_vb_bounds.csv", "average_vb_bounds.csv"]:
    pf = pd.read_csv(filename, sep=";", names=col_names)
    pf.to_pickle(replace_extension(filename, ".csv", ".pkl"))

