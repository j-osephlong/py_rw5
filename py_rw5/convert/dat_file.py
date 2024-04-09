"""
Converts rw5 data to a dat file
"""

import datetime
from py_rw5.parse.rw5_data import Rw5Data


class Rw5ToDatConverter:
    rw5_data: Rw5Data
    dat_file_lines: list[str]

    def __init__(self, data: Rw5Data) -> None:
        self.rw5_data = data
        self.dat_file_lines = []

    def write_header(self):
        job_record = self.rw5_data.job_record

        self.dat_file_lines.extend(
            [
                "# PY RW5 Version 1.0",
                "",
                f"# Input File Path : {self.rw5_data.rw5_path}",
                f"# Date Processed  : {datetime.datetime.now().isoformat()}",
                "",
                f"# Job             : {job_record.NM}",
                f"# Date            : {job_record.DT}",
                f"# Time            : {job_record.TM}",
                "",
            ]
        )

    def write_coordinate_prelude(self):
        for point_name, coord in self.rw5_data.coordinates.items():
            avg = coord.avg
            self.dat_file_lines.append(
                f"C  {point_name}".ljust(8)
                + f"{round(avg.easting, 3)}".rjust(15)
                + f"{round(avg.northing, 3)}".rjust(15)
                + f"{round(avg.elevation, 3)}".rjust(10)
            )
