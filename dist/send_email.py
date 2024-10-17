from logging import getLogger

from redmail import EmailSender

logger = getLogger(__name__)


def send_email(receiver, ticket, config):
    if receiver is None:
        logger.critical("Receiver email not filled.")
        exit(65)

    placeholder_values = {
        'subject': config.emails.subject,
        'summary': ticket.summary,
        'status': ticket.status,
        'who_is_impacted': ticket.who_is_impacted,
        'when': ticket.when,
    }

    email = EmailSender(
        host=config.smtp.server,
        port=0,
        username=config.smtp.username,
        password=config.smtp.password,
    )

    email.set_template_paths(
        html="./templates",
        text="./templates",
    )

    logger.debug("Sending msg to %s", receiver)

    email.send(
        subject=config.emails.subject,
        sender=config.emails.sender,
        receivers=[receiver],
        body_params=placeholder_values,
        html_template="email.html.jinja",
        text_template="email.text.jinja",
        body_images={
            "maintenance_icon": "./templates/images/maintenance-icon.png"
        }
    )
