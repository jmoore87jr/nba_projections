import numpy as np 
import pandas as pd 
import sklearn 

df = pd.read_csv('player-seasons.csv').dropna().drop('Unnamed: 0', axis=1)

print(df.head(10))
print(df.shape)