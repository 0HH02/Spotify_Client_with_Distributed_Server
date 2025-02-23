import os
import signal
import time
import random
import sys
from django.apps import AppConfig


class SpotifyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "spotify"

    def ready(self):
        print("Initializing Spotify")
        lock_file_path = "./tmp/startup_lock"
        try:
            from .distributed_layer.distributed_interface import DistributedInterface

            if not os.path.exists(lock_file_path):
                with open(lock_file_path, "w+", encoding="utf-8") as f:
                    f.write("lock")
                _ = DistributedInterface()

        except Exception as e:
            print(e)
            pass

        signal.signal(signal.SIGTERM, self.on_shutdown)
        signal.signal(signal.SIGINT, self.on_shutdown)
        return super().ready()

    def on_shutdown(self, _, __):
        lock_file_path = "./tmp/startup_lock"
        time.sleep(random.random())
        if os.path.exists(lock_file_path):
            print("Removing lock file")
            os.remove(lock_file_path)
        sys.exit(0)
