"""
Test data for AD extraction pipeline.

Contains the 10 test aircraft configurations and 3 verification examples
from the assignment.
"""

from models import AircraftConfiguration, ModificationReference


# 10 Test Aircraft Configurations from Assignment
TEST_AIRCRAFT = [
    AircraftConfiguration(
        model="MD-11",
        msn=48123,
        modifications_applied=[]
    ),
    AircraftConfiguration(
        model="DC-10-30F",
        msn=47890,
        modifications_applied=[]
    ),
    AircraftConfiguration(
        model="Boeing 737-800",
        msn=30123,
        modifications_applied=[]
    ),
    AircraftConfiguration(
        model="A320-214",
        msn=5234,
        modifications_applied=[]
    ),
    AircraftConfiguration(
        model="A320-232",
        msn=6789,
        modifications_applied=[
            ModificationReference(type="mod", identifier="24591", phase="production")
        ]
    ),
    AircraftConfiguration(
        model="A320-214",
        msn=7456,
        modifications_applied=[
            ModificationReference(type="sb", identifier="A320-57-1089", revision="04")
        ]
    ),
    AircraftConfiguration(
        model="A321-111",
        msn=8123,
        modifications_applied=[]
    ),
    AircraftConfiguration(
        model="A321-112",
        msn=364,
        modifications_applied=[
            ModificationReference(type="mod", identifier="24977", phase="production")
        ]
    ),
    AircraftConfiguration(
        model="A319-100",
        msn=9234,
        modifications_applied=[]
    ),
    AircraftConfiguration(
        model="MD-10-10F",
        msn=46234,
        modifications_applied=[]
    ),
]


# 3 Verification Examples from Assignment
VERIFICATION_EXAMPLES = [
    {
        "aircraft": AircraftConfiguration(
            model="MD-11F",
            msn=48400,
            modifications_applied=[]
        ),
        "expected": {
            "FAA-2025-23-53": True,   # ✅ Affected
            "EASA-2025-0254": False   # ❌ Not applicable
        }
    },
    {
        "aircraft": AircraftConfiguration(
            model="A320-214",
            msn=4500,
            modifications_applied=[
                ModificationReference(type="mod", identifier="24591", phase="production")
            ]
        ),
        "expected": {
            "FAA-2025-23-53": False,  # ❌ Not applicable
            "EASA-2025-0254": False   # ❌ Not affected (excluded by mod)
        }
    },
    {
        "aircraft": AircraftConfiguration(
            model="A320-214",
            msn=4500,
            modifications_applied=[]
        ),
        "expected": {
            "FAA-2025-23-53": False,  # ❌ Not applicable
            "EASA-2025-0254": True    # ✅ Affected
        }
    },
]
