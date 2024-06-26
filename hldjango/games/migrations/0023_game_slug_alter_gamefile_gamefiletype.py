# Generated by Django 5.0.3 on 2024-05-29 04:16

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("games", "0022_game_lastbuildlog"),
    ]

    operations = [
        migrations.AddField(
            model_name="game",
            name="slug",
            field=models.SlugField(
                blank=True,
                default=uuid.uuid4,
                help_text="Unique slug id of the game",
                max_length=128,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="gamefile",
            name="gameFileType",
            field=models.CharField(
                choices=[
                    ("uploadsStory", "Story upload (image, etc.)"),
                    ("buildDraft", "Build draft file"),
                    ("buildPreferred", "Preferred built file"),
                    ("published", "Published file"),
                    ("versionedGameText", "Versioned game text file"),
                    ("buildDebug", "Debug file"),
                ],
                default="uploadsStory",
                max_length=32,
            ),
        ),
    ]
