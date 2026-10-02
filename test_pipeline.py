
import time

from pipeline.process import process_news

while True:
    try:
        print("Starting news pipeline...")

        process_news()

        print("Pipeline completed successfully.")

    except Exception as e:
        print(f"Pipeline failed: {e}")

    print("Sleeping for 6 hours...")

    time.sleep(6 * 60 * 60)

