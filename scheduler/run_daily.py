"""
로컬 PC 스케줄러 — 매일 07:00 KST에 main.py 실행
실행: python scheduler/run_daily.py
(PC가 켜져 있어야 동작합니다. 클라우드는 GitHub Actions 권장)
"""
import logging
import sys
import os

from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv
load_dotenv(override=True)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("scheduler")


def job():
    logger.info("스케줄 실행 시작")
    from main import run
    run()


if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone=config.KST)
    scheduler.add_job(
        job,
        trigger="cron",
        hour=config.SCHEDULE_HOUR_KST,
        minute=config.SCHEDULE_MINUTE_KST,
    )
    logger.info(
        "스케줄러 시작 — 매일 %02d:%02d KST에 실행됩니다. 종료하려면 Ctrl+C",
        config.SCHEDULE_HOUR_KST,
        config.SCHEDULE_MINUTE_KST,
    )
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("스케줄러 종료")
