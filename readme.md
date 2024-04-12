# PyRw5 - WIP Carlson Rw5 library

Author: Joseph Long

Made for DMSE

## Breakdown

Parses Carlson-format Rw5 files into a more code friendly python dataclass representation allowing for easy manipulation and processing.

Also includes a converter from this representation to the STAR*NET .dat data format.

This is not a full implementation of either the Carlson Rw5 or STAR\*NET .dat formats, and is mostly concerned with GPS, SP, SS, BK, and LS records from the Rw5 file when it comes to the STAR\*NET conversion.

## Reading a Rw5 file

``` py
from py_rw5.parse import Rw5Parser

parser = Rw5Parser(
    path="path/to.file",
    encoding="utf-8",
    substitute_point_names=True,
    substitute_point_comment_prefix="CP/"
)

data = parser.parse()

```

### Substitute point names

The parser can be configured to replace point names in GPS and SS records with a name included in the comment of the record. By default it uses the name following "CP/" in the comment.

`GPS,PN6000,LA45.180601572576,LN-66.045114250148,EL30.227095,--CP/CP1`

In this line, PN6000 turns into PNCP1. In SS records the FP field is substituted instead.

## Converting to STAR*NET  .dat

``` py
from py_rw5.parse import Rw5Parser
from py_rw5.convert import Rw5ToDatConverter

# Same as before
parser = Rw5Parser(
    path="path/to.file",
    encoding="utf-8",
    substitute_point_names=True,
    substitute_point_comment_prefix="CP/"
)

data = parser.parse()

converter = Rw5ToDatConverter(data)

# You can just convert to an array of .dat lines
converter.convert()
print(converter.dat_file_lines)

# Or write it to a file
converter.convert() # still required
converter.write("path/to.out")
```

## Rw5Data

Calling parse returns a Rw5Data object, which holds an ordered list of all of it's records as Rw5Record objects.

### Rw5Record

Rw5Record is subclassed by each supported record type. For example:

``` py
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
```

Records also include a copy of the "machine_state" at the point in time it was processed. 

Machine state includes the current backsight coordinate name, the backsight angle (in DMS), as well as the instrument height and rod height from LS rw5 records.

### DMS
Degree-Seconds-Minutes come up a lot when handling these types of files, and so a DMS utility class is included at `py_wr5.parser.dms.DMS`. 

This includes a from_str function to convert from a string formatted as 'DD.MMSS'.

It also includes \_\_str\_\_ to convert to DD-MM-SS.

It also includes a from_degrees function to convert from a decimal-degrees float.

Subtraction is implemented as well (it was the only OP I needed), and other operations would be just as easy to implement.
