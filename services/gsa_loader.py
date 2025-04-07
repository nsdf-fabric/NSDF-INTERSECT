"""
File: gsa_loader.py
Author: NSDF-INTERSECT Team
License: BSD-3
Description: The gsa file parser
"""

import numpy as np
from collections import defaultdict
from typing import DefaultDict
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="nsdf-intersect-dashboard.log", encoding="utf-8", level=logging.INFO
)


def load_gsa_file(path: str) -> DefaultDict:
    gsa_data = defaultdict()
    try:
        with open(path, "r") as f:
            tof, counts, errors = [], [], []
            bank_id = -1

            data = f.readlines()
            for line in data:
                if (
                    line.startswith("#")
                    or line.startswith("BANK")
                    or line.startswith("Monitor")
                    or line.startswith("Sample")
                ):
                    if line.startswith("BANK"):
                        id = line.split()[1]
                        if bank_id == -1:
                            bank_id = int(id)
                            continue
                        gsa_data[bank_id] = np.asarray([tof, counts, errors])

                        bank_id = int(id)
                        tof.clear()
                        counts.clear()
                        errors.clear()
                    continue
                else:
                    _data = line.split()
                    if len(_data) == 3:
                        tof.append(float(_data[0]))
                        counts.append(float(_data[1]))
                        errors.append(float(_data[2]))

        # final bank
        if len(tof) != 0:
            gsa_data[bank_id] = np.asarray([tof, counts, errors])
    except Exception as e:
        logger.error(f"failed to load gsa workspace {path}: {e}")

    return gsa_data
