import logging
from datetime import datetime

logging.basicConfig(filename=f"logs/app_logs_{datetime.now().strftime("%Y-%m-%d_%H_%M")}.log", filemode="w", format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)