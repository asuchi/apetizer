#!/usr/bin/env python
import os
import sys

def parse_command():
    os.environ.setdefault("DJANGO_ENV", "dev")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apetizer.settings")

 	# add cwd to path
    sys.path.append(os.getcwd())

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    parse_command()