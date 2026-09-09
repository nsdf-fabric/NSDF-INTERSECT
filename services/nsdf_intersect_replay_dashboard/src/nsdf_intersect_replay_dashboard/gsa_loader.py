"""
File: gsa_loader.py
Author: NSDF-INTERSECT Team
License: BSD-3
Description: The gsa file parser
"""

import numpy as np
import re
from collections import defaultdict
from typing import DefaultDict
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="nsdf-intersect-dashboard.log", encoding="utf-8", level=logging.INFO
)


def tof_to_d(tof: float, difc: float, difa: float = 0.0, tzero: float = 0.0) -> float:
    """
    Calculates d-spacing from time-of-flight.
    NOTE: This is a python version of the Mantd C++ code in the reference.


    References
        - https://github.com/mantidproject/mantid/blob/v6.12.0.1/Framework/Kernel/src/Unit.cpp#L696-L744
    Uses citardauq (quadratic backwards) formula.
        see https://en.wikipedia.org/wiki/Quadratic_formula#Square_root_in_the_denominator

    Attributes:
        tof (float): Time-of-flight
        difc (float): DIFC value
        difa (float): DIFA value (default = 0.)
        tzero (float): TZERO value (default = 0.)

    Returns:
        d-spacing value.
    """
    negative_constant_term = tof - tzero

    if difa == 0.0:
        return negative_constant_term / difc

    if tzero > tof:
        if difa > 0.0:
            err_msg = (
                "Cannot convert to d spacing because ",
                "tzero > time-of-flight and difa is positive. ",
                "Quadratic doesn't have a positive root",
            )
            raise ValueError(err_msg)

    # citardauq formula hides non-zero root if tof==tzero
    # which means that the constantTerm == 0
    if tof == tzero:
        if difa < 0.0:
            return -difc / difa
        else:
            return 0.0

    # general citarqauq equation
    sqrt_term = 1.0 + 4.0 * difa * negative_constant_term / (difc * difc)
    if sqrt_term < 0.0:
        err_msg = "Cannot convert to d spacing. Quadratic doesn't have real roots"
        raise ValueError(err_msg)

    # pick smallest positive root. Since difc is positive it just depends on sign of constantTerm
    # NOTE: constantTerm is generally negative
    if negative_constant_term < 0:
        # single positive root
        return negative_constant_term / (0.5 * difc * (1 - np.sqrt(sqrt_term)))
    else:
        # two positive roots. pick most negative denominator to get smallest root
        return negative_constant_term / (0.5 * difc * (1 + np.sqrt(sqrt_term)))


def parse_bank_info(line: str) -> list[float]:
    """
    Get the total flight path length (L1 + L2), two theta scattering angle, and DIFC from GSAS file.

    Attributes:
        line (str): Line to parse from GSAS file.

    Returns:
        Tuple of flight path length, two theta, and DIFC
    """

    regex = r"Total flight path\s+([0-9.]+)m, tth\s+([0-9.]+)deg, DIFC\s+([0-9.]+)"
    regex_match = re.search(regex, line)

    if regex_match:
        length = float(regex_match.group(1))
        two_theta = float(regex_match.group(2))
        difc = float(regex_match.group(3))

    return length, two_theta, difc


def load_gsa_file(path: str) -> DefaultDict:
    gsa_data = defaultdict()
    try:
        with open(path, "r") as f:
            tof, counts, errors = [], [], []
            bank_id = -1

            data = f.readlines()
            temp_difc = 1.0
            for line in data:
                if (
                    line.startswith("#")
                    or line.startswith("BANK")
                    or line.startswith("Monitor")
                    or line.startswith("Sample")
                ):
                    if "DIFC" in line:
                        temp_length, temp_two_theta, temp_difc = parse_bank_info(line)

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
                        d_value = tof_to_d(float(_data[0]), difc=temp_difc)
                        tof.append(d_value)
                        counts.append(float(_data[1]))
                        errors.append(float(_data[2]))

        # final bank
        if len(tof) != 0:
            gsa_data[bank_id] = np.asarray([tof, counts, errors])
    except Exception as e:
        logger.error(f"failed to load gsa workspace {path}: {e}")

    return gsa_data
