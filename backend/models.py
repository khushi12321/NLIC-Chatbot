import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, desc

from sqlalchemy import (
    Index,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Plan(TimestampMixin, Base):
    __tablename__ = "plans"

    __table_args__ = (
        UniqueConstraint("name", "company", name="uq_plans_name_company"),
        CheckConstraint(
            "min_sum_assured IS NULL OR min_sum_assured > 0",
            name="ck_plans_min_sum_assured",
        ),
        CheckConstraint(
            "proposer_entry_age_min IS NULL OR proposer_entry_age_max IS NULL "
            "OR proposer_entry_age_min <= proposer_entry_age_max",
            name="ck_plans_proposer_age_range",
        ),
        # CheckConstraint( --removed because comparing days to years using 365 can reject valid edge cases. Validate exact age rules in the application instead.
        #     "insured_entry_age_max IS NULL OR insured_entry_age_min_days IS NULL "
        #     "OR insured_entry_age_min_days <= insured_entry_age_max * 365",
        #     name="ck_plans_insured_age_range",
        # ),
        CheckConstraint(
            "term_min IS NULL OR term_max IS NULL OR term_min <= term_max",
            name="ck_plans_term_range",
        ),
        CheckConstraint(
            "loan_max_pct_surrender_value IS NULL OR "
            "(loan_max_pct_surrender_value BETWEEN 0 AND 100)",
            name="ck_plans_loan_surrender_pct",
        ),
        CheckConstraint(
            "loan_max_pct_sum_assured IS NULL OR "
            "(loan_max_pct_sum_assured BETWEEN 0 AND 100)",
            name="ck_plans_loan_sum_assured_pct",
        ),
        CheckConstraint(
            "verification_status IN ('draft', 'proofread', 'verified')",
            name="ck_plans_verification_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(Text, nullable=False)
    company: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="Nepal Life Insurance Company Limited",
        server_default="Nepal Life Insurance Company Limited",
    )
    category: Mapped[str] = mapped_column(Text, nullable=False)
    is_with_profit: Mapped[bool] = mapped_column(Boolean, nullable=False)

    purpose_tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    min_sum_assured: Mapped[float | None] = mapped_column(Numeric(14, 2))
    max_sum_assured_rule: Mapped[str | None] = mapped_column(Text)

    proposer_entry_age_min: Mapped[int | None] = mapped_column(SmallInteger)
    proposer_entry_age_max: Mapped[int | None] = mapped_column(SmallInteger)
    insured_entry_age_min_days: Mapped[int | None] = mapped_column(SmallInteger)
    insured_entry_age_max: Mapped[int | None] = mapped_column(SmallInteger)

    term_min: Mapped[int | None] = mapped_column(SmallInteger)
    term_max: Mapped[int | None] = mapped_column(SmallInteger)
    max_maturity_age_proposer: Mapped[int | None] = mapped_column(SmallInteger)
    max_maturity_age_insured: Mapped[int | None] = mapped_column(SmallInteger)

    premium_modes: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    maturity_benefit: Mapped[str | None] = mapped_column(Text)
    commencement_of_risk_rule: Mapped[str | None] = mapped_column(Text)

    surrender_rule: Mapped[str | None] = mapped_column(Text)
    surrender_min_years: Mapped[int | None] = mapped_column(SmallInteger)
    loan_rule: Mapped[str | None] = mapped_column(Text)
    loan_min_years: Mapped[int | None] = mapped_column(SmallInteger)
    loan_max_pct_surrender_value: Mapped[float | None] = mapped_column(Numeric(5, 2))
    loan_max_pct_sum_assured: Mapped[float | None] = mapped_column(Numeric(5, 2))

    source_file: Mapped[str] = mapped_column(Text, nullable=False)
    verification_status: Mapped[str] = mapped_column(
        Text, nullable=False, default="draft", server_default="draft"
    )
    verified_by: Mapped[str | None] = mapped_column(Text)
    verified_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))


class PlanRider(TimestampMixin, Base):
    __tablename__ = "plan_riders"

    __table_args__ = (
        UniqueConstraint("plan_id", "rider_code", name="uq_plan_riders_plan_code"),
        CheckConstraint(
            "entry_age_min IS NULL OR maturity_age_max IS NULL "
            "OR entry_age_min <= maturity_age_max",
            name="ck_plan_riders_age_range",
        ),
        CheckConstraint(
            "applies_to IN ('proposer', 'insured', 'both')",
            name="ck_plan_riders_applies_to",
        ),
        CheckConstraint(
            "verification_status IN ('draft', 'proofread', 'verified')",
            name="ck_plan_riders_verification_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("plans.id", ondelete="CASCADE"),
        nullable=False,
    )

    rider_code: Mapped[str] = mapped_column(Text, nullable=False)
    rider_name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    entry_age_min: Mapped[int | None] = mapped_column(SmallInteger)
    maturity_age_max: Mapped[int | None] = mapped_column(SmallInteger)
    applies_to: Mapped[str] = mapped_column(Text, nullable=False)
    source_reference: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(
        Text, nullable=False, default="draft", server_default="draft"
    )


class PlanScenario(TimestampMixin, Base):
    __tablename__ = "plan_scenarios"

    __table_args__ = (
        Index(
            "ix_plan_scenarios_plan_id_display_order",
            "plan_id",
            "display_order",
        ),
        CheckConstraint(
            "verification_status IN ('draft', 'proofread', 'verified')",
            name="ck_plan_scenarios_verification_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("plans.id", ondelete="CASCADE"),
        nullable=False,
    )

    scenario: Mapped[str] = mapped_column(Text, nullable=False)
    payout: Mapped[str] = mapped_column(Text, nullable=False)
    policy_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    source_reference: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(
        Text, nullable=False, default="draft", server_default="draft"
    )
    verified_by: Mapped[str | None] = mapped_column(Text)
    verified_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))


class FAQ(TimestampMixin, Base):
    __tablename__ = "faqs"

    __table_args__ = (
        CheckConstraint(
            "verification_status IN ('draft', 'proofread', 'verified')",
            name="ck_faqs_verification_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text))

    plan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("plans.id", ondelete="SET NULL"),
    )

    source_reference: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    verification_status: Mapped[str] = mapped_column(
        Text, nullable=False, default="draft", server_default="draft"
    )
    reviewed_by: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))


class MockPolicy(TimestampMixin, Base):
    __tablename__ = "mock_policies"

    __table_args__ = (
        CheckConstraint("sum_assured > 0", name="ck_mock_policies_sum_assured"),
        CheckConstraint("premium_amount >= 0", name="ck_mock_policies_premium_amount"),
        CheckConstraint(
            "maturity_date >= policy_start_date",
            name="ck_mock_policies_maturity_date",
        ),
        CheckConstraint(
            "premium_due_date IS NULL OR premium_due_date >= policy_start_date",
            name="ck_mock_policies_due_date",
        ),
        CheckConstraint(
            "status IN ('active', 'lapsed', 'matured', 'surrendered', 'terminated')",
            name="ck_mock_policies_status",
        ),
        CheckConstraint("is_mock = TRUE", name="ck_mock_policies_is_mock"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    policy_number: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    customer_name: Mapped[str] = mapped_column(Text, nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    registered_email: Mapped[str] = mapped_column(Text, nullable=False)
    registered_phone: Mapped[str | None] = mapped_column(Text)

    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("plans.id", ondelete="RESTRICT"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(Text, nullable=False)
    sum_assured: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    premium_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    premium_mode: Mapped[str] = mapped_column(Text, nullable=False)

    policy_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    maturity_date: Mapped[date] = mapped_column(Date, nullable=False)
    premium_due_date: Mapped[date | None] = mapped_column(Date)

    is_mock: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

class PremiumPayment(Base):
    __tablename__ = "premium_payments"

    __table_args__ = (
        UniqueConstraint(
            "id",
            "policy_id",
            name="uq_premium_payments_id_policy",
        ),
        CheckConstraint("amount >= 0", name="ck_premium_payments_amount"),
        CheckConstraint(
            "period_to >= period_from",
            name="ck_premium_payments_period",
        ),
        Index(
            "ix_premium_payments_policy_id_paid_on",
            "policy_id",
            desc("paid_on"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mock_policies.id", ondelete="CASCADE"),
        nullable=False,
    )

    receipt_number: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    paid_on: Mapped[date] = mapped_column(Date, nullable=False)
    period_from: Mapped[date] = mapped_column(Date, nullable=False)
    period_to: Mapped[date] = mapped_column(Date, nullable=False)

    payment_method: Mapped[str | None] = mapped_column(Text)
    fiscal_year: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

class Claim(TimestampMixin, Base):
    __tablename__ = "claims"

    __table_args__ = (
        CheckConstraint(
            "claim_type IN "
            "('maturity', 'death', 'accidental_death', "
            "'critical_illness', 'disability', 'surrender')",
            name="ck_claims_claim_type",
        ),
        CheckConstraint(
            "status IN "
            "('submitted', 'under_review', 'additional_info_required', "
            "'approved', 'rejected', 'paid')",
            name="ck_claims_status",
        ),
        CheckConstraint(
            "claimed_amount IS NULL OR claimed_amount >= 0",
            name="ck_claims_claimed_amount",
        ),
        CheckConstraint(
            "approved_amount IS NULL OR approved_amount >= 0",
            name="ck_claims_approved_amount",
        ),
        CheckConstraint(
            "decided_on IS NULL OR decided_on >= submitted_on",
            name="ck_claims_decided_on",
        ),
        Index(
            "ix_claims_policy_id_submitted_on",
            "policy_id",
            desc("submitted_on"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mock_policies.id", ondelete="CASCADE"),
        nullable=False,
    )

    claim_reference: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    claim_type: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    status_note: Mapped[str | None] = mapped_column(Text)

    claimed_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    approved_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))

    submitted_on: Mapped[date] = mapped_column(Date, nullable=False)
    decided_on: Mapped[date | None] = mapped_column(Date)

