###############################
########## STATELESS ##########
###############################

BRAGG_VOLUME = "bragg_volume"  # scanned by dashboard (bragg plot)

##############################
########## STATEFUL ##########
##############################

# VOLUMES
STATE_VOLUME = "state"  # scanned by dashboard (transition, next temperature)
SCIENTIST_CLOUD_VOLUME = "scientist_cloud_volume"  # scanned by storage service

# FILES
TRANSITION_DATA_FILE = "transition_data.txt"
ANDIE_DATA_FILE = "andie_data.txt"
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

# PLOTS
BRAGG = "BRAGG"
TRANSITION = "TRANSITION"
ANDIE = "ANDIE"
