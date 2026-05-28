from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .seed import seed_demo_data, seed_demo_users


@receiver(post_migrate)
def bootstrap_demo_data(sender, app_config, **kwargs):
    if app_config and app_config.name == "ingestion":
        seed_demo_users()
        seed_demo_data()
