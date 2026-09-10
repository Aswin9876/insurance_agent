"""Seed script:
1. Generates synthetic data JSON (100 customers, CRM records, claims, enrollments)
2. Creates SQLite tables and seeds Users, Policies from the catalog.
Run:  python backend/seed.py
"""
import json
import os
import random
import string
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import Base, engine, SessionLocal  # noqa: E402
from backend.app.models import Policy, User  # noqa: E402

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

FIRST = ["Aarav", "Maya", "Liam", "Sofia", "Ethan", "Priya", "Noah", "Emma",
         "Rohan", "Aisha", "Lucas", "Chloe", "Kabir", "Zara", "Owen", "Mia",
         "Dev", "Nina", "Jack", "Lea", "Arjun", "Ivy", "Sam", "Nora"]
LAST = ["Sharma", "Patel", "Johnson", "Garcia", "Kim", "Chen", "Smith",
        "Khan", "Mehta", "Brown", "Davis", "Wilson", "Rao", "Lee", "Martin"]
CITIES = ["New York, NY", "Austin, TX", "Seattle, WA", "Chicago, IL",
          "Denver, CO", "Boston, MA", "San Jose, CA", "Miami, FL"]
OCCUPATIONS = ["software_engineer", "teacher", "nurse", "construction",
               "accountant", "truck_driver", "consultant", "retail_worker",
               "mining", "designer", "manager", "farmer"]
CONDITIONS_POOL = ["", "", "", "hypertension", "asthma", "diabetes",
                   "heart_disease", "diabetes,obesity"]
NEEDS_POOL = ["health", "life", "auto", "home", "health,life",
              "health,auto", "life,home", "health,life,auto"]
MARITAL = ["single", "married", "married", "single"]


def gen_customers(n: int = 100):
    random.seed(42)  # reproducible
    customers, crm_customers, crm_policies, crm_claims = [], [], [], []
    for i in range(1, n + 1):
        crm_id = f"CUST-{i:04d}"
        first = random.choice(FIRST)
        last = random.choice(LAST)
        email = f"{first.lower()}.{last.lower()}{i}@example.com"
        phone = f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        age = random.randint(22, 72)
        income = random.choice([28000, 35000, 48000, 55000, 72000, 95000,
                                120000, 150000, 200000])
        customers.append({
            "crm_id": crm_id,
            "first_name": first, "last_name": last,
            "email": email, "phone": phone,
            "age": age, "gender": random.choice(["male", "female"]),
            "location": random.choice(CITIES),
            "occupation": random.choice(OCCUPATIONS),
            "annual_income": income,
            "marital_status": random.choice(MARITAL),
            "health_conditions": random.choice(CONDITIONS_POOL),
            "smoker": random.choice(["no", "no", "no", "yes"]),
            "insurance_needs": random.choice(NEEDS_POOL),
            "budget": round(income * random.uniform(0.02, 0.06)),
            "consent_given": True,
        })
        # ~60% are existing CRM customers
        if random.random() < 0.6:
            crm_customers.append({
                "crm_id": crm_id,
                "first_name": first, "last_name": last, "email": email,
                "customer_since": f"20{random.randint(15, 23)}",
                "loyalty_tier": random.choice(["bronze", "silver", "gold"]),
            })
            # 0-2 prior policies
            for _ in range(random.choice([0, 1, 1, 2])):
                crm_policies.append({
                    "crm_id": crm_id,
                    "product_id": f"POL-{random.randint(1000, 9999)}",
                    "type": random.choice(["health", "life", "auto", "home"]),
                    "status": random.choice(["active", "active", "lapsed"]),
                    "started": f"20{random.randint(18, 23)}",
                })
            # 0-3 claims
            for _ in range(random.choice([0, 0, 1, 1, 2, 3])):
                crm_claims.append({
                    "crm_id": crm_id,
                    "claim_id": "CLM-" + "".join(
                        random.choices(string.digits, k=6)),
                    "type": random.choice(["health", "auto", "home"]),
                    "amount": random.choice([500, 1200, 3500, 8000, 15000,
                                             42000, 130000]),
                    "status": random.choice(["settled", "settled", "pending"]),
                    "date": (datetime.now() -
                             timedelta(days=random.randint(30, 1500))
                             ).strftime("%Y-%m-%d"),
                })
    return customers, crm_customers, crm_policies, crm_claims


def write_json(filename, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"  wrote {path} ({len(data)} records)")


def seed_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Demo user
        if not db.query(User).filter_by(email="demo@agent.ai").first():
            db.add(User(email="demo@agent.ai",
                        hashed_password="demo1234",  # plain for demo simplicity
                        full_name="Demo Agent", role="admin"))
            print("  seeded user demo@agent.ai / demo1234")

        # Policies from catalog
        catalog_path = os.path.join(DATA_DIR, "policy_catalog.json")
        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)
        for p in catalog:
            if not db.query(Policy).filter_by(product_id=p["product_id"]).first():
                db.add(Policy(
                    product_id=p["product_id"], name=p["name"],
                    category=p["category"], premium=p["premium"],
                    coverage=p["coverage"], eligibility=p["eligibility"],
                    risk_appetite=p["risk_appetite"], summary=p["summary"]))
        db.commit()
        print(f"  seeded {len(catalog)} policies")
    finally:
        db.close()


if __name__ == "__main__":
    print("Generating synthetic data...")
    customers, crm_c, crm_p, crm_cl = gen_customers(100)
    write_json("synthetic_customers.json", customers)
    write_json("crm_customers.json", crm_c)
    write_json("crm_policies.json", crm_p)
    write_json("crm_claims.json", crm_cl)
    print("Seeding database...")
    seed_db()
    print("Done ✔")