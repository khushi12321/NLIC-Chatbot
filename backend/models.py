import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, desc, text, ForeignKeyConstraint

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

class OTPChallenge(Base):
    __tablename__ = "otp_challenges"

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "id", "policy_id",
            name="uq_otp_challenges_id_policy",
        ),
        CheckConstraint(
            "mode IN ('email', 'mock')",
            name="ck_otp_challenges_mode",
        ),
        CheckConstraint(
            "attempt_count BETWEEN 0 AND max_attempts",
            name="ck_otp_challenges_attempt_count",
        ),
        CheckConstraint(
            "expires_at > created_at",
            name="ck_otp_challenges_expiry",
        ),
        Index(
            "ix_otp_challenges_policy_created",
            "policy_id",
            desc("created_at"),
        ),
        Index(
            "ix_otp_challenges_expires_at",
            "expires_at",
        ),
        Index(
            "uq_otp_challenges_one_active_per_policy",
            "policy_id",
            unique=True,
            postgresql_where=text(
                "consumed_at IS NULL AND invalidated_at IS NULL"
            ),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mock_policies.id", ondelete="CASCADE"),
        nullable=False,
    )

    otp_hash: Mapped[str] = mapped_column(Text, nullable=False)

    mode: Mapped[str] = mapped_column(Text, nullable=False)

    expires_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now() + interval '5 minutes'"),
    )

    attempt_count: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        server_default="0",
    )

    max_attempts: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=5,
        server_default="5",
    )

    consumed_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True)
    )

    invalidated_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True)
    )

    send_count: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        server_default="0",
    )

    last_sent_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True)
    )

    delivery_status: Mapped[str | None] = mapped_column(Text)


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "id", "policy_id",
            name="uq_auth_sessions_id_policy",
        ),
        UniqueConstraint(
            "otp_challenge_id",
            name="uq_auth_sessions_otp_challenge",
        ),
        CheckConstraint(
            "expires_at > created_at",
            name="ck_auth_sessions_expiry",
        ),
        ForeignKeyConstraint(
            ["otp_challenge_id", "policy_id"],
            ["otp_challenges.id", "otp_challenges.policy_id"],
            name="fk_auth_sessions_challenge_policy",
            ondelete="SET NULL (otp_challenge_id)",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    token_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
    )

    policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mock_policies.id", ondelete="CASCADE"),
        nullable=False,
    )

    otp_challenge_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True)
    )

    csrf_token_hash: Mapped[str] = mapped_column(Text, nullable=False)

    expires_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now() + interval '15 minutes'"),
    )

    last_seen_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True)
    )

    revoked_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True)
    )


class SupportTicket(TimestampMixin, Base):
    __tablename__ = "support_tickets"

    __table_args__ = (
        CheckConstraint(
            "category IN ('general_inquiry', 'policy_issue', 'claim', "
            "'premium_payment', 'document_issue', 'complaint', 'technical', 'other')",
            name="ck_support_tickets_category",
        ),
        CheckConstraint(
            "contact_method IN ('email', 'phone')",
            name="ck_support_tickets_contact_method",
        ),
        CheckConstraint(
            "status IN ('open', 'in_progress', 'resolved', 'closed')",
            name="ck_support_tickets_status",
        ),
        CheckConstraint(
            "priority IN ('low', 'normal', 'high', 'urgent')",
            name="ck_support_tickets_priority",
        ),
        CheckConstraint(
            "length(trim(issue_summary)) BETWEEN 1 AND 2000",
            name="ck_support_tickets_issue_summary_length",
        ),
        CheckConstraint(
            "resolved_at IS NULL OR resolved_at >= created_at",
            name="ck_support_tickets_resolved_at",
        ),
        Index("ix_support_tickets_status_priority_created", "status", "priority", "created_at"),
        Index("ix_support_tickets_category", "category"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticket_reference: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    idempotency_key: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True
    )
    category: Mapped[str] = mapped_column(Text, nullable=False)
    issue_summary: Mapped[str] = mapped_column(Text, nullable=False)
    customer_name: Mapped[str] = mapped_column(Text, nullable=False)
    contact_method: Mapped[str] = mapped_column(Text, nullable=False)
    contact_value: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="open", server_default="open"
    )
    priority: Mapped[str] = mapped_column(
        Text, nullable=False, default="normal", server_default="normal"
    )
    question_excerpt: Mapped[str | None] = mapped_column(Text)
    related_policy_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mock_policies.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))


class DocumentRequest(Base):
    __tablename__ = "document_requests"

    __table_args__ = (
        UniqueConstraint(
            "id", "policy_id", name="uq_document_requests_id_policy"
        ),
        CheckConstraint(
            "document_type IN ('premium_receipt', 'tax_certificate', 'policy_bond')",
            name="ck_document_requests_document_type",
        ),
        CheckConstraint(
            "status IN ('requested', 'generated', 'delivered', 'failed')",
            name="ck_document_requests_status",
        ),
        ForeignKeyConstraint(
            ["auth_session_id", "policy_id"],
            ["auth_sessions.id", "auth_sessions.policy_id"],
            name="fk_document_requests_session_policy",
            ondelete="SET NULL (auth_session_id)",
        ),
        ForeignKeyConstraint(
            ["payment_id", "policy_id"],
            ["premium_payments.id", "premium_payments.policy_id"],
            name="fk_document_requests_payment_policy",
            ondelete="SET NULL (payment_id)",
        ),
        Index(
            "ix_document_requests_policy_requested",
            "policy_id",
            desc("requested_at"),
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
    auth_session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    payment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    document_type: Mapped[str] = mapped_column(Text, nullable=False)
    fiscal_year: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="requested", server_default="requested"
    )
    delivery_destination_masked: Mapped[str | None] = mapped_column(Text)
    failure_code: Mapped[str | None] = mapped_column(Text)
    requested_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    generated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )