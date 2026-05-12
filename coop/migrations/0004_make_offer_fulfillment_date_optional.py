from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("coop", "0003_offer_optional_title_product_reference_discount_and_help"),
    ]

    operations = [
        migrations.AlterField(
            model_name="procurementoffer",
            name="fulfillment_date",
            field=models.DateField(
                blank=True,
                help_text="Teklif gerçekleşirse teslimatın veya fulfillment'ın yapılacağı tarih. Bilinmiyorsa boş bırakılabilir.",
                null=True,
            ),
        ),
    ]
