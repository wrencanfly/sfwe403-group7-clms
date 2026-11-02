#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clms.settings')
from django.core.management import execute_from_command_line
execute_from_command_line(sys.argv)
