import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("coop", "0002_alter_memberofferintent_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="procurementoffer",
            name="discount_rate",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="Opsiyonel indirim oranı. Varsa UI'da 'You save 30%' gibi gösterilir.",
                null=True,
                validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)],
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="reference_url",
            field=models.URLField(blank=True, help_text="Ürün hakkında internette referans verilebilecek sayfa URL'si."),
        ),
        migrations.AlterField(
            model_name="procurementoffer",
            name="deadline",
            field=models.DateTimeField(help_text="Üyelerin bu teklif için talep girip değiştirebileceği son tarih ve saat."),
        ),
        migrations.AlterField(
            model_name="procurementoffer",
            name="fulfillment_date",
            field=models.DateField(help_text="Teklif gerçekleşirse teslimatın veya fulfillment'ın yapılacağı tarih."),
        ),
        migrations.AlterField(
            model_name="procurementoffer",
            name="title",
            field=models.CharField(
                blank=True,
                help_text="Opsiyonel başlık. Boş bırakılırsa tedarikçi ve ürün adıyla gösterilir.",
                max_length=160,
            ),
        ),
        migrations.AlterField(
            model_name="suppliersource",
            name="website",
            field=models.URLField(blank=True, help_text="Tedarikçinin web sitesi veya sosyal medya profil URL'si."),
        ),
    ]
