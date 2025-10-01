
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_profile_address"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="address",
            name="unique_default_address_per_type",
        ),
        migrations.RemoveIndex(
            model_name="address",
            name="accounts_ad_user_id_b03917_idx",
        ),
        migrations.RemoveField(
            model_name="address",
            name="type",
        ),
        migrations.RemoveField(
            model_name="profile",
            name="marketing_opt_in",
        ),
        migrations.RemoveField(
            model_name="profile",
            name="newsletter_opt_in",
        ),
        migrations.AlterField(
            model_name="profile",
            name="phone",
            field=models.CharField(
                blank=True,
                help_text="مثال: +09123456789",
                max_length=20,
                null=True,
                unique=True,
                verbose_name="شماره موبایل",
            ),
        ),
        migrations.AddIndex(
            model_name="address",
            index=models.Index(
                fields=["user", "is_default"], name="accounts_ad_user_id_c8244c_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="address",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_default", True)),
                fields=("user",),
                name="unique_default_address_per_type",
            ),
        ),
    ]
