import json
import os
import traceback
from datetime import datetime, timedelta
from itertools import product
from logging import getLogger, basicConfig
from os import path

from huey import SqliteHuey, crontab, signals
from sqlalchemy import and_

from config import read_app_config
from models import DetectedError, History, init_history
from send_email import send_email
from service_now import get_datetime, get_tickets_from_service_now, get_access_token


def init_huey():
    if not path.isdir('./data'):
        os.mkdir('./data')

    return SqliteHuey(filename='./data/queue.db')


def init_logger():
    log_level = os.environ.get('LOG_LEVEL', 'INFO')

    basicConfig(level=log_level)
    getLogger('sqlalchemy.engine').setLevel(log_level)
    getLogger("requests.packages.urllib3").setLevel(log_level)

    return getLogger(__name__)


huey = init_huey()
logger = init_logger()

session = init_history("./data/history.db")

config = read_app_config()

access_token = get_access_token(config)

logger.debug("Access Token %s", access_token)


@huey.task(retries=3, retry_delay=60)
def new_ticket_email(ticket, email):
    send_email(email, ticket, config)


@huey.signal(signals.SIGNAL_ERROR)
def save_detected_errors(signal, task, exc):
    if task.retries > 0:
        return

    subject = f'Task [{task.name}] failed'
    message = f"""Task ID: {task.id}
    Args: {task.args}
    Kwargs: {task.kwargs}
    Exception: {exc}
    {traceback.format_exc()}"""

    ticket_number = None
    email = None

    if task.args is not None and len(task.args) > 1:
        ticket = task.args[0]
        ticket_number = ticket.number

        email = task.args[1]

    detected_error = DetectedError(ticket=ticket_number, email=email, error_message=message)

    session.add(detected_error)
    session.commit()


@huey.post_execute()
def post_execute(task, task_value, exc):
    if not exc is None:
        logger.error("Error detected %s executing task %s", exc, task.id)
        return

    history = session.query(History).where(History.task_id == task.id).first()

    if not history:
        return

    history.processed_at = datetime.utcnow()

    session.add(history)
    session.commit()


@huey.periodic_task(crontab(minute=config.service_now.frequency_in_minutes, strict=True))
def enqueue_tickets_and_emails():
    """Create an entry for each combination of ticket and email"""

    sys_updated_on = (session.query(History.sys_updated_on)
                      .where(History.processed_at.is_(None))
                      .order_by(History.sys_updated_on.desc()).first())

    if sys_updated_on is None:
        sys_updated_on = datetime.utcnow() - timedelta(days=config.service_now.oldest_date_in_days)
    else:
        sys_updated_on = sys_updated_on[0] - timedelta(minutes=10)

    tickets = get_tickets_from_service_now(after_than=sys_updated_on, config=config,
                                           access_token=access_token)

    for ticket, email in product(tickets, config.emails.receivers):
        if not email:
            logger.critical("Missing email. Restarting process %s.", config)
            exit(65)

        ticket_json = json.dumps(ticket, default=lambda k: k.__dict__)

        already_processed = session.query(History).where(and_(History.email == email,
                                                              History.ticket_json == ticket_json,
                                                              History.processed_at.isnot(None))
                                                         ).first()

        if already_processed:
            logger.warning("Already processed %s %s", email, ticket_json)
            continue

        task = new_ticket_email(ticket, email)

        print(task.id)

        history = History(email=email, ticket_json=ticket_json, task_id=task.id,
                          sys_updated_on=get_datetime(ticket.sys_updated_on))

        session.add(history)
        session.commit()
