import datetime
stages = {
    1: datetime.timedelta(minutes=0),
    2: datetime.timedelta(minutes=30),
    3: datetime.timedelta(hours=8),
    4: datetime.timedelta(hours=24),
    5: datetime.timedelta(weeks=1),
    6: datetime.timedelta(weeks=4),
    7: datetime.timedelta(weeks=12),
}
min_stage = 1
max_stage = 7
min_translation_stage = 1