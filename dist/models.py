from app import db


class DetectedError(db.Model):
    __tablename__ = 'detected_errors'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text, index=True)
    ticket = db.Column(db.Text, index=True)
    sys_component = db.Column(db.Text, index=True)
    error_message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)


class History(db.Model):
    __tablename__ = 'history'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text, nullable=False)
    task_id = db.Column(db.Text, nullable=False)
    ticket_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    sys_updated_on = db.Column(db.DateTime, nullable=False)
    processed_at = db.Column(db.DateTime)


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
