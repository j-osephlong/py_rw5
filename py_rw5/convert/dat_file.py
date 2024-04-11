"""
Converts rw5 data to a dat file
"""

import datetime
from decimal import Decimal
import logging
from pathlib import Path
from typing import Optional
from py_rw5.parse.dms import DMS
from py_rw5.parse.record import SideshotRecord, StorePointRecord
from py_rw5.parse.rw5_data import Rw5Data

# create logger with 'spam_application'
logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler("convert.log")
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)


class Rw5ToDatConverter:
    """
    Writes rw5 data to Star*Net .dat data format

    Written with help of this spec of the STAR*NET format :
    https://engineeringsurveyor.com/software/starnet-v6-manual.pdf
    """

    rw5_data: Rw5Data
    dat_file_lines: list[str]

    def __init__(self, data: Rw5Data) -> None:
        self.rw5_data = data
        self.dat_file_lines = []

        logger.info(f"Initialized with Rw5 data from file {data.rw5_path}")

    def convert(self):
        """Convert to dat"""
        self.write_header()
        self.dat_file_lines.append("")
        self.write_coordinate_prelude()
        self.dat_file_lines.append("")
        self.write_commands()

    def _comment(self, comment: str):
        """Comment record starting with a #"""
        return f"# {comment}"

    def _c(self, station: str, northing: Decimal, easting: Decimal, elevation: Decimal):
        """
        "C" record records a coordinate for a station.

        Follows format: `
        C  {Station}      {Easting}       {Northing} {Elevation} [Std Errors]

        NOTE: The spec linked above shows Northing THEN easting but that is not correct for us
        """
        return (
            f"C  {station}".ljust(8)
            + f"{round(easting, 3)}".rjust(15)
            + f"{round(northing, 3)}".rjust(15)
            + f"{round(elevation, 3)}".rjust(10)
        )

    def _ss(
        self,
        at: str,
        _from: str,
        to: str,
        angle: DMS,
        slope_distance: Decimal,
        zenith: DMS,
        instrument_height: Decimal,
        rod_height: Decimal,
        comment: Optional[str],
    ):
        """
        Sideshot record (observations to a sideshot point)

        SS {at_point}-{from}-{to} {angle} {slope distance} {zenith} [{inst height}/{rod height}]
        """
        return (
            f"SS {at}-{_from}-{to}".ljust(18)
            + f"{str(angle)}".rjust(15)
            + f"{round(slope_distance, 4)}".rjust(12)
            + f"{str(zenith)}".rjust(15)
            + f"{round(instrument_height, 3)}/{round(rod_height, 3)}".rjust(15)
            + f" '{comment}"
            if comment
            else ""
        )

    def _m(
        self,
        at: str,
        _from: str,
        to: str,
        angle: DMS,
        slope_distance: Decimal,
        zenith: DMS,
        instrument_height: Decimal,
        rod_height: Decimal,
        comment: Optional[str],
    ):
        """
        Measurement record (measurement to another station)

        SS {at_point}-{from}-{to} {angle} {slope distance} {zenith} [{inst height}/{rod height}]
        """
        return (
            f"M  {at}-{_from}-{to}".ljust(18)
            + f"{str(angle)}".rjust(15)
            + f"{round(slope_distance, 4)}".rjust(12)
            + f"{str(zenith)}".rjust(15)
            + f"{round(instrument_height, 3)}/{round(rod_height, 3)}".rjust(15)
            + f" '{comment}"
            if comment
            else ""
        )

    def _dv(
        self,
        at: str,
        _from: str,
        slope_distance: Decimal,
        zenith: DMS,
        instrument_height: Decimal,
        rod_height: Decimal,
        comment: Optional[str],
    ):
        """
        Distance and Vertical Measurements record (Distance and Vertical Measurements to another station)

        SS {at_point}-{from}-{to} {slope distance} {zenith} [{inst height}/{rod height}]

        Notably omits angle param that other similar commands include
        """
        return (
            f"DV {at}-{_from}".ljust(18)
            + "".rjust(15)
            + f"{round(slope_distance, 4)}".rjust(12)
            + f"{str(zenith)}".rjust(15)
            + f"{round(instrument_height, 3)}/{round(rod_height, 3)}".rjust(15)
            + f" '{comment}"
            if comment
            else ""
        )

    def _db(self, PN: str, comment: Optional[str]):
        """
        DB - Begin set of direction readings

        DB {From station name} {comment}
        """
        return f"DB {PN}" + (f" '{comment}" if comment else "")

    def _dm(
        self,
        to: str,
        direction: DMS,
        slope_distance: Decimal,
        zenith: DMS,
        instrument_height: Decimal,
        rod_height: Decimal,
    ):
        """
        DM - direction with measurements to another station

        DM {to} {direction} {slope distance} {zenith} [{instrument height}/{rod height}]
        """
        return (
            "DM "
            + f"{to}".ljust(15)
            + f"{str(direction)}".rjust(15)
            + f"{slope_distance}".rjust(12)
            + f"{str(zenith)}".rjust(15)
            + f"{round(instrument_height, 3)}/{round(rod_height, 3)}".rjust(15)
        )

    def _de(self):
        """
        End of set of direction readings
        """
        return "DE"

    def write_header(self):
        """Writes top of file comments"""
        logger.info(f"Writing header.")

        job_record = self.rw5_data.job_record

        header = [
            self._comment("PY RW5 Version 1.0"),
            "",
            self._comment(f"Input File Path : {self.rw5_data.rw5_path}"),
            self._comment(f"Date Processed  : {datetime.datetime.now().isoformat()}"),
            "",
            self._comment(f"Job             : {job_record.NM}"),
            self._comment(f"Date            : {job_record.DT}"),
            self._comment(f"Time            : {job_record.TM}"),
        ]

        for line in header:
            logger.info(line)

        self.dat_file_lines.extend(header)

    def write_coordinate_prelude(self):
        """Writes C records for GPS and store point (SP) records        `"""

        logger.info(f"Writing coordinates prelude.")
        for point_name, coord in self.rw5_data.coordinates.items():
            avg = coord.avg
            line = self._c(point_name, avg.northing, avg.easting, avg.elevation)
            logger.info(line)
            self.dat_file_lines.append(line)

    def write_side_shot(self, side_shot: SideshotRecord):
        """Writes Rw5 sideshot record as a DV, M, or SS STAR*NET command"""
        assert (
            side_shot.machine_state.backsight_angle is not None
        ), """Backsight required for M, SS or DV STAR*NET commands."""
        assert (
            side_shot.machine_state.backsight_coord is not None
        ), """Backsight required for M, SS or DV STAR*NET commands."""
        assert (
            side_shot.machine_state.instrument_height is not None
        ), """Instrument height required for M, SS or DV STAR*NET commands."""
        assert (
            side_shot.machine_state.rod_height is not None
        ), """Rod height required for M, SS or DV STAR*NET commands."""

        logger.info("Writing side shot.")
        logger.info(f"{self.rw5_data.point_occurrence_count=}")
        logger.info(f"{side_shot.FP}")

        # TO point == FROM point (backsight)
        if side_shot.FP == side_shot.machine_state.backsight_coord:
            line = self._dv(
                side_shot.OP,
                side_shot.machine_state.backsight_coord,
                side_shot.SD,
                side_shot.ZE,
                side_shot.machine_state.instrument_height,
                side_shot.machine_state.rod_height,
                side_shot.comment,
            )
            logger.info(line)
            self.dat_file_lines.append(line)
            return

        angle = side_shot.AR - side_shot.machine_state.backsight_angle

        command = self._ss

        # If the point has been seen more than once, use M record
        if self.rw5_data.point_occurrence_count[side_shot.FP] > 1:
            command = self._m

        line = command(
            side_shot.OP,
            side_shot.machine_state.backsight_coord,
            side_shot.FP,
            angle,
            side_shot.SD,
            side_shot.ZE,
            side_shot.machine_state.instrument_height,
            side_shot.machine_state.rod_height,
            side_shot.comment,
        )
        logger.info(line)
        self.dat_file_lines.append(line)

    def write_resection(self, store_point: StorePointRecord):
        """Writes Rw5 store point record w/ resection as DB, DM, and DE commands"""
        assert (
            store_point.machine_state.instrument_height is not None
        ), """Instrument height required for DM STAR*NET commands."""
        assert (
            store_point.machine_state.rod_height is not None
        ), """Rod height required for DM STAR*NET commands."""

        logger.info("Writing resection.")

        resection = [
            "",
            self._db(store_point.PN, store_point.comment),
            *[
                self._dm(
                    reading.FP,
                    reading.AR,
                    reading.SD,
                    reading.ZE,
                    store_point.machine_state.instrument_height,
                    store_point.machine_state.rod_height,
                )
                for reading in store_point.resection_readings
            ],
            self._de(),
            "",
        ]

        for line in resection:
            logger.info(line)

        self.dat_file_lines.extend(resection)

    def write_commands(self):
        for record in self.rw5_data.records:
            if isinstance(record, SideshotRecord):
                self.write_side_shot(record)
            elif isinstance(record, StorePointRecord) and record.is_resection:
                self.write_resection(record)

    def write(self, output_file_path: Path):
        with open(output_file_path, "w") as file:
            file.write("\n".join(self.dat_file_lines))
