#Boris 01/12/2021

- save_bounds.m: save for each volbrain structure, for age between 1 and 101, the upper and lower bounds
  It produces male_vb_bounds.csv & female_vb_bounds.csv & average_vb_bounds.csv

- files are then converted to pickle files :
  python3 csv_to_pkl.py

- *.pkl are then move in root directory :
 mv *.pkl ../




