"""Seed the NLIC chatbot database with the Ketaketi plan and FICTIONAL demo data.

Usage (from the backend folder):
    python seed.py            # insert or update seed data (safe to re-run)
    python seed.py --reset    # first delete mock policies and their dependants

Rules this script follows:
- Plan data is loaded as 'draft'. It must be proofread by a person against the
  brochure before verification_status is changed. Re-running the script never
  overwrites a status that someone has already set.
- All policyholder data is fictional. Premium amounts are invented because the
  brochure contains no premium rates.
- Tickets are never touched.
"""

import argparse
import os
from datetime import date
from decimal import Decimal

from dotenv import load_dotenv
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session

from models import (
    AuthSession,
    Claim,
    DocumentRequest,
    MockPolicy,
    OTPChallenge,
    Plan,
    PlanRider,
    PlanScenario,
    PremiumPayment,
)
from policy_validation import validate_policy_against_plan

load_dotenv()

# Fields a person sets during proofreading. Seeding must never overwrite them.
REVIEW_FIELDS = {"verification_status", "verified_by", "verified_at"}

# The email that receives real OTP codes in email mode. Set SEED_DEMO_EMAIL in
# .env to an inbox you control. The other addresses are placeholders.
DEMO_EMAIL = os.getenv("SEED_DEMO_EMAIL", "demo.policyholder1@example.com")

# ---------------------------------------------------------------------------
# Plan data: extraction draft from the brochure (context Section 14.5).
# TO DO: proofread every value against the PDF, then set the status by hand.
# ---------------------------------------------------------------------------
PLAN_NAME = "Ketaketi Sunaulo Bhawishya Jeevan Bemma Yojana (With Profit)"
COMPANY = "Nepal Life Insurance Company Limited"

PLAN = {
    "name": PLAN_NAME,
    "company": COMPANY,
    "category": "Child endowment",
    "is_with_profit": True,
    "purpose_tags": ["child_education", "savings"],  # my assumption, confirm
    "min_sum_assured": Decimal("25000.00"),
    "max_sum_assured_rule": "As per source and level of income",
    "proposer_entry_age_min": 21,
    "proposer_entry_age_max": 65,
    "insured_entry_age_min_days": 30,  # 1 month (30 days completed)
    "insured_entry_age_max": 17,
    "term_min": 5,
    "term_max": 25,
    "max_maturity_age_proposer": 70,
    "max_maturity_age_insured": 25,
    "premium_modes": ["yearly", "half_yearly", "quarterly", "monthly", "single"],
    "maturity_benefit": (
        "Sum assured plus accrued bonus is paid to the insured at maturity."
    ),
    "commencement_of_risk_rule": (
        "Child risk begins either two years after policy start or on the policy "
        "anniversary after the child completes five years of age, whichever is "
        "earlier. Proposer risk cover starts at policy commencement."
    ),
    "surrender_rule": (
        "Allowed only after completion of three full policy years, if premiums "
        "have been paid for at least three years. The surrender value follows "
        "Nepal Insurance Authority guidelines."
    ),
    "surrender_min_years": 3,
    "loan_rule": (
        "Available only after three full policy years, for regular and single "
        "premium. Up to 90% of the surrender value or 25% of the sum assured "
        "plus accrued bonus, whichever is lower. If both child and proposer "
        "die, the loan amount is deducted from the benefit payable."
    ),
    "loan_min_years": 3,
    "loan_max_pct_surrender_value": Decimal("90.00"),
    "loan_max_pct_sum_assured": Decimal("25.00"),  # 25% of (sum assured + bonus)
    "source_file": "brochure-final-sunaulo-bhabisya-keta-keti.pdf",
}

RIDERS = [
    {
        "rider_code": "ADB",
        "rider_name": "Accidental Death Benefit (ADB)",
    },
    {
        "rider_code": "ADB_PTD_PWB",
        "rider_name": "ADB / Permanent Total Disability / Premium Waiver Benefit",
    },
    {
        "rider_code": "CI",
        "rider_name": "Critical Illness (CI)",
    },
]
RIDER_COMMON = {
    "applies_to": "proposer",
    "entry_age_min": 21,
    "maturity_age_max": 70,
}

SCENARIOS = [
    {
        "display_order": 1,
        "scenario": "Child dies before risk commencement",
        "payout": "Paid premium, excluding rider and extra-rated premium.",
        "policy_outcome": "Terminated",
    },
    {
        "display_order": 2,
        "scenario": (
            "Child dies after risk commencement while the proposer is alive"
        ),
        "payout": (
            "Higher of 25% of the sum assured plus accrued bonus, or the paid "
            "premium excluding rider and extra-rated premium."
        ),
        "policy_outcome": "Terminated",
    },
    {
        "display_order": 3,
        "scenario": "Proposer dies while the child is alive",
        "payout": (
            "1% of the sum assured as monthly income until maturity. Premiums "
            "are waived until maturity. Sum assured plus accrued bonus is paid "
            "at maturity."
        ),
        "policy_outcome": "Continues",
    },
    {
        "display_order": 4,
        "scenario": "Child dies after the proposer's death",
        "payout": (
            "Higher of 25% of the sum assured plus accrued bonus, or the paid "
            "premium excluding rider and extra-rated premium."
        ),
        "policy_outcome": "Terminated",
    },
    {
        "display_order": 5,
        "scenario": "Proposer and child die at the same time",
        "payout": (
            "100% of the sum assured plus accrued bonus for proposer coverage, "
            "plus 25% of the sum assured for child coverage."
        ),
        "policy_outcome": "Terminated",
    },
]

# ---------------------------------------------------------------------------
# FICTIONAL policyholders. Names are labelled "Demo" on purpose.
# date_of_birth is the proposer's. Amounts are invented.
# ---------------------------------------------------------------------------
POLICIES = [
    {
        "policy_number": "NLIC-DEMO-0001",
        "customer_name": "Anil Demo Thapa",
        "date_of_birth": date(1985, 3, 12),
        "registered_email": DEMO_EMAIL,
        "status": "active",
        "sum_assured": Decimal("500000.00"),
        "premium_amount": Decimal("2500.00"),
        "premium_mode": "monthly",
        "policy_start_date": date(2023, 4, 14),
        "maturity_date": date(2038, 4, 14),
        "premium_due_date": date(2026, 11, 14),
    },
    {
        "policy_number": "NLIC-DEMO-0002",
        "customer_name": "Sita Demo Gurung",
        "date_of_birth": date(1978, 9, 2),
        "registered_email": "demo.policyholder2@example.com",
        "status": "active",
        "sum_assured": Decimal("750000.00"),
        "premium_amount": Decimal("30000.00"),
        "premium_mode": "yearly",
        "policy_start_date": date(2021, 1, 15),
        "maturity_date": date(2041, 1, 15),
        "premium_due_date": date(2027, 1, 15),
    },
    {
        "policy_number": "NLIC-DEMO-0003",
        "customer_name": "Ram Demo Shrestha",
        "date_of_birth": date(1990, 11, 20),
        "registered_email": "demo.policyholder3@example.com",
        "status": "lapsed",
        "sum_assured": Decimal("300000.00"),
        "premium_amount": Decimal("8000.00"),
        "premium_mode": "quarterly",
        "policy_start_date": date(2022, 7, 1),
        "maturity_date": date(2032, 7, 1),
        "premium_due_date": date(2026, 1, 1),
    },
]

# fiscal_year strings are demo labels. Confirm the format NLIC documents use.
PAYMENTS = [
    ("NLIC-DEMO-0001", "RCPT-DEMO-0001", "2500.00", date(2026, 8, 12), date(2026, 8, 14), date(2026, 9, 13), "online", "2083/84"),
    ("NLIC-DEMO-0001", "RCPT-DEMO-0002", "2500.00", date(2026, 9, 12), date(2026, 9, 14), date(2026, 10, 13), "online", "2083/84"),
    ("NLIC-DEMO-0001", "RCPT-DEMO-0003", "2500.00", date(2026, 10, 12), date(2026, 10, 14), date(2026, 11, 13), "online", "2083/84"),
    ("NLIC-DEMO-0002", "RCPT-DEMO-0004", "30000.00", date(2026, 1, 10), date(2026, 1, 15), date(2027, 1, 14), "bank_transfer", "2082/83"),
    ("NLIC-DEMO-0003", "RCPT-DEMO-0005", "8000.00", date(2025, 9, 28), date(2025, 10, 1), date(2025, 12, 31), "cash", "2082/83"),
]

CLAIMS = [
    {
        "policy_number": "NLIC-DEMO-0002",
        "claim_reference": "CLM-DEMO-0001",
        "claim_type": "critical_illness",
        "status": "under_review",
        "status_note": "Documents received and under review.",
        "claimed_amount": Decimal("500000.00"),
        "submitted_on": date(2026, 9, 20),
    },
    {
        "policy_number": "NLIC-DEMO-0003",
        "claim_reference": "CLM-DEMO-0002",
        "claim_type": "surrender",
        "status": "additional_info_required",
        "status_note": "Additional information is required to continue.",
        "claimed_amount": None,
        "submitted_on": date(2026, 3, 10),
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def apply_fields(obj, values: dict, protect: set[str] = frozenset()) -> None:
    """Copy values onto obj, skipping protected (human-reviewed) fields."""
    for key, value in values.items():
        if key not in protect:
            setattr(obj, key, value)


def seed_plan(session: Session) -> Plan:
    plan = session.scalar(
        select(Plan).where(Plan.name == PLAN_NAME, Plan.company == COMPANY)
    )
    if plan is None:
        plan = Plan(**PLAN, verification_status="draft")
        session.add(plan)
    else:
        apply_fields(plan, PLAN, protect=REVIEW_FIELDS)
    session.flush()
    return plan


def seed_riders(session: Session, plan: Plan) -> None:
    for rider in RIDERS:
        values = {**RIDER_COMMON, **rider}
        existing = session.scalar(
            select(PlanRider).where(
                PlanRider.plan_id == plan.id,
                PlanRider.rider_code == rider["rider_code"],
            )
        )
        if existing is None:
            session.add(PlanRider(plan_id=plan.id, verification_status="draft", **values))
        else:
            apply_fields(existing, values, protect=REVIEW_FIELDS)
    session.flush()


def seed_scenarios(session: Session, plan: Plan) -> None:
    for scenario in SCENARIOS:
        existing = session.scalar(
            select(PlanScenario).where(
                PlanScenario.plan_id == plan.id,
                PlanScenario.display_order == scenario["display_order"],
            )
        )
        if existing is None:
            session.add(
                PlanScenario(plan_id=plan.id, verification_status="draft", **scenario)
            )
        else:
            apply_fields(existing, scenario, protect=REVIEW_FIELDS)
    session.flush()


def seed_policies(session: Session, plan: Plan) -> dict[str, MockPolicy]:
    by_number: dict[str, MockPolicy] = {}
    for data in POLICIES:
        problems = validate_policy_against_plan(
            plan=plan,
            premium_mode=data["premium_mode"],
            sum_assured=data["sum_assured"],
            policy_start_date=data["policy_start_date"],
            maturity_date=data["maturity_date"],
            proposer_dob=data["date_of_birth"],
        )
        if problems:
            raise ValueError(f"{data['policy_number']}: " + "; ".join(problems))

        policy = session.scalar(
            select(MockPolicy).where(MockPolicy.policy_number == data["policy_number"])
        )
        if policy is None:
            policy = MockPolicy(plan_id=plan.id, is_mock=True, **data)
            session.add(policy)
        else:
            apply_fields(policy, data)
            policy.plan_id = plan.id
        by_number[data["policy_number"]] = policy
    session.flush()
    return by_number


def seed_payments(session: Session, policies: dict[str, MockPolicy]) -> None:
    for number, receipt, amount, paid_on, p_from, p_to, method, fy in PAYMENTS:
        values = {
            "policy_id": policies[number].id,
            "amount": Decimal(amount),
            "paid_on": paid_on,
            "period_from": p_from,
            "period_to": p_to,
            "payment_method": method,
            "fiscal_year": fy,
        }
        existing = session.scalar(
            select(PremiumPayment).where(PremiumPayment.receipt_number == receipt)
        )
        if existing is None:
            session.add(PremiumPayment(receipt_number=receipt, **values))
        else:
            apply_fields(existing, values)
    session.flush()


def seed_claims(session: Session, policies: dict[str, MockPolicy]) -> None:
    for data in CLAIMS:
        values = {k: v for k, v in data.items() if k != "policy_number"}
        values["policy_id"] = policies[data["policy_number"]].id
        existing = session.scalar(
            select(Claim).where(Claim.claim_reference == data["claim_reference"])
        )
        if existing is None:
            session.add(Claim(**values))
        else:
            apply_fields(existing, values)
    session.flush()


def reset_mock_data(session: Session) -> None:
    """Delete mock policies and everything that depends on them.

    Order matters: document_requests.policy_id is ON DELETE RESTRICT, so those
    rows must go first. Support tickets are kept (their policy link becomes
    NULL automatically).
    """
    for model in (
        DocumentRequest,
        AuthSession,
        OTPChallenge,
        Claim,
        PremiumPayment,
        MockPolicy,
    ):
        session.execute(delete(model))


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo data.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="delete mock policies and dependants before seeding",
    )
    args = parser.parse_args()

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is not set (check backend/.env).")

    engine = create_engine(database_url)
    with Session(engine) as session, session.begin():
        if args.reset:
            reset_mock_data(session)
        plan = seed_plan(session)
        seed_riders(session, plan)
        seed_scenarios(session, plan)
        policies = seed_policies(session, plan)
        seed_payments(session, policies)
        seed_claims(session, policies)

    print(
        f"Seeded 1 plan ({len(RIDERS)} riders, {len(SCENARIOS)} scenarios), "
        f"{len(POLICIES)} mock policies, {len(PAYMENTS)} payments, "
        f"{len(CLAIMS)} claims."
    )
    print("Plan verification_status is 'draft' until a person proofreads it.")


if __name__ == "__main__":
    main()