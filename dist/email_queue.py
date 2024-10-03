import json
import os
import traceback
from datetime import datetime, timedelta
from itertools import product
from logging import getLogger
from os import path

from huey import SqliteHuey, crontab, signals
from sqlalchemy import and_

from app import create_app, db
from models import DetectedError, History
from send_email import config, send_email
from service_now import get_datetime
from service_now import get_tickets_from_service_now

if not path.isdir('./data'):
    os.mkdir('./data')

huey = SqliteHuey(filename='./data/queue.db')


@huey.task()
def new_ticket_email(ticket, email):
    send_email(email, ticket)


logger = getLogger(__name__)

app = create_app()

ctx = app.app_context()

with ctx:
    db.create_all()


@huey.signal(signals.SIGNAL_ERROR)
def save_detected_errors(signal, task, exc):
    if task.retries > 0:
        return

    with (ctx):
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

        db.session.add(detected_error)
        db.session.commit()


@huey.post_execute()
def post_execute(task, task_value, exc):
    with (ctx):
        history = History.query.filter(History.task_id == task.id).first()

        if not history:
            return

        history.processed_at = datetime.now()

        db.session.add(history)
        db.session.commit()


@huey.periodic_task(crontab(minute=config.service_now.frequency_minutes, strict=True))
def enqueue_tickets_and_emails():
    """Create an entry for each combination of ticket and email"""

    with (ctx):
        sys_updated_on = History.query.with_entities(History.sys_updated_on).filter(
            History.processed_at.is_(None)).order_by(
            History.sys_updated_on.desc()).first() or datetime.now() - timedelta(days=4 * 365)

        tickets = get_tickets_from_service_now(sys_updated_on - timedelta(hours=10), **config.service_now.__dict__)

        for ticket, email in product(tickets, config.emails.receivers):
            if not email:
                logger.critical("Missing email. Restarting process %s.", config)
                exit(65)

            ticket_json = json.dumps(ticket, default=lambda k: k.__dict__)

            already_processed = History.query.filter(and_(History.email == email,
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

            db.session.add(history)
            db.session.commit()
