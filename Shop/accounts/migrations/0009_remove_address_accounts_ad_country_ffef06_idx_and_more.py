
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0008_address_created_at_address_updated_at"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="address",
            name="accounts_ad_country_ffef06_idx",
        ),
        migrations.RemoveField(
            model_name="address",
            name="country",
        ),
    ]
