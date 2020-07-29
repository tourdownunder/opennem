import logging
import re
from typing import Optional

from pydantic import BaseModel

from opennem.core.unit_single import facility_unit_numbers_are_single

logger = logging.getLogger(__name__)

__is_number = re.compile(r"^\d+$")

__is_single_number = re.compile(r"^\d$")

__is_unit_alias = re.compile(r"([A-Z|a-z]{1,6})")

__is_unit_alias_forced = re.compile(r"([A-Z|a-z]{1,6}\d{1,2})")

__unit_range_parse = re.compile(r"(\d+)\-(\d+)")


class UnitSchema(BaseModel):
    # The unit id
    id: int = 1

    # The unit alias
    alias: Optional[str] = None

    # The number of units
    number: int = 1

    capacity: Optional[int]


is_number = lambda v: bool(re.match(__is_number, v))

is_single_number = lambda v: bool(re.match(__is_single_number, v))

# Has a unit alias like A or GT
unit_has_alias = lambda v: bool(re.search(__is_unit_alias, v))

unit_has_alias_forced = lambda v: bool(re.search(__is_unit_alias_forced, v))

strip_whitespace = lambda v: str(re.sub(r"\s+", "", v.strip()))


def parse_unit_duid(unit_input: str, unit_duid: str):
    return parse_unit_number(
        unit_input, facility_unit_numbers_are_single(unit_duid)
    )


def parse_unit_number(unit_input: str, force_single: bool = False):
    """
        Parses unit number string into a UnitSchema model

        force_single is a hack for units like Hallett where "GT 2-4" means
        unit alias GT2-4 rather than alias GT with id 2 and 2 units
    """
    unit_id = 1
    unit_no = 1
    unit_alias = None

    has_alias = False

    # Normalize to string
    if type(unit_input) is not str:
        unit_input = str(unit_input)

    # Strip whitespace and capitalize
    unit_input = strip_whitespace(unit_input)
    unit_input = unit_input.upper()

    # @TODO handle the silly multi unit lines
    if "," in unit_input:
        uc = unit_input.split(",")

    if force_single and unit_has_alias_forced(unit_input):
        has_alias = True

        # extract the unit alias
        unit_alias_search = re.search(__is_unit_alias_forced, unit_input)

        if unit_alias_search and unit_alias_search.lastindex == 1:
            unit_alias = unit_alias_search.group(1)

        if not unit_alias or not type(unit_alias) is str:
            raise Exception(
                "Error extracting alias from {}: Got {}".format(
                    unit_input, unit_alias
                )
            )

        # remove the unit alias
        unit_input = re.sub(r"[A-Za-z]{1,6}\d{1,2}\-", "", unit_input)

    if not has_alias and unit_has_alias(unit_input):
        has_alias = True

        # extract the unit alias
        unit_alias_search = re.search(__is_unit_alias, unit_input)

        if unit_alias_search and unit_alias_search.lastindex == 1:
            unit_alias = unit_alias_search.group(1)

        if not unit_alias or not type(unit_alias) is str:
            raise Exception(
                "Error extracting alias from {}: Got {}".format(
                    unit_input, unit_alias
                )
            )

        # remove the unit alias
        unit_input = re.sub(r"[A-Za-z\ ]", "", unit_input)

    # Simple single number matches
    if is_number(unit_input):
        unit_id = int(unit_input)

    # Range matches (ex. 1-50)
    unit_range_match = re.search(__unit_range_parse, unit_input)

    if unit_range_match and unit_range_match.lastindex == 2:
        unit_id = int(unit_range_match.group(1))
        unit_max = int(unit_range_match.group(2))

        if unit_max < unit_id:
            raise Exception(
                "Invalid max unit number {} on id {} for range {}".format(
                    unit_max, unit_id, unit_input
                )
            )

        unit_no = unit_max - unit_id + 1

    unit = UnitSchema(id=unit_id, number=unit_no, alias=unit_alias,)

    return unit