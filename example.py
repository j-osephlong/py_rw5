from pathlib import Path

from py_rw5.parse.parser import Rw5Parser


if __name__ == "__main__":
    parser = Rw5Parser(Path(r"C:\Users\jlong\Downloads\rw52dat\19194AT230830.rw5"))
    data = parser.parse()
    print(data)
