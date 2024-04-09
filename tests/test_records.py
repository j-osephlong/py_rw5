from decimal import Decimal
from py_rw5.parse.machine_state import MachineState
from py_rw5.parse.record import (
    BacksightRecord,
    GPSRecord,
    JobRecord,
    LineOfSightRecord,
    ModeSetupRecord,
    NoteRecord,
    OccupyRecord,
    OffCenterShotRecord,
    Rw5Record,
    SideshotRecord,
    StorePointRecord,
)


def test_base_record():
    line = "JB,NM19194AT230830,DT08-31-2023,TM07:54:46,--hi"
    r, m = Rw5Record.from_string(0, "JB", line, MachineState())
    assert r.index == 0
    assert r.record_type == "JB"
    assert r.content == line
    assert r.comment == "hi"


def test_note_record():
    line = "--HRMS Avg: 0.0046 SD: 0.0004 Min: 0.0042 Max: 0.0057"
    r, m = NoteRecord.from_string(0, "--", line, MachineState())
    assert r.index == 0
    assert r.record_type == "--"
    assert r.content == line
    print(r.params)
    assert r.params["HRMS Avg"] == "0.0046"
    assert r.params["SD"] == "0.0004"
    assert r.params["Min"] == "0.0042"
    assert r.params["Max"] == "0.0057"


def test_backsight_record():
    line = "BK,OPI1,BPCP5,BS122.5230,BC122.5230"
    r, m = BacksightRecord.from_string(0, "--", line, MachineState())
    assert r.OP == "I1"
    assert r.BP == "CP5"
    assert r.BS.degrees == 122
    assert r.BS.minutes == 52
    assert r.BS.seconds == 30
    assert r.BC.degrees == 122
    assert r.BC.minutes == 52
    assert r.BC.seconds == 30

    assert m.backsight_angle.degrees == 122
    assert m.backsight_angle.minutes == 52
    assert m.backsight_angle.seconds == 30
    assert m.backsight_coord == "CP5"


def test_job_record():
    line = "JB,NM19194AT230830,DT08-31-2023,TM07:54:46,--hi"
    r, m = JobRecord.from_string(0, "JB", line, MachineState())

    assert r.NM == "19194AT230830"
    assert r.DT == "08-31-2023"
    assert r.TM == "07:54:46"


def test_los_record():
    line = "LS,HI1.5450,HR0.2100"
    r, m = LineOfSightRecord.from_string(0, "LS", line, MachineState())

    assert r.HI == Decimal("1.5450")
    assert r.HR == Decimal("0.2100")
    assert m.instrument_height == Decimal("1.5450")
    assert m.rod_height == Decimal("0.2100")


def test_mode_record():
    line = "MO,AD0,UN1,SF1.00000000,EC0,EO0.0,AU0"
    r, m = ModeSetupRecord.from_string(0, "LS", line, MachineState())

    assert r.AD == 0
    assert r.UN == 1
    assert r.SF - 1 < 0.00001
    assert r.EC == 0
    assert r.EO == 0.0
    assert r.AU == 0


def test_occupy_record():
    line = "OC,OPI1,N 7366894.66280,E 2532861.10816,EL44.536,--TEMP"
    r, m = OccupyRecord.from_string(0, "LS", line, MachineState())

    assert r.OP == "I1"
    assert r.N == Decimal("7366894.66280")
    assert r.E == Decimal("2532861.10816")
    assert r.EL == Decimal("44.536")


def test_off_center_shot_record():
    line = "OF,AR90.3333,ZE90.0000,SD25.550000"
    r, m = OffCenterShotRecord.from_string(0, "LS", line, MachineState())

    assert r.AR.degrees == 90
    assert r.AR.minutes == 33
    assert r.AR.seconds == 33
    assert r.ZE.degrees == 90
    assert r.ZE.minutes == 0
    assert r.ZE.seconds == 0
    assert r.SD == Decimal("25.55")


def test_store_point_record():
    line = "SP,PNI2,N 7366894.6465,E 2532861.0966,EL44.3360,--RES"
    r, m = StorePointRecord.from_string(0, "LS", line, MachineState())

    assert r.PN == "I2"
    assert r.N == Decimal("7366894.6465")
    assert r.E == Decimal("2532861.0966")
    assert r.EL == Decimal("44.3360")


def test_store_point_record__resection():
    line = "SP,PNI2,N 7366894.6465,E 2532861.0966,EL44.3360,--RES"
    r, m = StorePointRecord.from_string(0, "LS", line, MachineState())

    assert not r.is_resection

    r.notes.append(NoteRecord.from_string(0, "--", "--DT08-31-2023", MachineState())[0])
    r.notes.append(NoteRecord.from_string(0, "--", "--TM08:28:36", MachineState())[0])
    r.notes.append(
        NoteRecord.from_string(
            0,
            "--",
            "--Resection:HI1.545,PNI1,N 7366894.6628,E 2532861.1082,EL44.5363,--TEMP",
            MachineState(),
        )[0]
    )

    assert r.is_resection


def test_sideshot_record():
    line = "SS,OPI2,FP6033,AR216.0302,ZE85.0032,SD23.398200,--BOLT"
    r, m = SideshotRecord.from_string(0, "LS", line, MachineState())

    assert r.OP == "I2"
    assert r.FP == "6033"
    assert r.AR.degrees == 216
    assert r.AR.minutes == 3
    assert r.AR.seconds == 2
    assert r.ZE.degrees == 85
    assert r.ZE.minutes == 0
    assert r.ZE.seconds == 32
    assert r.SD == Decimal("23.3982")


def test_gps_record():
    line = "GPS,PN6000,LA45.180601572576,LN-66.045114250148,EL30.227095,--CP/CP1"
    r, m = GPSRecord.from_string(0, "LS", line, MachineState())

    assert r.PN == "6000"
    assert r.LA == Decimal("45.180601572576")
    assert r.LN == Decimal("-66.045114250148")
    assert r.EL == Decimal("30.227095")
