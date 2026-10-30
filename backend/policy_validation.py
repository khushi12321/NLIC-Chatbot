"""Cross-table validation for mock policies.

A SQL CHECK constraint cannot look at another table, so rules that compare a
policy with its plan live here. Call validate_policy_against_plan() whenever a
mock policy is created or updated (seed script now, admin tools later).

The returned messages are INTERNAL. Never show them to a customer.
"""

from datetime import date
from decimal import Decimal

# Single source of truth for premium mode spellings. Use these exact strings
# in plans.premium_modes and mock_policies.premium_mode.
PREMIUM_MODES = ("yearly", "half_yearly", "quarterly", "monthly", "single")


def age_on(dob: date, on: date) -> int:
    """Completed years between dob and the given date."""
    return on.year - dob.year - ((on.month, on.day) < (dob.month, dob.day))


def validate_policy_against_plan(
    *,
    plan,
    premium_mode: str,
    sum_assured: Decimal,
    policy_start_date: date,
    maturity_date: date,
    proposer_dob: date,
) -> list[str]:
    """Return a list of problems. An empty list means the policy fits the plan.

    Not checked: the insured child's entry age, because mock_policies does not
    store an insured date of birth. Add that column if you want the check.
    """
    problems: list[str] = []

    # Premium mode must be a known value and offered by the plan.
    if premium_mode not in PREMIUM_MODES:
        problems.append(f"premium_mode '{premium_mode}' is not a recognised value")
    if plan.premium_modes is not None and premium_mode not in plan.premium_modes:
        problems.append(f"premium_mode '{premium_mode}' is not offered by this plan")

    # Minimum sum assured.
    if plan.min_sum_assured is not None and sum_assured < plan.min_sum_assured:
        problems.append("sum_assured is below the plan minimum")

    # Policy term in completed years.
    term_years = age_on(policy_start_date, maturity_date)
    if plan.term_min is not None and term_years < plan.term_min:
        problems.append(f"term of {term_years} years is below the plan minimum")
    if plan.term_max is not None and term_years > plan.term_max:
        problems.append(f"term of {term_years} years is above the plan maximum")

    # Proposer age at start and at maturity.
    entry_age = age_on(proposer_dob, policy_start_date)
    if plan.proposer_entry_age_min is not None and entry_age < plan.proposer_entry_age_min:
        problems.append(f"proposer entry age {entry_age} is below the plan minimum")
    if plan.proposer_entry_age_max is not None and entry_age > plan.proposer_entry_age_max:
        problems.append(f"proposer entry age {entry_age} is above the plan maximum")

    maturity_age = age_on(proposer_dob, maturity_date)
    if (
        plan.max_maturity_age_proposer is not None
        and maturity_age > plan.max_maturity_age_proposer
    ):
        problems.append(f"proposer age at maturity ({maturity_age}) exceeds the plan limit")

    return problems