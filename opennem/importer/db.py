import logging
import re
from datetime import datetime
from pprint import pprint

from pydantic import BaseModel
from sqlalchemy.orm.session import make_transient

from opennem.core.loader import load_data
from opennem.db import engine, session
from opennem.db.initdb import init_opennem
from opennem.db.load_fixtures import load_fixtures
from opennem.db.models.opennem import Facility, Location, Revision, Station
from opennem.importer.mms import mms_import
from opennem.importer.registry import registry_import
from opennem.schema.opennem import StationSchema

logger = logging.getLogger(__name__)


def load_revisions(stations):
    pass


def create_revision(model):
    # s = session()

    # make_transient(model)

    clone = model.asdict(exclude_pk=True)
    # clone.pop("id")
    # model.fromdict(clone)

    # pylint: disable=no-member
    clone_model = Station().fromdict(clone)

    return clone_model


def get_schema_name(record: object) -> str:
    class_name = str(record.__class__.__name__)

    class_name = re.sub("Schema", "", class_name)

    class_name = class_name.lower()

    return class_name


def revision_factory(
    record: BaseModel, field_name: str, created_by: str, revision_data={}
) -> bool:
    s = session()

    field_type = get_schema_name(record)
    field_value = getattr(record, field_name)

    if not record.code:
        raise Exception("Require a code to create a revision")

    revision_lookup = (
        s.query(Revision)
        .filter(Revision.schema == field_type)
        .filter(Revision.code == record.code)
        .filter(Revision.data[field_name].as_string() == field_value)
        .one_or_none()
    )

    if revision_lookup:
        return True

    revision_data[field_name] = field_value

    revision = Revision(
        schema=field_type,
        code=record.code,
        created_by=created_by,
        data=revision_data,
    )

    s.add(revision)
    s.commit()

    return True


def load_revision(records, created_by="aemo.mms.202006"):
    logger.info("Running db test")
    s = session()

    s.query(Revision).delete()

    # all_stations = [i.code for i in s.query(Station.code).distinct()]
    # all_facilities = [i.code for i in s.query(Facility.code).distinct()]

    for station_record in records:
        station_model = (
            s.query(Station)
            .filter(Station.code == station_record.code)
            .one_or_none()
        )

        if not station_model:
            logger.info(
                f"New station {station_record.name} {station_record.code}"
            )

            # revision = Revision(
            #     schema="station",
            #     code=station_record.code,
            #     created_by=created_by,
            # )

            # revision.data = {
            #     "code": station_record.code,
            #     "network_name": station_record.network_name,
            # }
            revision_factory(station_record, "code", created_by)
            revision_factory(station_record, "name", created_by)
            revision_factory(station_record, "network_name", created_by)

            # s.add(revision)
            # s.commit()

        else:
            if station_model.name != station_record.name:
                revision_factory(station_record, "name", created_by)

            if station_model.network_name != station_record.network_name:
                revision_factory(station_record, "network_name", created_by)

        for facility in station_record.facilities:
            facility_model = (
                s.query(Facility)
                .filter(Facility.code == facility.code)
                .one_or_none()
            )

            if not facility_model:
                logger.info(
                    "New facility %s => %s", station_record.name, facility.code
                )

                revision_factory(facility, "code", created_by)
                revision_factory(facility, "code", created_by)


def db_test():
    mms = mms_import()

    load_revision(mms)


def registry_init():
    registry = registry_import()

    s = session()

    for station in registry:
        station_dict = station.dict(exclude={"id"})
        # pprint(station_dict)

        station_model = Station().fromdict(station_dict)
        station_model.approved = True
        station_model.approved_at = datetime.now()
        station_model.approved_by = "opennem.registry"
        station_model.created_by = "opennem.registry"

        for fac in station.facilities:
            f = Facility(
                **fac.dict(exclude={"id", "fueltech", "status", "network"})
            )

            f.network_id = fac.network.code

            if fac.fueltech:
                f.fueltech_id = fac.fueltech.code

            f.status_id = fac.status.code

            station_model.facilities.append(f)

        s.add(station_model)

    s.commit()


def test_revisions():
    registry = registry_import()
    # mms = mms_import()
    s = session()

    k = registry.get_code("KWINANA")

    station = Station(code=k.code, name=k.name, network_name=k.network_name,)
    s.add(station)
    s.commit()

    station_clone = station.asdict()
    station_clone.pop("id")

    pprint(station_clone)

    station = create_revision(station)

    station.location = Location(
        address1=k.location.address1,
        address2=k.location.address2,
        locality=k.location.locality,
        state=k.location.state,
        postcode=k.location.postcode,
    )

    s.add(station)
    s.commit()

    station = create_revision(station)

    station.name = "Kwinana Edited"

    s.add(station)
    s.commit()


def init():
    init_opennem(engine)
    logger.info("Db initialized")

    load_fixtures()
    logger.info("Fixtures loaded")

    registry_init()
    logger.info("Registry initialized")


if __name__ == "__main__":
    db_test()
