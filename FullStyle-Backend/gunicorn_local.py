"""Run a bounded maintenance job in existing local workers; no extra service."""

import os
import threading
import time


def post_worker_init(worker):
    if os.getenv("LOCAL_RUNTIME") != "true":
        return
    from maintenance_local import maintain

    def run():
        while True:
            with worker.wsgi.app_context():
                try:
                    maintain()
                except Exception as exc:
                    worker.log.warning("Local maintenance failed: %s", type(exc).__name__)
            time.sleep(60)

    threading.Thread(target=run, name="local-maintenance", daemon=True).start()
