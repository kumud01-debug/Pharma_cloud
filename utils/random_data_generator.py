# random_data_generator.py
import random
from datetime import datetime, timedelta
from faker import Faker
from database import db
from models import RawMaterial, QCSample, Specification, TestResult, COA
from sqlalchemy.exc import IntegrityError

fake = Faker()

# Predefined QC parameters for random specs
QC_PARAMETERS = [
    {"parameter": "pH", "unit": "pH units", "method": "USP <791>", "limits": (5.5, 7.5)},
    {"parameter": "Assay", "unit": "%", "method": "HPLC", "limits": (98.0, 102.0)},
    {"parameter": "LOD", "unit": "%", "method": "USP <731>", "limits": (0.0, 2.0)},
    {"parameter": "Appearance", "unit": None, "method": "Visual", "textual": "Complies"},
]

# Fixed pharma raw materials with codes
PHARMA_MATERIALS = {
    "RM001": "Paracetamol",
    "RM002": "Ranitidine",
    "RM003": "Dexamethasone",
    "RM004": "Frusemide",
    "RM005": "Ketoconazole",
    "RM006": "Luliconazole",
    "RM007": "Diclofenac",
    "RM008": "Ciprofloxacin",
    "RM009": "Amoxicillin",
    "RM010": "Metformin"
}


def generate_unique_ar_no():
    """Always return a unique AR number"""
    while True:
        candidate = f"AR-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000,9999)}"
        # Check in DB
        if not QCSample.query.filter_by(ar_no=candidate).first():
            return candidate


def generate_bulk_raw_materials(n=10):
    for _ in range(n):
        # Pick random (code, name) pair
        material_code, material_name = random.choice(list(PHARMA_MATERIALS.items()))

        rm = RawMaterial(
            material_code=material_code,
            material_name=material_name,
            lot_no=f"LOT{random.randint(10000,99999)}",
            vendor=fake.company(),
            received_qty=random.uniform(10, 500),
            unit="kg",
            received_date=fake.date_time_between(start_date="-60d", end_date="now"),
            status="Testing"
        )
        db.session.add(rm)
        db.session.flush()  # ensures rm.id is available

        # Add one sample
        sample = QCSample(
            ar_no=generate_unique_ar_no(),
            sample_date=fake.date_time_between(start_date="-30d", end_date="now"),
            sampler=fake.name(),
            remarks="Random generated sample",
            material_id=rm.id
        )

        db.session.add(sample)
        db.session.flush()

        overall_verdict = "Pass"

        # Add specifications and results
        for spec_data in QC_PARAMETERS:
            spec = Specification(
                material_id=rm.id,
                parameter=spec_data["parameter"],
                method=spec_data["method"],
                unit=spec_data.get("unit"),
                lower_limit=spec_data.get("limits", (None, None))[0],
                upper_limit=spec_data.get("limits", (None, None))[1],
                textual_limit=spec_data.get("textual")
            )
            db.session.add(spec)

            # Generate test result
            if "limits" in spec_data:
                value = random.uniform(spec.lower_limit - 1, spec.upper_limit + 1)
                verdict = "Pass" if spec.lower_limit <= value <= spec.upper_limit else "Fail"
                if verdict == "Fail":
                    overall_verdict = "Fail"
                result = TestResult(
                    sample_id=sample.id,
                    parameter=spec.parameter,
                    result_value=value,
                    unit=spec.unit,
                    verdict=verdict,
                    tested_by=fake.name(),
                )
            else:
                text = "Complies" if random.random() > 0.1 else "Does not comply"
                verdict = "Pass" if text == "Complies" else "Fail"
                if verdict == "Fail":
                    overall_verdict = "Fail"
                result = TestResult(
                    sample_id=sample.id,
                    parameter=spec.parameter,
                    result_text=text,
                    verdict=verdict,
                    tested_by=fake.name(),
                )
            db.session.add(result)

        # Add COA
        coa = COA(
            sample_id=sample.id,
            overall_verdict=overall_verdict,
            notes="Randomly generated COA"
        )
        db.session.add(coa)
        #Update raw material status based on COA
        rm.status = "Pass" if overall_verdict == "Pass" else "Fail"

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # regenerate with fresh AR numbers
        return generate_bulk_raw_materials(n)

    print(f"{n} random raw materials with specs & results generated.")
