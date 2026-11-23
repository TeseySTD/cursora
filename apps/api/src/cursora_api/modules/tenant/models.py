"""ORM models of the tenant module (subclasses of cursora_api.core.db.Base)."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Identity, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from cursora_api.core.db import Base
from cursora_api.modules.risk.sensitivity import SENSITIVITY_MAX, SENSITIVITY_MIN

SITE_KEY_MAX_LENGTH = 64
# Hex SHA-256 digest of the secret key.
SECRET_KEY_HASH_LENGTH = 64
# Longest DNS name (RFC 1035).
DOMAIN_MAX_LENGTH = 253


class Site(Base):
    """A customer website protected by Cursora (BR-26).

    The public site key identifies the site to the widget. The secret key, with which the site's
    backend will verify tokens (ADR 0002), is shown once on creation and stored only as a hash.

    TODO(team): projects, members and roles (OQ-26, OQ-27); how allowed origins are enforced.
    """

    __tablename__ = "sites"
    __table_args__ = (
        CheckConstraint(
            f"sensitivity BETWEEN {SENSITIVITY_MIN} AND {SENSITIVITY_MAX}", name="sensitivity"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    site_key: Mapped[str] = mapped_column(String(SITE_KEY_MAX_LENGTH), unique=True)
    secret_key_hash: Mapped[str] = mapped_column(String(SECRET_KEY_HASH_LENGTH))
    domain: Mapped[str] = mapped_column(String(DOMAIN_MAX_LENGTH))
    allowed_origins: Mapped[list[str]] = mapped_column(ARRAY(Text))
    # TODO(team): default sensitivity and how it maps to thresholds (OQ-17). NULL = not set.
    sensitivity: Mapped[int | None] = mapped_column(SmallInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
