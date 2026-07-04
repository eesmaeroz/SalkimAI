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
from apps.api.models.sensor_reading import SensorReading
from apps.api.models.prediction import HarvestPrediction

__all__ = [
    "Base",
    "TimestampMixin",
    "User",
    "Greenhouse",
    "Plant",
    "Image",
    "Analysis",
    "Harvest",
    "SensorReading",
    "HarvestPrediction",
]
