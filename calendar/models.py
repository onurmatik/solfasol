from django.core.exceptions import ValidationError
from django.db import models

from common.models import TimeStampedModel


class CalendarEvent(TimeStampedModel):
    class EventType(models.TextChoices):
        EDUCATION = "education", "Eğitim"
        COMMUNITY = "community", "Topluluk"
        EXTERNAL = "external", "Dış etkinlik"
        OTHER = "other", "Diğer"

    class Status(models.TextChoices):
        DRAFT = "draft", "Taslak"
        PUBLISHED = "published", "Yayında"
        CANCELED = "canceled", "İptal"

    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=24, choices=EventType.choices, default=EventType.COMMUNITY)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    is_all_day = models.BooleanField(default=False)
    location_name = models.CharField(max_length=160, blank=True)
    location_address = models.TextField(blank=True)
    link_url = models.URLField(blank=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.DRAFT)

    class Meta:
        ordering = ["starts_at", "title"]
        verbose_name = "Takvim etkinliği"
        verbose_name_plural = "Takvim etkinlikleri"

    def __str__(self):
        return self.title

    def clean(self):
        if self.ends_at and self.ends_at <= self.starts_at:
            raise ValidationError({"ends_at": "Bitiş zamanı başlangıçtan sonra olmalı."})

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED
