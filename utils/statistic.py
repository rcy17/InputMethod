import os
import sys
if os.getcwd().split('/')[-1] == 'utils':
    sys.path.append(os.path.abspath('..'))
else:
    sys.path.append(os.path.abspath('.'))
