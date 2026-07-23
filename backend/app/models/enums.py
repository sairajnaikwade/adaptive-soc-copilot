"""
Centralized Python Enum definitions for Adaptive SOC CoPilot.

Using str-based Enums (class MyEnum(str, enum.Enum)) provides two benefits:
  1. Values serialize directly to strings in JSON responses (Pydantic compat).
  2. Comparison with plain strings still works: UserRole.ADMIN == "admin" → True

All enums here mirror the PostgreSQL ENUM types defined in the Alembic migration.
Any new enum values MUST have a corresponding Alembic migration to add them to
the PostgreSQL type before being used in application code.
"""

import enum


# ===========================================================================
# User & Tenant
# ===========================================================================

class UserRole(str, enum.Enum):
    """Roles assigned to SOC platform users."""
    ADMIN = "admin"       # Full access: manage users, tenants, trigger retraining
    ANALYST = "analyst"   # Operational access: view threats, submit feedback


# ===========================================================================
# Monitored Accounts
# ===========================================================================

class MonitoredAccountStatus(str, enum.Enum):
    """Lifecycle states of a monitored account."""
    ACTIVE = "active"           # Normal monitoring
    SUSPENDED = "suspended"     # Temporarily restricted (e.g., MFA triggered)
    BLOCKED = "blocked"         # Account fully blocked by response engine
    HONEYPOT = "honeypot"       # Redirected to honeypot environment
    INACTIVE = "inactive"       # No longer being monitored


# ===========================================================================
# Authentication Events
# ===========================================================================

class AuthEventType(str, enum.Enum):
    """Types of authentication events ingested from monitored systems."""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_RESET = "password_reset"
    MFA_CHALLENGE = "mfa_challenge"
    MFA_SUCCESS = "mfa_success"
    MFA_FAILURE = "mfa_failure"
    ACCOUNT_LOCKED = "account_locked"


# ===========================================================================
# Activity Events
# ===========================================================================

class ActivityEventType(str, enum.Enum):
    """Types of user-activity events ingested from monitored systems."""
    FILE_DOWNLOAD = "file_download"
    FILE_UPLOAD = "file_upload"
    DATA_EXPORT = "data_export"
    PRIVILEGE_CHANGE = "privilege_change"
    API_CALL = "api_call"
    CONFIG_CHANGE = "config_change"
    DATA_ACCESS = "data_access"
    REPORT_DOWNLOAD = "report_download"


# ===========================================================================
# ML Models
# ===========================================================================

class MLModelType(str, enum.Enum):
    """Supported unsupervised anomaly detection model types."""
    ISOLATION_FOREST = "isolation_forest"    # Primary model
    ONE_CLASS_SVM = "one_class_svm"          # Comparison model


# ===========================================================================
# Threat Events
# ===========================================================================

class RiskTier(str, enum.Enum):
    """Risk classification tiers produced by the Rule Engine."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ThreatEventStatus(str, enum.Enum):
    """Lifecycle status of a detected threat event."""
    OPEN = "open"                       # Awaiting analyst review
    ACKNOWLEDGED = "acknowledged"       # Analyst has seen it
    RESOLVED = "resolved"               # Threat handled and closed
    FALSE_POSITIVE = "false_positive"   # Confirmed not a real threat


# ===========================================================================
# Rule Engine
# ===========================================================================

class RuleConditionField(str, enum.Enum):
    """Fields that a rule can evaluate."""
    TRUST_SCORE = "trust_score"
    CONFIDENCE_SCORE = "confidence_score"
    ANOMALY_SCORE = "anomaly_score"


class RuleConditionOperator(str, enum.Enum):
    """Comparison operators used in rule conditions."""
    LT = "lt"    # Less than
    GT = "gt"    # Greater than
    LTE = "lte"  # Less than or equal
    GTE = "gte"  # Greater than or equal
    EQ = "eq"    # Equal


class RuleEvaluationResult(str, enum.Enum):
    """Outcome of evaluating a rule against a threat event."""
    MATCHED = "matched"
    NOT_MATCHED = "not_matched"


# ===========================================================================
# Adaptive Response Engine
# ===========================================================================

class ResponseActionType(str, enum.Enum):
    """Actions the Adaptive Response Engine can execute."""
    MONITOR = "monitor"                         # Continue monitoring only
    NOTIFY_ANALYST = "notify_analyst"           # Send alert to SOC analyst
    TRIGGER_MFA = "trigger_mfa"                 # Force MFA re-authentication
    RESTRICT_PRIVILEGES = "restrict_privileges" # Reduce account permissions
    BLOCK_ACCOUNT = "block_account"             # Fully block the account
    TERMINATE_SESSION = "terminate_session"     # Kill active sessions
    REDIRECT_HONEYPOT = "redirect_honeypot"     # Route to honeypot environment


class ResponseActionStatus(str, enum.Enum):
    """Execution status of a response action."""
    PENDING = "pending"
    EXECUTED = "executed"
    FAILED = "failed"
    REVERTED = "reverted"


# ===========================================================================
# Reports
# ===========================================================================

class ReportType(str, enum.Enum):
    """Report generation schedule types."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ON_DEMAND = "on_demand"


class ReportStatus(str, enum.Enum):
    """Report generation and delivery lifecycle."""
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    SENT = "sent"


# ===========================================================================
# Analyst Feedback
# ===========================================================================

class AnalystVerdict(str, enum.Enum):
    """Analyst classification of a detected threat event."""
    TRUE_POSITIVE = "true_positive"   # Legitimate threat — model was correct
    FALSE_POSITIVE = "false_positive" # Not a threat — model was wrong
    NEEDS_REVIEW = "needs_review"     # Requires further investigation


# ===========================================================================
# Continuous Improvement (Retraining)
# ===========================================================================

class RetrainingStatus(str, enum.Enum):
    """Lifecycle of a model retraining run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
