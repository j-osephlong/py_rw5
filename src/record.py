# pylint: disable=C0103

"""
Defines the Rw5 record definition
Author: Joseph Long

Follows the following spec: 
https://totalopenstation.readthedocs.io/en/latest/input_formats/if_carlson_rw5.html 
"""

import dataclasses
from decimal import Decimal
from functools import cached_property
from typing import Literal, Optional, Self

from src.dms import DMS

from .machine_state import MachineState

record_types = [
    "--",  # Note
    "JB",
    "MO",
    "BD",
    "BK",
    "BR",
    "FD",
    "FR",
    "GPS",
    "GS",
    "LS",
    "OC",
    "OF",
    "SP",
    "TR",
    "SS",
]

RecordType = Literal[
    "--",  # Note
    "JB",
    "MO",
    "BD",
    "BK",
    "BR",
    "FD",
    "FR",
    "GPS",
    "GS",
    "LS",
    "OC",
    "OF",
    "SP",
    "TR",
    "SS",
]

record_descriptions = {
    "--": "Note",
    "JB": "Job",
    "MO": "Mode Setup",
    "BD": "Backsight Direct",
    "BK": "Backsight",
    "BR": "Backsight Reverse",
    "FD": "Foresight Direct",
    "FR": "Foresight Reverse",
    "GPS": "GPS Position",
    "GS": "Reduced local coordinate from GPS record and localization data",
    "LS": "Line of Sight",
    "OC": "Occupy Point",
    "OF": "Off Center Shot",
    "SP": "Store Point",
    "TR": "Traverse",
    "SS": "Sideshot",
}


@dataclasses.dataclass(kw_only=True)
class Rw5Record:
    """Base Rw5 Record"""

    index: int
    """Line index in file"""
    record_type: RecordType
    """
    The type of the record.
    Must be one of the types defined in {record_types}
    """
    machine_state: MachineState
    """
    Machine state at time of instruction
    """
    content: str
    """
    Raw line string
    """
    comment: Optional[str] = ""
    """
    Comment at the end of the record, omitting the prefix '--' 
    """
    notes: list["NoteRecord"] = dataclasses.field(default_factory=list)
    """
    List of note records after this record.
    """

    @staticmethod
    def get_param_optional(line: str, prefix: str):
        """
        Get line parameter value

        Example: SS,OP1,FP2,AR0.0044,ZE86.0133,SD10.313750,--CP
        get_param(line 'OP') -> '1'
        """
        if prefix not in line:
            return None
        return line[line.find(prefix) + len(prefix) : line.find(",", line.find(prefix))]

    @staticmethod
    def get_param(line: str, prefix: str):
        """
        Get line parameter value

        Example: SS,OP1,FP2,AR0.0044,ZE86.0133,SD10.313750,--CP
        get_param(line 'OP') -> '1'
        """
        return line[line.find(prefix) + len(prefix) : line.find(",", line.find(prefix))]

    @property
    def type_description(self):
        """Description of record type"""
        return record_descriptions[self.record_type]

    def __str__(self) -> str:
        return (
            f'[{str(self.index).rjust(4)}] {self.record_type.rjust(3)} "{self.content}"'
        )

    @classmethod
    def from_string(
        cls, index: int, record_type: RecordType, line: str, machine_state: MachineState
    ) -> Self:
        return cls(
            index=index,
            record_type=record_type,
            machine_state=machine_state,
            content=line,
        )


@dataclasses.dataclass(kw_only=True)
class NoteRecord(Rw5Record):
    """
    Record starting with '--'

    May contain controller debug output
    """

    @cached_property
    def params(self):
        """
        Notes can have debug output.
        This tries it's best to parse out key/value pairs from the output
        """
        _params = {}
        words = self.content.split(" ")

        key_complete = False
        key = ""

        for word in words:
            if not key_complete:
                key += word
                if ":" in word:
                    key = key.removesuffix(":")
                    key_complete = True
            else:
                _params[key] = word

        return _params


@dataclasses.dataclass(kw_only=True)
class BacksightRecord(Rw5Record):
    """Ex: BK,OP1,BP2,BS315.0000,BC0.0044"""

    OP: str
    """Occupy point"""
    BP: str
    """Back point"""
    BS: DMS
    """Backsight"""
    BC: DMS
    """Back circle"""

    @classmethod
    def from_string(
        cls, index: int, record_type: RecordType, line: str, machine_state: MachineState
    ) -> Self:
        OP = Rw5Record.get_param(line, "OP")
        assert OP
        BP = Rw5Record.get_param(line, "BP")
        assert BP
        _BS = Rw5Record.get_param(line, "BS")
        assert _BS
        BS = DMS.from_str(_BS)
        _BC = Rw5Record.get_param(line, "BC")
        BC = DMS.from_str(_BC)

        return cls(
            index=index,
            record_type=record_type,
            content=line,
            machine_state=machine_state,
            OP=OP,
            BP=BP,
            BS=BS,
            BC=BC,
        )


@dataclasses.dataclass(kw_only=True)
class JobRecord(Rw5Record):
    """Ex: JB,NMSAMPLE,DT06-27-2003,TM14:21:53"""

    NM: str
    """Name"""
    DT: str
    """Date"""
    TM: str
    """Time"""

    @classmethod
    def from_string(
        cls, index: int, record_type: RecordType, line: str, machine_state: MachineState
    ) -> Self:
        NM = Rw5Record.get_param(line, "NM")
        DT = Rw5Record.get_param(line, "DT")
        TM = Rw5Record.get_param(line, "TM")

        return cls(
            index=index,
            record_type=record_type,
            content=line,
            machine_state=machine_state,
            NM=NM,
            DT=DT,
            TM=TM,
        )


@dataclasses.dataclass(kw_only=True)
class LineOfSightRecord(Rw5Record):
    """Ex: LS,HI5.000000,HR6.000000"""

    HI: Optional[Decimal] = None
    """Height of instrument"""
    HR: Optional[Decimal] = None
    """Height of rod"""

    @classmethod
    def from_string(
        cls, index: int, record_type: RecordType, line: str, machine_state: MachineState
    ) -> Self:
        HI = Rw5Record.get_param_optional(line, "HI")
        HR = Rw5Record.get_param_optional(line, "HR")

        return cls(
            index=index,
            record_type=record_type,
            content=line,
            machine_state=machine_state,
            HI=Decimal(HI) if HI else None,
            HR=Decimal(HR) if HR else None,
        )


@dataclasses.dataclass(kw_only=True)
class ModeSetup(Rw5Record):
    """Ex: MO,AD0,UN0,SF1.00000000,EC1,EO0.0,AU0"""

    AD: Literal[0, 1]
    """Azimuth direction (0 = North) (1 = South)"""
    UN: Literal[0, 1, 2]
    """Distance unit (0 = Feet) (1=Meter) (2=US Survey Feet)"""
    SF: Decimal
    """Scale factor"""
    EC: Literal[0, 1]
    """Earth Curvature (0 = off) (1=On)"""
    AU: Literal[0, 1]
    """Angle Unit (0=Degree) (1=Grads)"""
    EO: Optional[Decimal] = None
    """EDM offset"""

    @classmethod
    def from_string(
        cls, index: int, record_type: RecordType, line: str, machine_state: MachineState
    ) -> Self:
        AD = Rw5Record.get_param(line, "AD")
        UN = Rw5Record.get_param(line, "UN")
        SF = Rw5Record.get_param(line, "SF")
        EC = Rw5Record.get_param(line, "EC")
        AU = Rw5Record.get_param(line, "AU")
        EO = Rw5Record.get_param_optional(line, "EO")

        return cls(
            index=index,
            record_type=record_type,
            content=line,
            machine_state=machine_state,
            AD=int(AD),  # type: ignore
            UN=int(UN),  # type: ignore
            SF=Decimal(SF),
            EC=int(EC),  # type: ignore
            AU=int(AU),  # type: ignore
            EO=Decimal(EO) if EO else None,
        )


@dataclasses.dataclass(kw_only=True)
class OccupyRecord(Rw5Record):
    """Ex: OC,OP1,N 5000.00000,E 5000.00000,EL100.000,--CP"""

    PN: str
    """Point number"""
    N: Decimal
    """Northing"""
    E: Decimal
    """Easting"""
    EL: Decimal
    """Elevation"""

    @classmethod
    def from_string(
        cls, index: int, record_type: RecordType, line: str, machine_state: MachineState
    ) -> Self:
        PN = Rw5Record.get_param(line, "PN")
        N = Rw5Record.get_param(line, "N")
        E = Rw5Record.get_param(line, "E")
        EL = Rw5Record.get_param(line, "EL")

        return cls(
            index=index,
            record_type=record_type,
            content=line,
            machine_state=machine_state,
            PN=PN,
            N=Decimal(N),
            E=Decimal(E),
            EL=Decimal(EL),
        )


@dataclasses.dataclass(kw_only=True)
class OffCenterShotRecord(Rw5Record):
    """Ex: OF,AR90.3333,ZE90.0000,SD25.550000"""

    AR: Decimal
    """Angle right"""
    ZE: Decimal
    """Zenith (actual)"""
    SD: Decimal
    """Slope Distance"""

    @classmethod
    def from_string(
        cls, index: int, record_type: RecordType, line: str, machine_state: MachineState
    ) -> Self:
        AR = Rw5Record.get_param(line, "AR")
        ZE = Rw5Record.get_param(line, "ZE")
        SD = Rw5Record.get_param(line, "SD")

        return cls(
            index=index,
            record_type=record_type,
            content=line,
            machine_state=machine_state,
            AR=Decimal(AR),
            ZE=Decimal(ZE),
            SD=Decimal(SD),
        )


@dataclasses.dataclass(kw_only=True)
class StorePointRecord(Rw5Record):
    """Ex: SP,PN100,N 5002.0000,E 5000.0000,EL100.0000,--PP"""

    PN: str
    """Point Number"""
    N: Decimal
    """Northing"""
    E: Decimal
    """Easting"""
    EL: Decimal
    """Elevation """

    @classmethod
    def from_string(
        cls, index: int, record_type: RecordType, line: str, machine_state: MachineState
    ) -> Self:
        PN = Rw5Record.get_param(line, "PN")
        N = Rw5Record.get_param(line, "N")
        E = Rw5Record.get_param(line, "E")
        EL = Rw5Record.get_param(line, "EL")

        return cls(
            index=index,
            record_type=record_type,
            content=line,
            machine_state=machine_state,
            PN=PN,
            N=Decimal(N),
            E=Decimal(E),
            EL=Decimal(EL),
        )


@dataclasses.dataclass(kw_only=True)
class SideshotRecord(Rw5Record):
    """Ex: SS,OP1,FP2,AR0.0044,ZE86.0133,SD10.313750,--CP"""

    OP: str
    """Occupy point"""
    FP: str
    """Foresight point"""
    AR: DMS
    """Angle-Right"""
    ZE: DMS
    """Zenith"""
    SD: Decimal
    """Slope Distance"""

    @classmethod
    def from_string(
        cls, index: int, record_type: RecordType, line: str, machine_state: MachineState
    ) -> Self:
        OP = Rw5Record.get_param(line, "OP")
        FP = Rw5Record.get_param(line, "FP")
        AR = Rw5Record.get_param(line, "AR")
        ZE = Rw5Record.get_param(line, "ZE")
        SD = Rw5Record.get_param(line, "SD")

        return cls(
            index=index,
            record_type=record_type,
            content=line,
            machine_state=machine_state,
            OP=OP,
            FP=FP,
            AR=DMS.from_str(AR),
            ZE=DMS.from_str(ZE),
            SD=Decimal(SD),
        )
