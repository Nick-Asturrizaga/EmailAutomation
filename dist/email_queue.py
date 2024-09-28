import json
from datetime import datetime, timedelta
from itertools import product
from logging import getLogger

from huey import SqliteHuey, crontab
from sqlalchemy import and_

from app import create_app, db
from models import History
from send_email import config, send_email
from service_now import get_datetime
from service_now import get_tickets_from_service_now

huey = SqliteHuey(filename='./data/queue.db')


@huey.task()
def new_ticket_email(ticket, email):
    send_email(email, ticket)


logger = getLogger(__name__)

app = create_app()

ctx = app.app_context()

with ctx:
    db.create_all()


@huey.post_execute()
def post_execute(task, task_value, exc):
    with (ctx):
        history = History.query.filter(History.task_id == task.id).first()

        if not history:
            return

        history.processed_at = datetime.now()

        db.session.add(history)
        db.session.commit()


@huey.periodic_task(crontab(minute='*'))
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
