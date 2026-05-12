from datetime import date, timedelta
from django.contrib.auth.models import User
from django.utils import timezone

from coop.models import DeliveryPoint, ProcurementOffer, Product, ProductCategory, SupplierSource
from members.models import UserProfile


class CoopFixtureMixin:
    def setUp(self):
        self.member = User.objects.create_user(username="member", password="pass12345")
        UserProfile.objects.create(user=self.member, is_coop_member=True)
        self.inviter = User.objects.create_user(username="inviter", password="pass12345")
        UserProfile.objects.create(user=self.inviter, is_coop_member=True)
        self.staff = User.objects.create_user(username="staff", password="pass12345", is_staff=True)
        self.category = ProductCategory.objects.create(name="Zeytinyağı")
        self.product = Product.objects.create(
            category=self.category,
            name="5lt zeytinyağı",
            unit=Product.Unit.PIECE,
            reference_url="https://example.com/product",
        )
        self.delivery_point = DeliveryPoint.objects.create(name="Merkez", address="Ankara")
        self.source = SupplierSource.objects.create(name="ABC Ziraat", website="https://example.com")
        self.offer = ProcurementOffer.objects.create(
            title="",
            product=self.product,
            source=self.source,
            unit_price=1000,
            target_quantity=10,
            deadline=timezone.now() + timedelta(days=3),
            fulfillment_date=date(2026, 5, 20),
            discount_rate=30,
        )
