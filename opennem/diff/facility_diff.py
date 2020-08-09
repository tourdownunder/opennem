"""
    Parse current and v3 facilities registries and take a diff.


"""

import csv
import json
import logging
from datetime import timedelta
from operator import itemgetter
from pprint import pprint

from opennem.utils import logging

logger = logging.getLogger("opennem.diff")
logger.setLevel(logging.DEBUG)

logging.basicConfig(level=logging.INFO)


def normalize_states(state):
    state = state.lower()

    if state == "commissioned":
        return "operating"

    if state == "decommissioned":
        return "retired"

    return state


def normalize_regions(region):
    if region == "WA":
        return "WA1"

    return region


def run_diff():
    logger.info("Running facility diff")

    with open("opennem/db/fixtures/facility_registry.json") as fh:
        fac_current = json.load(fh)

    remapped = []

    for k, v in fac_current.items():
        for duid, fac in v["duid_data"].items():
            i = [
                v["display_name"] or "",
                k,
                normalize_regions(v["region_id"]) or "",
                normalize_states(v["status"]["state"]),
                duid or "",
                fac["fuel_tech"] if "fuel_tech" in fac else "",
                fac["registered_capacity"]
                if "registered_capacity" in fac
                else 0,
            ]
            remapped.append(i)

    remapped = sorted(remapped, key=itemgetter(2, 0, 4, 6))

    with open("data/facility_diff/facilities_current.csv", "w") as fh:
        csvwriter = csv.writer(fh)
        for line in remapped:
            csvwriter.writerow(line)

    with open("data/facility_diff/au_facilities.json") as fh:
        fac_v3 = json.load(fh)

    fac_v3 = fac_v3["features"]
    remapped = []

    for f in fac_v3:
        for fac in f["properties"]["duid_data"]:
            i = [
                f["properties"]["name"] or "",
                # fac["duid"],
                f["properties"]["oid"],
                f["properties"]["station_code"] or "",
                normalize_regions(f["properties"]["network_region"]) or "",
                fac["status"].lower(),
                fac["duid"] or "",
                fac["fuel_tech"] if "fuel_tech" in fac else "",
                fac["registered_capacity"]
                if "registered_capacity" in fac
                else 0,
            ]
            remapped.append(i)

    remapped = sorted(remapped, key=itemgetter(3, 0, 5, 7))

    with open("data/facility_diff/facilities_v3.csv", "w") as fh:
        csvwriter = csv.writer(fh)
        for line in remapped:
            csvwriter.writerow(line)