from dataclasses import dataclass
from typing import Optional


# ============================================================
# ADMIN TYPES
# ============================================================

ADMIN_OWNER = "owner"
ADMIN_SUPERADMIN = "superadmin"
ADMIN_ADMIN = "admin"
ADMIN_MODERATOR = "moderator"
ADMIN_PRIMARCH = "primarch"


ADMIN_TYPES = {
    ADMIN_OWNER,
    ADMIN_SUPERADMIN,
    ADMIN_ADMIN,
    ADMIN_MODERATOR,
    ADMIN_PRIMARCH,
}


# ============================================================
# PERMISSIONS
# ============================================================

VIEW_PROFILE = "view_profile"
EDIT_NAME = "edit_name"
EDIT_ROLE = "edit_role"
EDIT_RANK = "edit_rank"
EDIT_LEGION = "edit_legion"
EDIT_STATUS = "edit_status"
EDIT_REPUTATION = "edit_reputation"

MANAGE_RANKS = "manage_ranks"
MANAGE_LEGIONS = "manage_legions"
MANAGE_ROLES = "manage_roles"
MANAGE_STATUSES = "manage_statuses"

MANAGE_ADMINS = "manage_admins"
MANAGE_PERMISSIONS = "manage_permissions"

MODERATE_USERS = "moderate_users"
VIEW_AUDIT_LOG = "view_audit_log"


PERMISSIONS = {
    VIEW_PROFILE,
    EDIT_NAME,
    EDIT_ROLE,
    EDIT_RANK,
    EDIT_LEGION,
    EDIT_STATUS,
    EDIT_REPUTATION,
    MANAGE_RANKS,
    MANAGE_LEGIONS,
    MANAGE_ROLES,
    MANAGE_STATUSES,
    MANAGE_ADMINS,
    MANAGE_PERMISSIONS,
    MODERATE_USERS,
    VIEW_AUDIT_LOG,
}


# ============================================================
# MEMBER PROFILE
# ============================================================

@dataclass
class MemberProfile:
    user_id: int
    chat_id: int

    display_name: Optional[str] = None

    role_id: Optional[int] = None
    rank_id: Optional[int] = None
    legion_id: Optional[int] = None
    status_id: Optional[int] = None

    reputation: int = 0


# ============================================================
# LEGION
# ============================================================

@dataclass
class Legion:
    id: int
    chat_id: int
    name: str

    primarch_id: Optional[int] = None
    active: bool = True


# ============================================================
# RANK
# ============================================================

@dataclass
class Rank:
    id: int
    legion_id: int

    name: str
    description: Optional[str] = None

    points_required: int = 0
    position: int = 0

    active: bool = True


# ============================================================
# ROLE
# ============================================================

@dataclass
class Role:
    id: int
    chat_id: int

    name: str
    description: Optional[str] = None

    active: bool = True


# ============================================================
# STATUS
# ============================================================

@dataclass
class Status:
    id: int
    chat_id: int

    name: str
    description: Optional[str] = None

    active: bool = True


# ============================================================
# ADMINISTRATOR
# ============================================================

@dataclass
class Administrator:
    id: int
    chat_id: int
    user_id: int

    admin_type: str

    active: bool = True
    assigned_by: Optional[int] = None


# ============================================================
# PERMISSION
# ============================================================

@dataclass
class Permission:
    id: int
    code: str
    description: Optional[str] = None


# ============================================================
# ADMIN PERMISSION
# ============================================================

@dataclass
class AdminPermission:
    administrator_id: int
    permission_id: int


# ============================================================
# AUDIT LOG
# ============================================================

@dataclass
class AuditLog:
    id: int
    chat_id: int

    actor_id: int
    action: str

    target_id: Optional[int] = None

    old_value: Optional[str] = None
    new_value: Optional[str] = None

    created_at: Optional[str] = None