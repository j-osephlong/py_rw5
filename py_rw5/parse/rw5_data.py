from decimal import Decimal
from os import PathLike
from pathlib import Path

from py_rw5.parse.coordinate import AvgCoordinate, Coordinate
from py_rw5.parse.record import (
    GPSRecord,
    JobRecord,
    Rw5Record,
    SideshotRecord,
    StorePointRecord,
)


class Rw5Data:
    """
    Represents the data of an rw5 file
    """

    records: list[Rw5Record]
    rw5_path: PathLike
    rw5_encoding: str
    coordinates: dict[str, AvgCoordinate]
    """Dictionary of point names to avg coordinate classes"""
    point_occurrence_count: dict[str, int]
    """Dictionary of point names to # of occurrences"""

    def __init__(
        self, rw5_path: PathLike, rw5_encoding: str, records: list[Rw5Record]
    ) -> None:
        self.records = records
        self.rw5_path = rw5_path
        self.rw5_encoding = rw5_encoding
        self.coordinates = {}
        self.point_occurrence_count = {}
        self.process_coordinates()

    def __str__(self) -> str:
        _str = ""
        _str += f"Rw5 file {self.rw5_path}\n"
        for inst in self.records:
            _str += f"{str(inst)}\n"
        return _str

    @property
    def job_record(self):
        for record in self.records:
            if isinstance(record, JobRecord):
                return record
        raise ValueError("No job record.")

    def process_coordinates(self):
        """
        Create coordinate averages and keep track of occurrence counts
        """
        for record in self.records:
            point_name = None
            if isinstance(record, GPSRecord) or (
                isinstance(record, StorePointRecord) and not record.resection
            ):
                if record.PN not in self.coordinates:
                    self.coordinates[record.PN] = AvgCoordinate()

                # Average point coordinate
                self.coordinates[record.PN].coordinates.append(
                    Coordinate(
                        northing=record.N,
                        easting=record.E,
                        elevation=record.EL,
                    )
                )

                point_name = record.PN

            elif isinstance(record, SideshotRecord):
                point_name = record.FP

            if point_name is not None:
                # Increment occurrence count
                if point_name not in self.point_occurrence_count:
                    self.point_occurrence_count[point_name] = 0

                self.point_occurrence_count[point_name] += 1
