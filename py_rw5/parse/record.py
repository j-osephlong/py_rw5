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

from .dms import DMS

from .machine_state import MachineState

# region Base Record Definition
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
    notes: list[str] = dataclasses.field(default_factory=list)
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
        return Rw5Record.get_param(line, prefix)

    @staticmethod
    def get_param(line: str, prefix: str):
        """
        Get line parameter value

        Example: SS,OP1,FP2,AR0.0044,ZE86.0133,SD10.313750,--CP
        get_param(line 'OP') -> '1'
        """
        start_of_val = line.find(prefix) + len(prefix)
        end_of_val = line.find(",", line.find(prefix))
        if end_of_val == -1:
            end_of_val = len(line)

        param = line[start_of_val:end_of_val].strip()
        if "--" in param:
            param = param[: param.find("--")]
        return param

    @staticmethod
    def get_comment(line: str):
        _line = line
        comment_index = _line.find("--")
        if comment_index == 0:
            # this means it's a comment line
            # comment lines might be comment "records" which can have their own comments
            _line = _line.removeprefix("--")
            comment_index = _line.find("--")

        # no comment found
        if comment_index == -1:
            return None

        return _line[comment_index:].removeprefix("--")

    @property
    def type_description(self):
        """Description of record type"""
        return record_descriptions[self.record_type]

    def __str__(self) -> str:
        return (
            f'[{str(self.index).rjust(4)}] {self.record_type.rjust(3)} "{self.content}"'
        )

    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    def from_string(
        cls,
        index: int,
        record_type: RecordType,
        line: str,
        machine_state: MachineState,
        comment_lines: list[str],
    ) -> tuple[Self, MachineState]:
        """Creates record from line of Rw5 file"""
        comment = Rw5Record.get_comment(line)
        return (
            cls(
                index=index,
                record_type=record_type,
                machine_state=machine_state,
                comment=comment,
                notes=comment_lines,
                content=line,
            ),
            machine_state,
        )


# endregion


# region Note Record
@dataclasses.dataclass(kw_only=True)
class NoteRecord(Rw5Record):
    """
    Record starting with '--'

    May contain controller debug output
    """

    def get_colon_mode_params(self):
        """
        When a note line is split up by spaces with colon separated key/value pairs

        Ex: --HRMS Avg: 0.0046 SD: 0.0004 Min: 0.0043 Max: 0.0058
        """
        params = {}
        words = self.content.removeprefix("--").split(" ")

        key_parts = []
        key = None

        for word in words:
            if key is None:
                key_parts.append(word)
                if ":" in word:
                    key = " ".join(key_parts)
                    key = key.removesuffix(":")

            else:
                params[key] = word
                key_parts = []
                key = None

        return params

    def get_comma_mode_params(self):
        """
        When a note line is split up by commas with 2 character key-prefixes to values

        Ex:  --GS,PN6001,N 7366899.7136,E 2532873.5826,EL49.6420,--CP/CP1

        """
        params = {}
        words = self.content.removeprefix("--").split(",")

        for word in words:
            params[word[:2]] = word[2:]

        return params

    @cached_property
    def params(self):
        """
        Notes can have debug output.
        This tries it's best to parse out key/value pairs from the output
        """
        # Rule of thumb is if there's a colon in the line and no comma, we use colon mode
        if ":" in self.content and "," not in self.content:
            return self.get_colon_mode_params()

        return self.get_comma_mode_params()


# endregion


# region Backsight Record
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
        cls,
        index: int,
        record_type: RecordType,
        line: str,
        machine_state: MachineState,
        comment_lines: list[str],
    ) -> tuple[Self, MachineState]:
        comment = Rw5Record.get_comment(line)
        OP = Rw5Record.get_param(line, "OP")
        assert OP
        BP = Rw5Record.get_param(line, "BP")
        assert BP
        _BS = Rw5Record.get_param(line, "BS")
        assert _BS
        BS = DMS.from_str(_BS)
        _BC = Rw5Record.get_param(line, "BC")
        BC = DMS.from_str(_BC)

        machine_state.backsight_coord = BP
        machine_state.backsight_angle = BS

        return (
            cls(
                index=index,
                record_type=record_type,
                content=line,
                machine_state=machine_state,
                comment=comment,
                notes=comment_lines,
                OP=OP,
                BP=BP,
                BS=BS,
                BC=BC,
            ),
            machine_state,
        )


# endregion


# region Job Record
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
        cls,
        index: int,
        record_type: RecordType,
        line: str,
        machine_state: MachineState,
        comment_lines: list[str],
    ) -> tuple[Self, MachineState]:
        comment = Rw5Record.get_comment(line)
        NM = Rw5Record.get_param(line, "NM")
        DT = Rw5Record.get_param(line, "DT")
        TM = Rw5Record.get_param(line, "TM")

        return (
            cls(
                index=index,
                record_type=record_type,
                content=line,
                machine_state=machine_state,
                comment=comment,
                notes=comment_lines,
                NM=NM,
                DT=DT,
                TM=TM,
            ),
            machine_state,
        )


# endregion


# region LoS Record
@dataclasses.dataclass(kw_only=True)
class LineOfSightRecord(Rw5Record):
    """Ex: LS,HI5.000000,HR6.000000"""

    HI: Optional[Decimal] = None
    """Height of instrument"""
    HR: Optional[Decimal] = None
    """Height of rod"""

    @classmethod
    def from_string(
        cls,
        index: int,
        record_type: RecordType,
        line: str,
        machine_state: MachineState,
        comment_lines: list[str],
    ) -> tuple[Self, MachineState]:
        comment = Rw5Record.get_comment(line)
        _HI = Rw5Record.get_param_optional(line, "HI")
        _HR = Rw5Record.get_param_optional(line, "HR")
        HI = None
        HR = None

        if _HI:
            HI = Decimal(_HI)
            machine_state.instrument_height = HI
        if _HR:
            HR = Decimal(_HR)
            machine_state.rod_height = HR

        return (
            cls(
                index=index,
                record_type=record_type,
                content=line,
                machine_state=machine_state,
                comment=comment,
                notes=comment_lines,
                HI=HI,
                HR=HR,
            ),
            machine_state,
        )


# endregion


# region Mode Setup Record
@dataclasses.dataclass(kw_only=True)
class ModeSetupRecord(Rw5Record):
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
        cls,
        index: int,
        record_type: RecordType,
        line: str,
        machine_state: MachineState,
        comment_lines: list[str],
    ) -> tuple[Self, MachineState]:
        comment = Rw5Record.get_comment(line)
        AD = Rw5Record.get_param(line, "AD")
        UN = Rw5Record.get_param(line, "UN")
        SF = Rw5Record.get_param(line, "SF")
        EC = Rw5Record.get_param(line, "EC")
        AU = Rw5Record.get_param(line, "AU")
        EO = Rw5Record.get_param_optional(line, "EO")

        return (
            cls(
                index=index,
                record_type=record_type,
                content=line,
                machine_state=machine_state,
                comment=comment,
                notes=comment_lines,
                AD=int(AD),  # type: ignore
                UN=int(UN),  # type: ignore
                SF=Decimal(SF),
                EC=int(EC),  # type: ignore
                AU=int(AU),  # type: ignore
                EO=Decimal(EO) if EO else None,
            ),
            machine_state,
        )


# endregion


# region Occupy Record
@dataclasses.dataclass(kw_only=True)
class OccupyRecord(Rw5Record):
    """Ex: OC,OP1,N 5000.00000,E 5000.00000,EL100.000,--CP"""

    OP: str
    """Occupy Point"""
    N: Decimal
    """Northing"""
    E: Decimal
    """Easting"""
    EL: Decimal
    """Elevation"""

    @classmethod
    def from_string(
        cls,
        index: int,
        record_type: RecordType,
        line: str,
        machine_state: MachineState,
        comment_lines: list[str],
    ) -> tuple[Self, MachineState]:
        comment = Rw5Record.get_comment(line)
        OP = Rw5Record.get_param(line, "OP")
        N = Rw5Record.get_param(line, "N ")
        E = Rw5Record.get_param(line, "E ")
        EL = Rw5Record.get_param(line, "EL")

        return (
            cls(
                index=index,
                record_type=record_type,
                content=line,
                machine_state=machine_state,
                comment=comment,
                notes=comment_lines,
                OP=OP,
                N=Decimal(N),
                E=Decimal(E),
                EL=Decimal(EL),
            ),
            machine_state,
        )


# endregion


# region Off center Record
@dataclasses.dataclass(kw_only=True)
class OffCenterShotRecord(Rw5Record):
    """Ex: OF,AR90.3333,ZE90.0000,SD25.550000"""

    AR: DMS
    """Angle right"""
    ZE: DMS
    """Zenith (actual)"""
    SD: Decimal
    """Slope Distance"""

    @classmethod
    def from_string(
        cls,
        index: int,
        record_type: RecordType,
        line: str,
        machine_state: MachineState,
        comment_lines: list[str],
    ) -> tuple[Self, MachineState]:
        comment = Rw5Record.get_comment(line)
        _AR = Rw5Record.get_param(line, "AR")
        AR = DMS.from_str(_AR)
        _ZE = Rw5Record.get_param(line, "ZE")
        ZE = DMS.from_str(_ZE)
        SD = Rw5Record.get_param(line, "SD")

        return (
            cls(
                index=index,
                record_type=record_type,
                content=line,
                machine_state=machine_state,
                comment=comment,
                notes=comment_lines,
                AR=AR,
                ZE=ZE,
                SD=Decimal(SD),
            ),
            machine_state,
        )


# endregion


# region Store Point Record


@dataclasses.dataclass(kw_only=True)
class StorePointResectionReadingCommentRecord:
    name: str
    FP: str
    AR: DMS
    ZE: DMS
    SD: Decimal
    comment: Optional[str]


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

    resection: bool
    resection_readings: list[StorePointResectionReadingCommentRecord]

    @classmethod
    def from_string(
        cls,
        index: int,
        record_type: RecordType,
        line: str,
        machine_state: MachineState,
        comment_lines: list[str],
    ) -> tuple[Self, MachineState]:
        comment = Rw5Record.get_comment(line)
        PN = Rw5Record.get_param(line, "PN")
        N = Rw5Record.get_param(line, "N ")
        E = Rw5Record.get_param(line, "E ")
        EL = Rw5Record.get_param(line, "EL")

        resection = False
        resection_readings: list[StorePointResectionReadingCommentRecord] = list()

        if len(comment_lines) >= 3 and comment_lines[2].startswith("--Resection:"):
            resection = True
            for line in comment_lines[3:]:
                if line.startswith("--Reading"):
                    name_start = line.find("--Reading ") + len("--Reading ")
                    name_end = line.find(":")
                    name = line[name_start:name_end]
                    _l = line[name_end + 1 :]
                    FP = Rw5Record.get_param(_l, "FP")
                    _AR = Rw5Record.get_param(_l, "AR")
                    AR = DMS.from_str(_AR)
                    _ZE = Rw5Record.get_param(_l, "ZE")
                    ZE = DMS.from_str(_ZE)
                    _SD = Rw5Record.get_param(_l, "SD")
                    SD = Decimal(_SD)
                    comment = Rw5Record.get_comment(_l)
                    resection_readings.append(
                        StorePointResectionReadingCommentRecord(
                            FP=FP, AR=AR, ZE=ZE, SD=SD, comment=comment, name=name
                        )
                    )
        return (
            cls(
                index=index,
                record_type=record_type,
                content=line,
                machine_state=machine_state,
                comment=comment,
                notes=comment_lines,
                PN=PN,
                N=Decimal(N),
                E=Decimal(E),
                EL=Decimal(EL),
                resection=resection,
                resection_readings=resection_readings,
            ),
            machine_state,
        )


# endregion


# region Sideshot Record
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
        cls,
        index: int,
        record_type: RecordType,
        line: str,
        machine_state: MachineState,
        comment_lines: list[str],
    ) -> tuple[Self, MachineState]:
        comment = Rw5Record.get_comment(line)
        OP = Rw5Record.get_param(line, "OP")
        FP = Rw5Record.get_param(line, "FP")
        AR = Rw5Record.get_param(line, "AR")
        ZE = Rw5Record.get_param(line, "ZE")
        SD = Rw5Record.get_param(line, "SD")

        return (
            cls(
                index=index,
                record_type=record_type,
                content=line,
                machine_state=machine_state,
                comment=comment,
                notes=comment_lines,
                OP=OP,
                FP=FP,
                AR=DMS.from_str(AR),
                ZE=DMS.from_str(ZE),
                SD=Decimal(SD),
            ),
            machine_state,
        )


# endregion


# region GPS Record
@dataclasses.dataclass(kw_only=True)
class GPSRecord(Rw5Record):
    PN: str
    _LA: Decimal
    """Raw Latitude. The property N should be used instead as it has been post processed."""
    _LN: Decimal
    """Raw Longitude. The property E should be used instead as it has been post processed."""
    _EL: Decimal
    """Raw Elevation. The property EL should be used instead as it has been post processed."""

    N: Decimal
    """Northing (Processed)"""
    E: Decimal
    """Easting (Processed)"""
    EL: Decimal
    """Elevation (Processed)"""

    FIXED: bool
    """Was GPS shot fixed?
    
    'Fixed means you have a full phase solution with the satellites on both base 
        and rover antennas and radio connection with the receiver.'
    """
    HRMS: Decimal
    """Horizontal RMS"""
    VRMS: Decimal
    """Vertical RMS"""
    AGE: Decimal
    """Age of reading"""
    num_epochs: int
    """Number of epochs (readings) for this measurement."""

    @classmethod
    def from_string(
        cls,
        index: int,
        record_type: RecordType,
        line: str,
        machine_state: MachineState,
        comment_lines: list[str],
    ) -> tuple[Self, MachineState]:
        comment = Rw5Record.get_comment(line)
        PN = Rw5Record.get_param(line, "PN")
        LA = Rw5Record.get_param(line, "LA")
        LN = Rw5Record.get_param(line, "LN")
        EL = Rw5Record.get_param(line, "EL")

        # --GS,PN6016,N 7366799.2873,E 2532888.7519,EL46.5363,--CP/CP8
        GS_line = comment_lines[0]
        N = Decimal(Rw5Record.get_param(GS_line, "N "))
        E = Decimal(Rw5Record.get_param(GS_line, "E "))
        EL = Decimal(Rw5Record.get_param(GS_line, "EL"))

        FIXED: bool
        num_readings: int
        HRMS: Decimal
        VRMS: Decimal
        if comment_lines[2].startswith("--Valid Readings:"):
            # This is an average line (assumed FIXED)
            FIXED = True
            print(comment_lines[2].removeprefix("--Valid Readings:").strip().split(" "))
            num_readings = int(
                comment_lines[2].removeprefix("--Valid Readings:").strip().split(" ")[0]
            )
            HRMS_line = comment_lines[10]
            HRMS = Decimal(HRMS_line.removeprefix("--HRMS Avg:").strip().split(" ")[0])
            VRMS_line = comment_lines[11]
            VRMS = Decimal(VRMS_line.removeprefix("--VRMS Avg:").strip().split(" ")[0])
            AGE_line = comment_lines[15]
            AGE = Decimal(AGE_line.removeprefix("--AGE Avg:").strip().split(" ")[0])
        elif comment_lines[2].startswith("--HRMS"):
            # This is a single epoch line
            HRMS_line = comment_lines[2]
            num_readings = 1
            HRMS = Decimal(Rw5Record.get_param(HRMS_line, "HRMS:"))
            VRMS = Decimal(Rw5Record.get_param(HRMS_line, "VRMS:"))
            AGE = Decimal(Rw5Record.get_param(HRMS_line, "AGE:"))
            FIXED = Rw5Record.get_param(HRMS_line, "STATUS:") == "FIXED"

        return (
            cls(
                index=index,
                record_type=record_type,
                content=line,
                machine_state=machine_state,
                comment=comment,
                notes=comment_lines,
                PN=PN,
                _LA=Decimal(LA),
                _LN=Decimal(LN),
                _EL=Decimal(EL),
                N=N,
                E=E,
                EL=EL,
                FIXED=FIXED,
                num_epochs=num_readings,
                HRMS=HRMS,
                VRMS=VRMS,
                AGE=AGE,
            ),
            machine_state,
        )


# endregion
