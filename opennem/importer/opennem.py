import os

from opennem.core import load_data_csv
from opennem.core.loader import load_data
from opennem.db.models.opennem import Facility, Station
from opennem.utils.log_config import logging

from .aemo_gi import gi_import
from .aemo_rel import rel_import
from .mms import mms_import

logger = logging.getLogger("opennem.importer")

RECORD_MODEL_MAP = {
    "STATION": Station,
    "FACILITY": Facility,
}


def opennem_import():
    """
        Reads the OpenNEM data source

    """

    opennem_records = load_data_csv("opennem.csv")

    for rec in opennem_records:
        logger.debug(rec)

        if "record_type" not in rec:
            raise Exception("Invalid CSV: No record_type")

        record_type = rec["record_type"]

        if record_type not in RECORD_MODEL_MAP:
            raise Exception(
                "Invalid record type: {} is not a valid record type".format(
                    record_type
                )
            )

        record_model = RECORD_MODEL_MAP[record_type]

    return record_model


def opennem_import():
    """
        This is the main method that overlays AEMO data and produces facilities

    """
    nem_mms = mms_import()
    nem_rel = rel_import()
    nem_gi = gi_import()
    registry = load_data("facility_registry.json")

    for mms_record in nem_mms:
        pass


def opennem_export():
    pass


if __name__ == "__main__":
    opennem_import()
