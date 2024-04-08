from pathlib import Path

from src.parser import Rw5Parser


if __name__ == "__main__":
    parser = Rw5Parser(Path(r"C:\Users\jlong\Downloads\rw52dat\19194AT230830.rw5"))
    parser.parse()
    print(parser)
