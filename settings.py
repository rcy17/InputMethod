import os

import models

smooth = float(os.environ.get('INPUT_METHOD_SMOOTH', 0.8))
smooth_1 = float(os.environ.get('INPUT_METHOD_SMOOTH_1', 0.1))
smooth_2 = float(os.environ.get('INPUT_METHOD_SMOOTH_2', 0.2))
input_file = os.environ.get('FILE_IN', 'input/in1.txt')
answer_file = os.environ.get('FILE_ANS', 'output/ans1.txt')
model_class = models.PinyinBinaryModel if 'USE_BINARY_MODEL' in os.environ else models.TrigramModel
candidates = 20
occurrence_bound = 5
key = os.environ.get('FILE_KEY', '2016')
warning = False
debug = False
