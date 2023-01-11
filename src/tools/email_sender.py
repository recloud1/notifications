import logging
import smtplib
import socket
import ssl
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Literal

logger = logging.getLogger("email-sender")


def smtp_connect(
    host: str, port: int, login: str | None, password: str | None, use_ssl=False
) -> smtplib.SMTP | smtplib.SMTP_SSL:
    """
    Контекстный менеджер для подключения к smtp серверу
    :param host: адрес по которому расположен smtp сервер
    :param port: порт для подключения к smtp серверу
    :param login: имя пользователя smtp сервера
    :param password: пароль от указанного почтового адреса
    :return: контекстный менеджер для отправки сообщений
    """
    if use_ssl:
        klass = smtplib.SMTP_SSL
        context = ssl.create_default_context()
        kwargs = {"context": context}
    else:
        klass = smtplib.SMTP
        kwargs = {}

    try:
        server = klass(host, port, **kwargs, timeout=30)
    except socket.gaierror:
        raise ConnectionError("Не удалось подключиться к почтовому серверу")
    if login and password:
        server.login(login, password)
    else:
        logger.debug("No password passed. Skipping authorization on smtp server")
    return server


MessageContent = str


class EmailSender:
    DEFAULT_SMTP_PORT = 465  # for SSL connections

    ContentType = Literal["html", "plain"]

    def __init__(
        self,
        smtp_host: str,
        from_email: str,
        login: str | None = None,
        password: str | None = None,
        smtp_port: int | None = DEFAULT_SMTP_PORT,
        use_ssl: bool = False,
    ):

        self.smtp_port = smtp_port
        self.smtp_host = smtp_host
        self.login = login
        self.password = password
        self.from_email = from_email
        self.use_ssl = use_ssl

        self.server: smtplib.SMTP = smtp_connect(
            self.smtp_host, self.smtp_port, self.login, self.password, self.use_ssl
        )

    def reconnect(self):
        try:
            self.close()
        except smtplib.SMTPServerDisconnected:
            pass

        self.server = smtp_connect(
            self.smtp_host, self.smtp_port, self.login, self.password, self.use_ssl
        )

    def close(self):
        """
        Закрывает SMTP соединение с сервером
        """
        try:
            self.server.quit()
        except smtplib.SMTPServerDisconnected:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()

    def send_message_safe(
        self,
        to_email: str | list[str],
        content: MessageContent,
        title: str,
        content_type: ContentType = "plain",
        attachments: list[str | tuple[str, str]] | None = None,
        event_data: str = None,
    ):
        """
        Отправляет сообщение 1 или нескольким пользователям.

        Сообщение может быть представлено в виде текста, либо html сообщения. Для корректной отправки
        необходимо выбрать соответствующий тип сообщения в поле `content_type`. Помимо этого, при
        наличии переменных шаблона, сообщение будет собрано через шаблонизатор *jinja2*.

        :param to_email: 1 или несколько адресов электронной почты, на которые будут отправлены письма.
        :param content: содержимое письма.
        :param title: заголовок для письма.
        :param content_type: вид содержимого (обычный текст или html).
        :param attachments: список файлов, которые будут прикреплены к письму.
        Допускается указание кортежа из (<названия вложения>, <пути до файла>).
        :param event_data: содержимое ICS файла, прикрепляемого к письму.

        :raises FileNotFoundError при отсутствии одного из вложений.
        :raises ConnectionError при проблемах с отправкой.
        """

        try:
            self.server.login(self.login, self.password)
            self.send_message_fast(
                to_email, content, title, content_type, attachments, event_data
            )
        finally:
            self.server.close()

    def send_message_fast(
        self,
        to_email: str | list[str],
        content: MessageContent,
        title: str,
        content_type: ContentType = "plain",
        event_data: str = None,
    ):
        """
        Отправляет сообщение 1 или нескольким пользователям.

        В отличии от безопасного варианта, не закрывает соединение,
        а требует вручную выполнять .close() метод.

        Сообщение может быть представлено в виде текста, либо html сообщения. Для корректной отправки
        необходимо выбрать соответствующий тип сообщения в поле `content_type`. Помимо этого, при
        наличии переменных шаблона, сообщение будет собрано через шаблонизатор *jinja2*.

        :param to_email: 1 или несколько адресов электронной почты, на которые будут отправлены письма.
        :param content: содержимое письма.
        :param title: заголовок для письма.
        :param content_type: вид содержимого (обычный текст или html).
        :param attachments: список файлов, которые будут прикреплены к письму.
        Допускается указание кортежа из (<названия вложения>, <пути до файла>).
        :param event_data: содержимое ICS файла, прикрепляемого к письму.

        :raises FileNotFoundError: при отсутствии одного из вложений.
        :raises ConnectionError: при проблемах с отправкой.
        """

        if type(to_email) == str:
            to_email = [to_email]

        try:
            for email in to_email:
                self._send_message(
                    self.server,
                    email,
                    content,
                    title,
                    content_type,
                    event_data=event_data,
                )
        except Exception as e:
            logger.error("Unable to connect with smtp server", exc_info=True)
            raise ConnectionError(
                "Невозможно отправить письмо."
                " Отсутствует подключение к серверу почты"
            ) from e

    def _send_message(
        self,
        connection: smtplib.SMTP_SSL | smtplib.SMTP,
        to_email: str,
        content: MessageContent,
        title: str,
        content_type: ContentType = "plain",
        event_data: str = None,
        max_retries: int = 5,
        retry: int = 1,
        error=None,
    ):
        """
        :raises ConnectionError при проблемах с отправкой
        """
        if retry == max_retries:
            err = ConnectionError(
                "Не удалось отправить письмо. Достигнуто максимально кол-во попыток"
            )
            raise (error or err)

        message = MIMEMultipart()
        message["From"] = self.from_email
        message["To"] = to_email
        message["subject"] = title

        mimed_content = MIMEText(content, content_type)
        message.attach(mimed_content)

        try:
            connection.send_message(message, self.from_email, to_email)
        except smtplib.SMTPRecipientsRefused as e:
            logger.debug("You probably was banned by recipient", exc_info=True)
            raise ConnectionError("Пользователь отклонил письмо") from e
        except smtplib.SMTPServerDisconnected as e:
            self.reconnect()

            self._send_message(
                connection,
                to_email,
                content,
                title,
                content_type,
                event_data,
                max_retries=max_retries,
                retry=retry + 1,
                error=e,
            )
        except smtplib.SMTPSenderRefused as e:
            self.reconnect()

            self._send_message(
                connection,
                to_email,
                content,
                title,
                content_type,
                event_data,
                max_retries=max_retries,
                retry=retry + 1,
                error=e,
            )
            time.sleep(retry)
        except Exception as e:
            logger.error("Some troubles via sending", exc_info=True)
            raise ConnectionError("Не удалось отправить письмо") from e
