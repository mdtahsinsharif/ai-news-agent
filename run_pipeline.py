"""
Run the news pipeline once and exit.

Scheduled hourly by launchd; see README for the commands.
"""

from datetime import datetime

from pipeline.process import process_news


if __name__ == "__main__":

    print(
        f"\n=== Pipeline run started "
        f"{datetime.now():%Y-%m-%d %H:%M:%S} ==="
    )

    process_news()

    print(
        f"=== Pipeline run finished "
        f"{datetime.now():%Y-%m-%d %H:%M:%S} ==="
    )
