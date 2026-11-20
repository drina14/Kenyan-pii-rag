import json
import random
import re
from collections import Counter

import sys
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 42
OUT = sys.argv[2] if len(sys.argv) > 2 else "data/records_large.json"
random.seed(SEED)

FIRST = ["Wanjiru", "Brian", "Aisha", "Kevin", "Grace", "Fatuma", "John", "Mercy", "Peter",
         "Njeri", "Otieno", "Achieng", "Kiptoo", "Amina", "Samuel", "Faith", "Hassan", "Cheptoo",
         "Mutua", "Naliaka"]
LAST = ["Kamau", "Otieno", "Mohamed", "Mwangi", "Njeri", "Hassan", "Odhiambo", "Chebet", "Kiprop",
        "Wafula", "Mutiso", "Abdi", "Korir", "Wekesa", "Akinyi", "Maina", "Barasa", "Ndungu"]


def digits(n):
    return str(random.randint(10 ** (n - 1), 10 ** n - 1))


def new_id():
    return digits(random.choice([7, 8]))


def new_decoy():
    return digits(random.choice([7, 8]))


def new_name():
    f, l = random.choice(FIRST), random.choice(LAST)
    style = random.choice(["normal", "normal", "reversed", "initial"])
    if style == "reversed":
        return f"{l} {f}"
    if style == "initial":
        return f"{f[0]}. {l}"
    return f"{f} {l}"


def new_phone():
    p = random.choice(["7", "1"]) + digits(2)  
    rest = digits(6)
    return random.choice([
        f"+254{p}{rest}",
        f"+254 {p} {rest[:3]} {rest[3:]}",
        f"0{p} {rest[:3]} {rest[3:]}",
        f"0{p}{rest}",
        f"0{p}-{rest[:3]}-{rest[3:]}",
        f"254{p}{rest}",
    ])


def new_date():
    return f"{random.randint(1, 28):02d}/{random.randint(1, 12):02d}/2026"


TEMPLATES = [
    ("id_label_before", "Patient {PERSON}, national ID {ID}, phone {PHONE}, invoice {DECOY}."),
    ("id_label_before", "{PERSON} (ID No: {ID}) can be reached on {PHONE}. Appointment ref {DECOY}."),
    ("id_label_before", "Please confirm the patient {PERSON}, ID {ID}, on {PHONE}."),
    ("id_label_before", "{PERSON} presented national ID {ID} at reception. Receipt number {DECOY}."),
    ("id_label_before", "Contact {PERSON} on {PHONE}. Identity card number: {ID}."),
    ("id_label_before", "Referral for {PERSON}, ID number {ID}. Claim {DECOY} was submitted on {DATE}."),
    ("id_no_label", "Patient {PERSON} ({ID}) was seen on {DATE}. Invoice {DECOY} is pending."),
    ("id_no_label", "Visit note for {ID}: {PERSON} reported a headache. Call {PHONE} to follow up."),
    ("id_label_after", "Records for {PERSON} - {ID} (national ID) were updated on {DATE}."),
    ("phone_name_only", "Reminder: call {PERSON} on {PHONE} to confirm the {DATE} appointment."),
    ("name_only", "Dr. {PERSON} reviewed file {DECOY} during the morning round."),
    ("decoy_only", "Billing code {DECOY} was applied to claim {DECOY2} for the clinic."),
    ("decoy_only", "Pharmacy order {DECOY} was dispatched on {DATE}."),
    ("decoy_only", "Lab ticket {DECOY} is awaiting results. Invoice {DECOY2} has been paid."),
]

LABELS = {"PERSON": "PERSON", "ID": "KE_NATIONAL_ID", "PHONE": "PHONE_NUMBER"}
MAKERS = {"PERSON": new_name, "ID": new_id, "PHONE": new_phone, "DATE": new_date,
          "DECOY": new_decoy, "DECOY2": new_decoy}


def build(tag, template, rec_id):
    text, entities, last = "", [], 0
    used = set()
    for m in re.finditer(r"\{(\w+)\}", template):
        text += template[last:m.start()]
        slot = m.group(1)
        value = MAKERS[slot]()
        while value in used:          
            value = MAKERS[slot]()
        used.add(value)
        text += value
        if slot in LABELS:
            entities.append([value, LABELS[slot]])
        last = m.end()
    text += template[last:]
    return {"id": rec_id, "tag": tag, "text": text, "entities": entities}


records = []
for i in range(1, 151):
    tag, template = random.choice(TEMPLATES)
    records.append(build(tag, template, i))

json.dump(records, open(OUT, "w", encoding="utf-8"), indent=1)

print(f"{len(records)} records written to {OUT} (seed {SEED})")
print("By tag:", dict(Counter(r["tag"] for r in records)))
print("Entities:", dict(Counter(e[1] for r in records for e in r["entities"])))
print("Example:", records[0]["text"])