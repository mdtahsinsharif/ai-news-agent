"""
Run the news pipeline once and exit.

For the 6-hour schedule use: python -m pipeline.scheduler
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
