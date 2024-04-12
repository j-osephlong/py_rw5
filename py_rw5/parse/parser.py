"""
Parser.py
Author: Joseph Long
"""

import copy
import logging
from pathlib import Path
from typing import Literal, Optional, cast

from py_rw5.parse.rw5_data import Rw5Data

from .machine_state import MachineState
from .record import (
    BacksightRecord,
    GPSRecord,
    JobRecord,
    LineOfSightRecord,
    ModeSetupRecord,
    NoteRecord,
    OccupyRecord,
    OffCenterShotRecord,
    RecordType,
    Rw5Record,
    SideshotRecord,
    StorePointRecord,
)

# create logger with 'spam_application'
logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler("parse.log")
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)


class Rw5Parser:
    """Parses Carlson Rw5 file into instructions"""

    records: list[Rw5Record]
    rw5_path: Path
    rw5_encoding: str
    current_machine_state: MachineState
    last_non_comment_record: Optional[Rw5Record]
    substitute_point_names: bool
    substitute_point_comment_prefix: str

    def __init__(
        self,
        path: Path,
        encoding: str = "utf-8",
        substitute_point_names=True,
        substitute_point_comment_prefix="CP/",
    ) -> None:
        """Creates a rw5 parser

        Args:
            path (Path): Path to Rw5 file
            encoding (str, optional): Encoding of Rw5 file. Defaults to "utf-8".
            substitute_point_names (bool, optional): If true, GPS and sideshot records will have their point names replaced with the point name found after the comment prefix. Defaults to True.
            substitute_point_comment_prefix (str, optional): Prefix to name to use for name substitution. Defaults to "CP/".
        """
        self.current_machine_state = MachineState()
        self.rw5_path = path
        self.rw5_encoding = encoding
        self.records = []
        self.substitute_point_names = substitute_point_names
        self.substitute_point_comment_prefix = substitute_point_comment_prefix
        logger.info(
            f"Initialized with {path=}, {encoding=}, {substitute_point_names=}, {substitute_point_comment_prefix=}."
        )

    def parse(self):
        """Steps through lines of file"""

        logger.info("Beginning parse.")

        record_line_index: Optional[int] = None
        record_line: Optional[str] = None
        comment_lines = []

        with open(self.rw5_path, "r", encoding=self.rw5_encoding) as file:
            for index, line in enumerate(file):
                if line.startswith("--") and record_line is not None:
                    comment_lines.append(line)
                else:
                    if record_line is not None and record_line_index is not None:
                        self.records.append(
                            self.parse_instruction(
                                record_line_index, record_line, comment_lines
                            )
                        )
                    record_line = line
                    record_line_index = index
                    comment_lines = []

        return Rw5Data(self.rw5_path, self.rw5_encoding, self.records)

    def substitute_point_name(
        self, record_type: Literal["GPS", "SS"], line: str
    ) -> str:
        """Replaces point name in line."""

        if f"--{self.substitute_point_comment_prefix}" not in line:
            return line

        point_name: str

        if record_type == "GPS":
            point_name_start = line.find("PN") + 2
            point_name_end_exclusive = line.find(",", point_name_start)
            point_name = line[point_name_start:point_name_end_exclusive]
        else:
            point_name_start = line.find("FP") + 2
            point_name_end_exclusive = line.find(",", point_name_start)
            point_name = line[point_name_start:point_name_end_exclusive]

        new_point_name_start = line.find(self.substitute_point_comment_prefix) + len(
            self.substitute_point_comment_prefix
        )
        new_point_name = line[new_point_name_start:].split(" ")[0].strip()
        logger.info(f"Replacing {point_name} with {new_point_name} in line {line}.")

        return line.replace(point_name, new_point_name)

    def parse_instruction(
        self, index: int, line: str, comment_lines: list[str]
    ) -> Rw5Record:
        """Parses single line of file"""

        logger.info(f"Parsing line {index} {line=}")

        code: RecordType = cast(RecordType, line.split(",")[0])
        if code[:2] == "--":
            code = "--"

        # Find right record class
        record_class: type[Rw5Record] = Rw5Record

        match code:
            case "--":
                record_class = NoteRecord
            case "BK":
                record_class = BacksightRecord
            case "JB":
                record_class = JobRecord
            case "LS":
                record_class = LineOfSightRecord
            case "MO":
                record_class = ModeSetupRecord
            case "OC":
                record_class = OccupyRecord
            case "OF":
                record_class = OffCenterShotRecord
            case "SP":
                record_class = StorePointRecord
            case "SS":
                line = self.substitute_point_name("SS", line)
                record_class = SideshotRecord
            case "GPS":
                line = self.substitute_point_name("GPS", line)
                record_class = GPSRecord

        # Use that record class to create a record from the line
        (record, machine_state) = record_class.from_string(
            index=index,
            record_type=code,
            line=line.strip(),
            machine_state=copy.deepcopy(self.current_machine_state),
            comment_lines=comment_lines,
        )

        self.current_machine_state = machine_state

        logger.info(f"{record.__dict__}")

        return record
