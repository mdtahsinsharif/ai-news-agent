"""
Run the news pipeline now and then every 6 hours.

    python -m pipeline.scheduler

Leave it running in a terminal; Ctrl+C stops it. It checks the
clock every minute instead of sleeping 6 hours straight, because
a long sleep pauses while the Mac is asleep. This way a run that
came due during sleep starts as soon as the Mac wakes.
"""

import time
import traceback
from datetime import datetime, timedelta

from pipeline.process import process_news


INTERVAL = timedelta(hours=6)

CHECK_EVERY_SECONDS = 60


def main():

    next_run = datetime.now()

    while True:

        if datetime.now() >= next_run:

            print(
                f"\n=== Pipeline run started "
                f"{datetime.now():%Y-%m-%d %H:%M:%S} ===",
                flush=True,
            )

            # A failed run shouldn't stop future runs.
            try:
                process_news()
            except Exception:
                traceback.print_exc()

            next_run = datetime.now() + INTERVAL

            print(
                f"=== Next run at {next_run:%Y-%m-%d %H:%M} ===",
                flush=True,
            )

        time.sleep(CHECK_EVERY_SECONDS)


if __name__ == "__main__":
    main()
