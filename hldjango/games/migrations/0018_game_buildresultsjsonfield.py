# Generated by Django 5.0.3 on 2024-05-22 20:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("games", "0017_rename_buildstats_game_leadstats_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="game",
            name="buildResultsJsonField",
            field=models.JSONField(
                blank=True, default="", help_text="All build results as json"
            ),
        ),
    ]
