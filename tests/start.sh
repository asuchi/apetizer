#/bin/sh
virtualenv .
source bin/activate
jupyter notebook --config './jupyter_notebook_config.py'