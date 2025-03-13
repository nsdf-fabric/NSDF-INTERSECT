"""
File: constants.py
Authors: NSDF-INTERSECT Team
Description: Constants used across services.
License: BSD-3
"""

###############################
########## STATELESS ##########
###############################

BRAGG_DATA_VOLUME = "bragg_volume"  # scanned by dashboard (bragg plot)
TRANSITION_DATA_VOLUME = "transition_volume"  # scanned by dashboard (transition plot)
ANDIE_DATA_VOLUME = (
    "andie_volume"  # scanned by dashboard (ANDiE trace in transition plot)
)

##############################
########## STATEFUL ##########
##############################

# VOLUMES
SCIENTIST_CLOUD_VOLUME = "scientist_cloud_volume"  # scanned by storage service

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

# SCAN PERIODS
BRAGG_SCAN_PERIOD = 2
TRANSITION_SCAN_PERIOD = 2
STORAGE_SCAN_PERIOD = 30
SELECT_SCAN_PERIOD = 45

# DASHBOARD
MAX_BANKS = 6
