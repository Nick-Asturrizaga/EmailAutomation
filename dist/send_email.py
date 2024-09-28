import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from logging import getLogger
from smtplib import SMTP_SSL as SMTP

from jinja2 import Template
from strenum import StrEnum

from config import Config


class ContentType(StrEnum):
    HTML = 'html'
    TEXT = 'text'


def get_email_content(content_type, placeholder_map):
    with open(f"./templates/email.{content_type}.jinja", 'r') as f:
        template_str = f.read()

    return Template(template_str).render(placeholder_map)


config: Config = Config()

context = ssl.create_default_context()

sender = config.emails.sender

logger = getLogger(__name__)


def send_email(receiver, ticket):
    if receiver is None:
        logger.critical("Receiver email not filled.")
        exit(65)

    placeholder_values = {
        'subject': config.emails.subject,
        'summary': ticket.summary,
        'status': ticket.status,
        'who_is_impacted': ticket.who_is_impacted,
        'when': ticket.when
    }

    text = get_email_content(ContentType.TEXT, placeholder_map=placeholder_values)
    html = get_email_content(ContentType.HTML, placeholder_map=placeholder_values)

    part_text = MIMEText(text, "plain")
    part_html = MIMEText(html, "html")

    message = MIMEMultipart("alternative")
    message["Subject"] = config.emails.subject
    message["From"] = sender
    message["To"] = receiver

    message.attach(part_text)
    message.attach(part_html)

    with SMTP(config.smtp.server, config.smtp.port, context=context) as server:
        server.login(config.smtp.username, config.smtp.password)

        logger.debug("Sending msg to %s", receiver)

        server.sendmail(sender, receiver, message.as_string())
