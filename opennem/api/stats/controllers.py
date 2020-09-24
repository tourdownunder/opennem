from datetime import datetime
from itertools import groupby
from operator import itemgetter
from typing import List, Optional

import pytz
from sqlalchemy.orm import Session

from opennem.core.time import human_to_interval
from opennem.db.models.opennem import FacilityScada, Station

from .schema import OpennemData, OpennemDataHistory


def stats_factory(scada: List[FacilityScada]) -> Optional[OpennemData]:
    if len(scada) < 1:
        return None

    network_timezone = pytz.timezone(scada[0].network.timezone)

    dates = [s.trading_interval for s in scada]
    start = min(dates)
    end = max(dates)

    network = scada[0].network.code
    interval = scada[0].network.interval_size

    # pluck the list
    data = [
        {
            k: v
            for k, v in scada_record
            if k in ["trading_interval", "generated"]
        }
        for scada_record in scada
    ]

    data_grouped = {}

    for key, v in groupby(data, itemgetter("trading_interval")):
        if key not in data_grouped:
            data_grouped[key] = 0.0

        data_grouped[key] = float(sum([i["generated"] for i in list(v)]))

    history = OpennemDataHistory(
        start=start.astimezone(network_timezone),
        last=end.astimezone(network_timezone),
        interval="{}m".format(str(interval)),
        data=list(data_grouped.values()),
    )

    data = OpennemData(
        network=network, data_type="power", units="MW", history=history
    )

    return data


def station_attach_stats(station: Station, session: Session) -> Station:
    since = datetime.now() - human_to_interval("7d")

    facility_codes = list(set([f.code for f in station.facilities]))

    stats = (
        session.query(FacilityScada)
        .filter(FacilityScada.facility_code.in_(facility_codes))
        .filter(FacilityScada.trading_interval >= since)
        .order_by(FacilityScada.facility_code)
        .order_by(FacilityScada.trading_interval)
        .all()
    )

    for facility in station.facilities:
        facility_power = list(
            filter(lambda s: s.facility_code == facility.code, stats)
        )

        facility.scada_power = stats_factory(facility_power)

    return station
