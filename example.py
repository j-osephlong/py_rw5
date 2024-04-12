from pathlib import Path
import pprint

from py_rw5.convert.dat_file import Rw5ToDatConverter
from py_rw5.parse.parser import Rw5Parser
from py_rw5.parse.record import StorePointRecord


if __name__ == "__main__":
    parser = Rw5Parser(Path(r"C:\Users\jlong\Downloads\rw52dat\19194AT230830.rw5"))
    data = parser.parse()
    converter = Rw5ToDatConverter(data)

    converter.convert()

    converter.write(Path(r"C:\Users\jlong\Documents\dmsemapping\py_rw5\out.dat"))

    for record in data.records:
        if isinstance(record, StorePointRecord):
            pprint.pprint(record.__dict__)
