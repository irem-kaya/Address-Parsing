import pickle, os

BASE = os.path.dirname(__file__)             # .../scripts
DATA_RAW = os.path.join(BASE, "..", "data", "raw")

with open(os.path.join(DATA_RAW, "X.pkl"), "rb") as f:
    X = pickle.load(f)
with open(os.path.join(DATA_RAW, "y.pkl"), "rb") as f:
    y = pickle.load(f)
