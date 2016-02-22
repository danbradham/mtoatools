# -*- coding: utf-8 -*-
import os
from functools import partial

tests_path = partial(os.path.join, os.path.dirname(__file__))

import sys
if 'mayapy' in sys.executable:
    from maya import standalone
    standalone.initialize(name='python')
