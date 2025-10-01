
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_alter_city_unique_together_remove_city_province_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="City",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=120, verbose_name="شهر")),
            ],
            options={
                "verbose_name": "شهر",
                "verbose_name_plural": "شهرها",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Province",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=100, unique=True, verbose_name="استان"),
                ),
            ],
            options={
                "verbose_name": "استان",
                "verbose_name_plural": "استان\u200cها",
                "ordering": ["name"],
            },
        ),
        migrations.RemoveConstraint(
            model_name="address",
            name="unique_default_address_per_type",
        ),
        migrations.RemoveField(
            model_name="address",
            name="state",
        ),
        migrations.AlterField(
            model_name="address",
            name="line1",
            field=models.CharField(max_length=255, verbose_name="آدرس ۱"),
        ),
        migrations.AlterField(
            model_name="address",
            name="line2",
            field=models.CharField(blank=True, max_length=255, verbose_name="آدرس ۲"),
        ),
        migrations.AlterField(
            model_name="address",
            name="city",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="addresses",
                to="accounts.city",
                verbose_name="شهر",
            ),
        ),
        migrations.AddField(
            model_name="city",
            name="province",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="cities",
                to="accounts.province",
            ),
        ),
        migrations.AddField(
            model_name="address",
            name="province",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="addresses",
                to="accounts.province",
                verbose_name="استان",
            ),
        ),
        migrations.AddIndex(
            model_name="address",
            index=models.Index(
                fields=["province", "city"], name="accounts_ad_provinc_09fa27_idx"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="city",
            unique_together={("province", "name")},
        ),
    ]
