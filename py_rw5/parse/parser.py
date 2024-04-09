"""
Parser.py
Author: Joseph Long
"""

import copy
import logging
from pathlib import Path
from typing import Optional, cast

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

    def __init__(self, path: Path, encoding: str = "utf-8") -> None:
        self.current_machine_state = MachineState()
        self.rw5_path = path
        self.rw5_encoding = encoding
        self.records = []
        logger.info(f"Initialized with {path=}, {encoding=}.")

    def parse(self):
        """Steps through lines of file"""

        logger.info("Beginning parse.")

        with open(self.rw5_path, "r", encoding=self.rw5_encoding) as file:
            for index, line in enumerate(file):
                self.records.append(self.parse_instruction(index, line))

        return Rw5Data(self.rw5_path, self.rw5_encoding, self.records)

    def parse_instruction(self, index: int, line: str) -> Rw5Record:
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
                record_class = SideshotRecord
            case "GPS":
                record_class = GPSRecord

        # Use that record class to create a record from the line
        (record, machine_state) = record_class.from_string(
            index=index,
            record_type=code,
            line=line.strip(),
            machine_state=copy.deepcopy(self.current_machine_state),
        )

        self.current_machine_state = machine_state

        logger.info(f"{record.__dict__}")

        # If the record is a note, append it to the last non-note record
        if not isinstance(record, NoteRecord):
            self.last_non_comment_record = record
        elif self.last_non_comment_record is not None:
            self.last_non_comment_record.notes.append(record)

        return record
