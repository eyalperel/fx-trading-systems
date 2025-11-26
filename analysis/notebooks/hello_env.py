# notebooks/hello_env.py
import numpy as np
import pandas as pd
import matplotlib
import sys
print("python:", sys.version.split()[0])
print("numpy:", np.__version__)
print("pandas:", pd.__version__)
print("matplotlib:", matplotlib.__version__)
print("sample:", np.arange(5).tolist())
