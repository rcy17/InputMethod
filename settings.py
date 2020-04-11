import os

smooth = float(os.environ.get('INPUT_METHOD_SMOOTH', 0.8))
smooth_1 = float(os.environ.get('INPUT_METHOD_SMOOTH_1', 0.1))
smooth_2 = float(os.environ.get('INPUT_METHOD_SMOOTH_2', 0.2))
candidates = 20
occurrence_bound = 5
key = os.environ.get('FILE_KEY', '2016')
warning = False
debug = False
