# Generated by Django 5.0.3 on 2024-05-14 00:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("games", "0013_alter_game_buildstats"),
    ]

    operations = [
        migrations.AlterField(
            model_name="gamefile",
            name="gameFileType",
            field=models.CharField(
                choices=[
                    ("gftypeStoryUpload", "Story upload (image, etc.)"),
                    ("gftypeDraftBuild", "Build draft file"),
                    ("gftypePreferredBuild", "Preferred built file"),
                    ("gftypePublished", "Published file"),
                    ("gftypeDebug", "Debug file"),
                ],
                default="gftypeStoryUpload",
                max_length=32,
            ),
        ),
    ]
