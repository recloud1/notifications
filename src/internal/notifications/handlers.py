import abc
import logging
from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from core.config import envs
from internal.templates.environment import TemplateEnvironment
from models import Backend, Notification, NotificationMessage
from tools.email_sender import EmailSender

Title, Content = str, str


class NotificationHandlerAbstract(abc.ABC):
    """
    Абстрактный класс для реализации отправки уведомлений в разных backend'ах.
    """

    def __init__(
        self,
        notification_id: str,
        send_to: str,
    ) -> None:
        self.notification_id = notification_id
        self.send_to = send_to
        self.notification: Notification | None = None
        self.logger = logging.getLogger(self.__class__.__name__)

    def __call__(self, session: Session):
        notification = self.get_notification(session, self.notification_id)
        self.notification = notification

        title, content = self.render()
        self.create_message(session, notification, title=title, content=content)
        self.send_notification(content=content, title=title)

    @staticmethod
    def get_notification(session: Session, _id: str):
        notification = session.get(
            Notification, _id, options=[joinedload(Notification.template)]
        )
        if notification is None:
            raise ValueError("Notification not found")

        return notification

    @property
    @abc.abstractmethod
    def backend(self) -> Backend:
        """
        Backend, для которого реализуется отправка уведомлений
        """
        pass

    def create_message(
        self, session: Session, notification: Notification, content: str, title: str
    ) -> NotificationMessage:
        now = datetime.utcnow()
        message = NotificationMessage(
            user_id=notification.user_id,
            notification_id=notification.id,
            send_to=self.send_to,
            title=title,
            content=content,
            backend=self.backend,
            created_at=now,
            sent_at=now,
        )
        session.add(message)
        return message

    def render(self, with_base_template: bool = False) -> tuple[Title, Content]:
        notification = self.notification
        if notification is None:
            raise Exception("Notification should be pre-loaded on __call__")

        env = TemplateEnvironment()
        content_template = env.get_template(
            notification.template.slug, wrap_by_base_template=with_base_template
        )

        title_template = env.from_string(notification.template.title)

        rendered_content = content_template.render(**notification.template_data)
        rendered_title = title_template.render(**notification.template_data)
        return rendered_title, rendered_content

    @abc.abstractmethod
    def send_notification(self, content: str, title: str):
        """
        Реализация отправки уведомления
        """


class EmailNotificationHandler(NotificationHandlerAbstract):
    email_sender: EmailSender | None = None

    def __init__(self, notification_id: str, send_to: str):
        super().__init__(notification_id, send_to)
        if self.email_sender is None:
            self.email_sender = EmailSender(
                smtp_host=envs.smtp.server,
                smtp_port=envs.smtp.port,
                from_email=envs.smtp.from_email,
                login=envs.smtp.login,
                password=envs.smtp.password,
                use_ssl=True,
            )

    def render(self, with_base_template: bool = False) -> tuple[Title, Content]:
        return super().render(with_base_template=True)

    @property
    def backend(self) -> Backend:
        return Backend.email

    def send_notification(self, content: str, title: str):
        notification = self.notification
        if notification is None:
            raise ValueError("Notification should be pre-loaded on __call__")

        self.email_sender.send_message_fast(
            self.send_to,
            content,
            title,
            content_type="html",
        )
