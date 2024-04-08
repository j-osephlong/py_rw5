"""
Defines the state of a the pseudo Rw5 machines at a specific point in time
"""

import dataclasses
from decimal import Decimal


@dataclasses.dataclass
class MachineState:
    """
    Defines the state of a the pseudo Rw5 machines at a specific point in time
    """

    instrument_height: Decimal | None = None
    rod_height: Decimal | None = None
    backsight_angle: tuple[int, int, int] | None = None
    backsight_coord: str | None = None
