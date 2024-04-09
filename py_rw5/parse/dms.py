"""
Degree-Minutes-Seconds utility class
Author: Joseph Long
"""


class DMS:
    """
    Degrees minutes seconds
    """

    degrees: int
    minutes: int
    seconds: float

    def __init__(self, degrees: int, minutes: int, seconds: float) -> None:
        self.degrees = degrees
        self.minutes = minutes
        self.seconds = seconds

    @classmethod
    def from_str(cls, string: str):
        """
        Convert from a decimal string "123.4567" to DMS
        """
        (part1, rest) = string.split(".", maxsplit=1)
        part2 = rest[:2]
        part3 = rest[2:4]

        return cls(int(part1), int(part2), int(part3))

    def __str__(self) -> str:
        s_part_1, s_part_2 = str(float(self.seconds)).split(".")
        s1 = s_part_1.zfill(2)
        s2 = s_part_2.ljust(2, "0")

        return f"{self.degrees}-{str(self.minutes).zfill(2)}-{s1}.{s2}"

    def __repr__(self) -> str:
        return self.__str__()

    def __sub__(self, other: "DMS"):
        self_degrees = self.dd
        other_degrees = other.dd
        diff = self_degrees - other_degrees

        # If under flowed
        if diff < 0:
            diff += 360

        dms = DMS.from_degrees(diff)

        return dms

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, DMS):
            return False

        return (
            self.degrees == __value.degrees
            and self.minutes == __value.minutes
            and abs(self.seconds - __value.seconds) < 0.00001
        )

    def _decimal_degrees(self):
        """Convert DMS to degrees"""

        return self.degrees + self.minutes / 60 + self.seconds / 3600

    @property
    def dd(self):
        """Decimal Degrees"""
        return self._decimal_degrees()

    @classmethod
    def from_degrees(cls, decimal_degrees: float):
        """Convert from degrees to DMS"""

        d = int(decimal_degrees)
        m = int((decimal_degrees - d) * 60)
        s = float(round((decimal_degrees - d - m / 60) * 3600))

        return cls(d, m, s)
