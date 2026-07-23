"""
ORM model registry — imports all 17 models to ensure they are registered
with Base.metadata before Alembic reads it for migration generation.

IMPORTANT: This module MUST be imported by alembic/env.py and by any
other module that creates tables or runs migrations.

Import order respects FK dependencies (parents before children).
"""

# Root entity (no FKs)
from app.models.tenant import Tenant

# Level 1 — depend only on Tenant
from app.models.user import User
from app.models.monitored_account import MonitoredAccount
from app.models.ml_model import MLModel
from app.models.rule_definition import RuleDefinition

# Level 2 — depend on MonitoredAccount
from app.models.auth_event import AuthEvent
from app.models.activity_event import ActivityEvent
from app.models.feature_vector import FeatureVector

# Level 3 — depend on FeatureVector
from app.models.feature_value import FeatureValue

# Level 4 — depend on MonitoredAccount + FeatureVector + MLModel
from app.models.threat_event import ThreatEvent

# Level 5 — depend on ThreatEvent
from app.models.shap_contribution import SHAPContribution
from app.models.rule_evaluation import RuleEvaluation
from app.models.response_action import ResponseAction
from app.models.honeypot_session import HoneypotSession

# Level 6 — depend on ThreatEvent + User
from app.models.analyst_feedback import AnalystFeedback

# Level 6 — depend on Tenant + User
from app.models.report import Report

# Level 6 — depend on MLModel + User
from app.models.retraining_run import RetrainingRun

# Enum definitions (not a model, but imported here for convenience)
from app.models.enums import (
    UserRole,
    MonitoredAccountStatus,
    AuthEventType,
    ActivityEventType,
    MLModelType,
    RiskTier,
    ThreatEventStatus,
    RuleConditionField,
    RuleConditionOperator,
    RuleEvaluationResult,
    ResponseActionType,
    ResponseActionStatus,
    ReportType,
    ReportStatus,
    AnalystVerdict,
    RetrainingStatus,
)

__all__ = [
    # Models (17 tables)
    "Tenant",
    "User",
    "MonitoredAccount",
    "MLModel",
    "RuleDefinition",
    "AuthEvent",
    "ActivityEvent",
    "FeatureVector",
    "FeatureValue",
    "ThreatEvent",
    "SHAPContribution",
    "RuleEvaluation",
    "ResponseAction",
    "HoneypotSession",
    "AnalystFeedback",
    "Report",
    "RetrainingRun",
    # Enums
    "UserRole",
    "MonitoredAccountStatus",
    "AuthEventType",
    "ActivityEventType",
    "MLModelType",
    "RiskTier",
    "ThreatEventStatus",
    "RuleConditionField",
    "RuleConditionOperator",
    "RuleEvaluationResult",
    "ResponseActionType",
    "ResponseActionStatus",
    "ReportType",
    "ReportStatus",
    "AnalystVerdict",
    "RetrainingStatus",
]
