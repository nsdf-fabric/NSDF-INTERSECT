"""
File: constants.py
Authors: NSDF-INTERSECT Team
Description: Constants used across services.
License: BSD-3
"""

##############################
########## STATEFUL ##########
##############################

# FILES
RETRY_FILE = "retry.txt"

############################
########## CONFIG ##########
############################

# SCIENTIST_CLOUD
BUCKET_PATH = "utk"
BRAGG_PATH = "bragg_data"
TRANSITION_DATA_PATH = "transition_data"
NEXT_TEMPERATURE_DATA_PATH = "andie_data"

# DASHBOARD
MAX_BANKS = 6
INTERSECT_DASHBOARD_CONFIG = "INTERSECT_DASHBOARD_CONFIG"  # env variable holds the path to dashboard file configuration

# SERVICE
INTERSECT_SERVICE_CONFIG = "INTERSECT_SERVICE_CONFIG"  # env variable holds the path to service file configuration
