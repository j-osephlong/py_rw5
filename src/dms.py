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
        s = str(self.seconds)
        s1 = s[:2].zfill(2)
        s2 = s[2:4].ljust(2, "0")

        return f"{self.degrees}-{str(self.minutes).zfill(2)}-{s1}.{s2}"

    def __sub__(self, other: "DMS"):
        self_degrees = self.degrees + self.minutes / 60 + self.seconds / 3600
        other_degrees = other.degrees + other.minutes / 60 + other.seconds / 3600
        diff = self_degrees - other_degrees
        if diff < 0:
            diff += 360
        m, s = divmod(abs(diff) * 3600, 60)
        d, m = divmod(m, 60)
        d, m, s = int(str(d)), int(str(m)), round(s, 2)

        return DMS(d, m, s)
