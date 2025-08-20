import os, pandas as pd
BASE = os.path.dirname(__file__)
DATA_RAW = os.path.join(BASE, "..", "data", "raw")

test = pd.read_csv(os.path.join(DATA_RAW, "test.csv")).fillna("")
