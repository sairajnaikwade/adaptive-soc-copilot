"""
Initial database schema — all 17 tables for Adaptive SOC CoPilot.

Revision ID: 001
Revises: (none — this is the initial migration)
Create Date: 2026-07-23

Tables created (in FK dependency order):
    1.  tenants
    2.  users
    3.  monitored_accounts
    4.  ml_models
    5.  rule_definitions
    6.  auth_events
    7.  activity_events
    8.  feature_vectors
    9.  feature_values
    10. threat_events
    11. shap_contributions
    12. rule_evaluations
    13. response_actions
    14. honeypot_sessions
    15. reports
    16. analyst_feedback
    17. retraining_runs

PostgreSQL ENUM types created before tables:
    userrole, monitoredaccountstatus, autheventtype, activityeventtype,
    mlmodeltype, risktier, threateventstatus, ruleconditionfield,
    ruleconditionoperator, ruleevaluationresult, responseactiontype,
    responseactionstatus, reporttype, reportstatus, analystverdict,
    retrainingstatus
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


# =============================================================================
# PostgreSQL ENUM type definitions
# =============================================================================

userrole_enum = postgresql.ENUM(
    "admin", "analyst", name="userrole", create_type=False
)
monitored_account_status_enum = postgresql.ENUM(
    "active", "suspended", "blocked", "honeypot", "inactive",
    name="monitoredaccountstatus", create_type=False,
)
auth_event_type_enum = postgresql.ENUM(
    "login_success", "login_failure", "logout", "password_reset",
    "mfa_challenge", "mfa_success", "mfa_failure", "account_locked",
    name="autheventtype", create_type=False,
)
activity_event_type_enum = postgresql.ENUM(
    "file_download", "file_upload", "data_export", "privilege_change",
    "api_call", "config_change", "data_access", "report_download",
    name="activityeventtype", create_type=False,
)
ml_model_type_enum = postgresql.ENUM(
    "isolation_forest", "one_class_svm",
    name="mlmodeltype", create_type=False,
)
risk_tier_enum = postgresql.ENUM(
    "low", "medium", "high",
    name="risktier", create_type=False,
)
threat_event_status_enum = postgresql.ENUM(
    "open", "acknowledged", "resolved", "false_positive",
    name="threateventstatus", create_type=False,
)
rule_condition_field_enum = postgresql.ENUM(
    "trust_score", "confidence_score", "anomaly_score",
    name="ruleconditionfield", create_type=False,
)
rule_condition_operator_enum = postgresql.ENUM(
    "lt", "gt", "lte", "gte", "eq",
    name="ruleconditionoperator", create_type=False,
)
rule_evaluation_result_enum = postgresql.ENUM(
    "matched", "not_matched",
    name="ruleevaluationresult", create_type=False,
)
response_action_type_enum = postgresql.ENUM(
    "monitor", "notify_analyst", "trigger_mfa", "restrict_privileges",
    "block_account", "terminate_session", "redirect_honeypot",
    name="responseactiontype", create_type=False,
)
response_action_status_enum = postgresql.ENUM(
    "pending", "executed", "failed", "reverted",
    name="responseactionstatus", create_type=False,
)
report_type_enum = postgresql.ENUM(
    "daily", "weekly", "monthly", "on_demand",
    name="reporttype", create_type=False,
)
report_status_enum = postgresql.ENUM(
    "generating", "completed", "failed", "sent",
    name="reportstatus", create_type=False,
)
analyst_verdict_enum = postgresql.ENUM(
    "true_positive", "false_positive", "needs_review",
    name="analystverdict", create_type=False,
)
retraining_status_enum = postgresql.ENUM(
    "pending", "running", "completed", "failed",
    name="retrainingstatus", create_type=False,
)

ALL_ENUMS = [
    userrole_enum, monitored_account_status_enum, auth_event_type_enum,
    activity_event_type_enum, ml_model_type_enum, risk_tier_enum,
    threat_event_status_enum, rule_condition_field_enum,
    rule_condition_operator_enum, rule_evaluation_result_enum,
    response_action_type_enum, response_action_status_enum,
    report_type_enum, report_status_enum, analyst_verdict_enum,
    retraining_status_enum,
]


def upgrade() -> None:
    """Create all 16 PostgreSQL ENUM types and all 17 tables."""

    conn = op.get_bind()

    # -------------------------------------------------------------------------
    # Step 1: Create all PostgreSQL ENUM types
    # -------------------------------------------------------------------------
    for enum_type in ALL_ENUMS:
        enum_type.create(conn, checkfirst=True)

    # -------------------------------------------------------------------------
    # Step 2: Table — tenants (root, no FKs)
    # -------------------------------------------------------------------------
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)

    # -------------------------------------------------------------------------
    # Step 3: Table — users (FK: tenant_id → tenants)
    # -------------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", userrole_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_index("ix_users_email", "users", ["email"])
    # Per-tenant email uniqueness
    op.create_index("uq_users_tenant_email", "users", ["tenant_id", "email"], unique=True)

    # -------------------------------------------------------------------------
    # Step 4: Table — monitored_accounts (FK: tenant_id → tenants)
    # -------------------------------------------------------------------------
    op.create_table(
        "monitored_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_user_id", sa.String(255), nullable=False),
        sa.Column("username", sa.String(255), nullable=False),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("department", sa.String(255), nullable=True),
        sa.Column("current_trust_score", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column("status", monitored_account_status_enum, nullable=False, server_default="active"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "external_user_id", name="uq_monitored_accounts_tenant_external_user"),
    )
    op.create_index("ix_monitored_accounts_tenant_id", "monitored_accounts", ["tenant_id"])
    op.create_index("ix_monitored_accounts_status", "monitored_accounts", ["status"])

    # -------------------------------------------------------------------------
    # Step 5: Table — ml_models (FK: tenant_id → tenants)
    # -------------------------------------------------------------------------
    op.create_table(
        "ml_models",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_type", ml_model_type_enum, nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("file_path", sa.String(1024), nullable=False),
        sa.Column("training_samples", sa.Integer(), nullable=True),
        sa.Column("training_accuracy", sa.Float(), nullable=True),
        sa.Column("contamination_rate", sa.Float(), nullable=True),
        sa.Column("hyperparameters", sa.Text(), nullable=True),
        sa.Column("trained_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_ml_models_tenant_id", "ml_models", ["tenant_id"])
    op.create_index("ix_ml_models_is_active", "ml_models", ["is_active"])

    # -------------------------------------------------------------------------
    # Step 6: Table — rule_definitions (FK: tenant_id → tenants)
    # -------------------------------------------------------------------------
    op.create_table(
        "rule_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("condition_field", rule_condition_field_enum, nullable=False),
        sa.Column("condition_operator", rule_condition_operator_enum, nullable=False),
        sa.Column("condition_value", sa.Float(), nullable=False),
        sa.Column("risk_tier", risk_tier_enum, nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_rule_definitions_tenant_id", "rule_definitions", ["tenant_id"])
    op.create_index("ix_rule_definitions_is_active", "rule_definitions", ["is_active"])

    # -------------------------------------------------------------------------
    # Step 7: Table — auth_events
    # -------------------------------------------------------------------------
    op.create_table(
        "auth_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("monitored_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monitored_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", auth_event_type_enum, nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("geo_location", sa.String(255), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("device_fingerprint", sa.String(255), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_auth_events_tenant_account_time", "auth_events", ["tenant_id", "monitored_account_id", "timestamp"])
    op.create_index("ix_auth_events_tenant_type_time", "auth_events", ["tenant_id", "event_type", "timestamp"])

    # -------------------------------------------------------------------------
    # Step 8: Table — activity_events
    # -------------------------------------------------------------------------
    op.create_table(
        "activity_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("monitored_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monitored_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action_type", activity_event_type_enum, nullable=False),
        sa.Column("resource", sa.String(1024), nullable=True),
        sa.Column("resource_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_activity_events_tenant_account_time", "activity_events", ["tenant_id", "monitored_account_id", "timestamp"])
    op.create_index("ix_activity_events_tenant_action_time", "activity_events", ["tenant_id", "action_type", "timestamp"])

    # -------------------------------------------------------------------------
    # Step 9: Table — feature_vectors
    # -------------------------------------------------------------------------
    op.create_table(
        "feature_vectors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("monitored_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monitored_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_feature_vectors_tenant_id", "feature_vectors", ["tenant_id"])
    op.create_index("ix_feature_vectors_tenant_account_window", "feature_vectors", ["tenant_id", "monitored_account_id", "window_end"])

    # -------------------------------------------------------------------------
    # Step 10: Table — feature_values (FK: feature_vector_id → feature_vectors)
    # -------------------------------------------------------------------------
    op.create_table(
        "feature_values",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("feature_vector_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("feature_vectors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("feature_name", sa.String(255), nullable=False),
        sa.Column("feature_value", sa.Float(), nullable=False),
        sa.UniqueConstraint("feature_vector_id", "feature_name", name="uq_feature_values_vector_name"),
    )
    op.create_index("ix_feature_values_vector_id", "feature_values", ["feature_vector_id"])
    op.create_index("ix_feature_values_name", "feature_values", ["feature_name"])

    # -------------------------------------------------------------------------
    # Step 11: Table — threat_events
    # -------------------------------------------------------------------------
    op.create_table(
        "threat_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("monitored_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monitored_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("feature_vector_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("feature_vectors.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("ml_model_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ml_models.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("anomaly_score", sa.Float(), nullable=False),
        sa.Column("trust_score", sa.Float(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("risk_tier", risk_tier_enum, nullable=False),
        sa.Column("status", threat_event_status_enum, nullable=False, server_default="open"),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_threat_events_tenant_id", "threat_events", ["tenant_id"])
    op.create_index("ix_threat_events_tenant_tier_time", "threat_events", ["tenant_id", "risk_tier", "detected_at"])
    op.create_index("ix_threat_events_tenant_status_time", "threat_events", ["tenant_id", "status", "detected_at"])
    op.create_index("ix_threat_events_risk_tier", "threat_events", ["risk_tier"])
    op.create_index("ix_threat_events_status", "threat_events", ["status"])

    # -------------------------------------------------------------------------
    # Step 12: Table — shap_contributions (FK: threat_event_id → threat_events)
    # -------------------------------------------------------------------------
    op.create_table(
        "shap_contributions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("threat_event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("threat_events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("feature_name", sa.String(255), nullable=False),
        sa.Column("shap_value", sa.Float(), nullable=False),
        sa.Column("feature_value", sa.Float(), nullable=True),
        sa.UniqueConstraint("threat_event_id", "feature_name", name="uq_shap_contributions_event_feature"),
    )
    op.create_index("ix_shap_contributions_tenant_id", "shap_contributions", ["tenant_id"])
    op.create_index("ix_shap_contributions_threat_event_id", "shap_contributions", ["threat_event_id"])

    # -------------------------------------------------------------------------
    # Step 13: Table — rule_evaluations
    # -------------------------------------------------------------------------
    op.create_table(
        "rule_evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("threat_event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("threat_events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rule_definition_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rule_definitions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("result", rule_evaluation_result_enum, nullable=False),
        sa.Column("risk_tier_assigned", risk_tier_enum, nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_rule_evaluations_threat_event_id", "rule_evaluations", ["threat_event_id"])
    op.create_index("ix_rule_evaluations_tenant_rule", "rule_evaluations", ["tenant_id", "rule_definition_id"])

    # -------------------------------------------------------------------------
    # Step 14: Table — response_actions
    # -------------------------------------------------------------------------
    op.create_table(
        "response_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("threat_event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("threat_events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action_type", response_action_type_enum, nullable=False),
        sa.Column("status", response_action_status_enum, nullable=False, server_default="pending"),
        sa.Column("executed_by", sa.String(255), nullable=False, server_default="system"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_response_actions_threat_event_id", "response_actions", ["threat_event_id"])
    op.create_index("ix_response_actions_tenant_status", "response_actions", ["tenant_id", "status"])

    # -------------------------------------------------------------------------
    # Step 15: Table — honeypot_sessions
    # -------------------------------------------------------------------------
    op.create_table(
        "honeypot_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("threat_event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("threat_events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("monitored_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monitored_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attacker_ip", sa.String(45), nullable=True),
        sa.Column("session_token", sa.String(255), nullable=True),
        sa.Column("decoy_url", sa.String(1024), nullable=True),
        sa.Column("session_log", postgresql.JSONB(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("redirected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_honeypot_sessions_threat_event_id", "honeypot_sessions", ["threat_event_id"])
    op.create_index("ix_honeypot_sessions_tenant_active", "honeypot_sessions", ["tenant_id", "is_active"])

    # -------------------------------------------------------------------------
    # Step 16: Table — reports (FK: generated_by → users)
    # -------------------------------------------------------------------------
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("report_type", report_type_enum, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(1024), nullable=True),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", report_status_enum, nullable=False, server_default="generating"),
        sa.Column("generated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recipients", postgresql.ARRAY(sa.String(320)), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_reports_tenant_id", "reports", ["tenant_id"])
    op.create_index("ix_reports_tenant_type_created", "reports", ["tenant_id", "report_type", "created_at"])
    op.create_index("ix_reports_status", "reports", ["status"])

    # -------------------------------------------------------------------------
    # Step 17: Table — analyst_feedback (FK: threat_event_id, analyst_id)
    # -------------------------------------------------------------------------
    op.create_table(
        "analyst_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("threat_event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("threat_events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analyst_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("verdict", analyst_verdict_enum, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("threat_event_id", "analyst_id", name="uq_analyst_feedback_event_analyst"),
    )
    op.create_index("ix_analyst_feedback_tenant_id", "analyst_feedback", ["tenant_id"])
    op.create_index("ix_analyst_feedback_threat_event_id", "analyst_feedback", ["threat_event_id"])
    op.create_index("ix_analyst_feedback_tenant_verdict", "analyst_feedback", ["tenant_id", "verdict"])

    # -------------------------------------------------------------------------
    # Step 18: Table — retraining_runs (FK: ml_model_id, triggered_by_user_id)
    # -------------------------------------------------------------------------
    op.create_table(
        "retraining_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ml_model_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ml_models.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("output_model_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ml_models.id", ondelete="SET NULL"), nullable=True),
        sa.Column("triggered_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("triggered_by_system", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("samples_used", sa.Integer(), nullable=True),
        sa.Column("accuracy_before", sa.Float(), nullable=True),
        sa.Column("accuracy_after", sa.Float(), nullable=True),
        sa.Column("status", retraining_status_enum, nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_retraining_runs_tenant_id", "retraining_runs", ["tenant_id"])
    op.create_index("ix_retraining_runs_tenant_status", "retraining_runs", ["tenant_id", "status"])


def downgrade() -> None:
    """Drop all tables and PostgreSQL ENUM types (full rollback)."""

    # Drop tables in reverse FK dependency order
    op.drop_table("retraining_runs")
    op.drop_table("analyst_feedback")
    op.drop_table("reports")
    op.drop_table("honeypot_sessions")
    op.drop_table("response_actions")
    op.drop_table("rule_evaluations")
    op.drop_table("shap_contributions")
    op.drop_table("threat_events")
    op.drop_table("feature_values")
    op.drop_table("feature_vectors")
    op.drop_table("activity_events")
    op.drop_table("auth_events")
    op.drop_table("rule_definitions")
    op.drop_table("ml_models")
    op.drop_table("monitored_accounts")
    op.drop_table("users")
    op.drop_table("tenants")

    # Drop ENUM types
    conn = op.get_bind()
    for enum_type in reversed(ALL_ENUMS):
        enum_type.drop(conn, checkfirst=True)
