"""
Salkım AI — ORM Modelleri

Tüm modelleri tek noktadan import etmek için.
Alembic env.py ve uygulama başlangıcında bu modül import edilir.
"""

from apps.api.models.base import Base, TimestampMixin
from apps.api.models.user import User
from apps.api.models.greenhouse import Greenhouse
from apps.api.models.plant import Plant
from apps.api.models.image import Image
from apps.api.models.analysis import Analysis
from apps.api.models.harvest import Harvest

__all__ = [
    "Base",
    "TimestampMixin",
    "User",
    "Greenhouse",
    "Plant",
    "Image",
    "Analysis",
    "Harvest",
]
