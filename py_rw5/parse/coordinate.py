"""
Dataclasses to represent coordinates
"""

import dataclasses
from decimal import Decimal
from functools import reduce


@dataclasses.dataclass
class Coordinate:
    """A single coordinate reading for a point"""

    northing: Decimal
    easting: Decimal
    elevation: Decimal


@dataclasses.dataclass
class AvgCoordinate:
    """Represents a group of coordinate readings for a single point"""

    coordinates: list[Coordinate] = dataclasses.field(default_factory=list)

    @property
    def avg(self):
        return Coordinate(
            northing=reduce(lambda a, b: a + b.northing, self.coordinates, Decimal(0))
            / len(self.coordinates),
            easting=reduce(lambda a, b: a + b.easting, self.coordinates, Decimal(0))
            / len(self.coordinates),
            elevation=reduce(lambda a, b: a + b.elevation, self.coordinates, Decimal(0))
            / len(self.coordinates),
        )
