import datetime
import os
env = os.getenv('BOT_ENV', 'staging')
stages = {
    1: datetime.timedelta(minutes=0),
    2: datetime.timedelta(minutes=30),
    3: datetime.timedelta(hours=8),
    4: datetime.timedelta(hours=24),
    5: datetime.timedelta(days=3),
    6: datetime.timedelta(weeks=1),
    7: datetime.timedelta(weeks=4),
    8: datetime.timedelta(weeks=12),
}
min_stage = 1
max_stage = 8
if env=='debug':
    min_translation_stage = 1
else:
    min_translation_stage = 3