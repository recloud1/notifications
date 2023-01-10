from core.crud.base import BaseCrud
from models import Notification, NotificationRecurrence

notification_crud = BaseCrud(entity=Notification)

notification_recurrence_crud = BaseCrud(entity=NotificationRecurrence)
