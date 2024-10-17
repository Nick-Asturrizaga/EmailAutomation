from sqlalchemy import Column, Integer, Text, DateTime, func, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session


def init_history(filename):
    engine = create_engine(f"sqlite:///{filename}", connect_args={'check_same_thread': False})

    base.metadata.bind = engine

    session = scoped_session(sessionmaker())(bind=engine)

    base.metadata.create_all(engine)

    return session


base = declarative_base()


class DetectedError(base):
    __tablename__ = 'detected_errors'

    id = Column(Integer, primary_key=True)
    email = Column(Text, index=True)
    ticket = Column(Text, index=True)
    sys_component = Column(Text, index=True)
    error_message = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class History(base):
    __tablename__ = 'history'

    id = Column(Integer, primary_key=True)
    email = Column(Text, nullable=False)
    task_id = Column(Text, nullable=False)
    ticket_json = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    sys_updated_on = Column(DateTime, nullable=False)
    processed_at = Column(DateTime)


class Ticket:
    def __init__(self, number, summary, status, who_is_impacted, when, state, sys_updated_on):
        self.number = number
        self.summary = summary.rstrip()
        self.status = status
        self.who_is_impacted = who_is_impacted
        self.when = when
        self.state = state
        self.sys_updated_on = sys_updated_on

    def __repr__(self):
        return '<Ticket #{}: {}>'.format(self.number, self.summary)
