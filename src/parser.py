"""
Parser.py
Author: Joseph Long
"""

import copy
from pathlib import Path

from .machine_state import MachineState
from .record import Rw5Record


class Rw5Parser:
    """Parses Carlson Rw5 file into instructions"""

    path: Path
    encoding: str
    instructions: list[Rw5Record]
    current_machine_state: MachineState

    def __init__(self, path: Path, encoding: str = "utf-8") -> None:
        self.path = path
        self.encoding = encoding
        self.instructions = []
        self.current_machine_state = MachineState()

    def parse(self):
        """Steps through lines of file"""
        with open(self.path, "r", encoding=self.encoding) as file:
            for index, line in enumerate(file):
                self.instructions.append(self.parse_instruction(index, line))

    def parse_instruction(self, index: int, line: str) -> Rw5Record:
        """Parses single line of file"""
        code = line.split(",")[0]
        if code[:2] == "--":
            code = "--"

        return Rw5Record(
            index,
            code,
            machine_state=copy.deepcopy(self.current_machine_state),
            content=line.strip(),
        )

    def __str__(self) -> str:
        _str = ""
        _str += f"Rw5 file {self.path}\n"
        for inst in self.instructions:
            _str += f"{str(inst)}\n"
        return _str
