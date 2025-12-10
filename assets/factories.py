import factory
from factory.django import DjangoModelFactory
from assets.models import Asset
from accounts.models import User
import random
from datetime import date, timedelta

class AssetFactory(DjangoModelFactory):
    class Meta:
        model = Asset

    asset_category = factory.Iterator(['laptop', 'desktop', 'printer', 'projector'])
    model = factory.Sequence(lambda n: f"Model-{n}")
    serial_number = factory.Sequence(lambda n: f"SN{n:05}")
    barcode = factory.Sequence(lambda n: f"BC{n:05}")
    specification = factory.Faker('sentence', nb_words=5)
    description = factory.Faker('sentence', nb_words=8)
    status = factory.Iterator(['available', 'borrowed', 'maintenance', 'retired', 'returned'])
    asset_condition = factory.Iterator(['good', 'fair', 'poor'])

    # Only admin/staff can be the creator
    @factory.lazy_attribute
    def created_by(self):
        return User.objects.filter(role__in=['admin', 'staff']).order_by('?').first()
