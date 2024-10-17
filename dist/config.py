import yaml


class Config:
    class ServiceNow:
        def __init__(self, url, username, password, filter_, date_fields, capture, frequency_in_minutes, client_id,
                     client_secret, grant_type, max_records, oldest_date_in_days):
            self.url = url.rstrip('/')
            self.username = username
            self.password = password
            self.filter_ = filter_
            self.date_fields = date_fields
            self.capture = capture
            self.client_id = client_id
            self.client_secret = client_secret
            self.grant_type = grant_type
            self.max_records = max_records
            self.oldest_date_in_days = oldest_date_in_days
            self.frequency_in_minutes = "*/{}".format(frequency_in_minutes)

        def __repr__(self):
            return "ServiceNow(url={}, username={}, password={})".format(self.url, self.username, self.password)

    class Emails:
        def __init__(self, sender, subject, receivers):
            self.sender = sender
            self.subject = subject
            self.receivers = receivers

        def __repr__(self):
            return "Emails(sender={}, subject={}, receivers={})".format(self.sender, self.subject, self.receivers)

    class Smtp:
        def __init__(self, server, username, password):
            self.server = server
            self.username = username
            self.password = password

    def __init__(self, service_now, emails, smtp):
        self.service_now = service_now
        self.emails = emails
        self.smtp = smtp

    def __repr__(self):
        return "Config ServiceNow {}, Emails {}, Smtp {}".format(self.service_now, self.emails, self.smtp)


def read_app_config():
    with open('./config/config.yaml', 'r') as f:
        content = yaml.safe_load(f)

    service_now_map = content['serviceNow']
    emails_map = content['emails']
    smtp_map = content['smtp']

    return Config(service_now=Config.ServiceNow(
        url=service_now_map['url'],
        username=service_now_map['username'],
        password=service_now_map['password'],
        client_id=service_now_map['clientId'],
        client_secret=service_now_map['clientSecret'],
        grant_type=service_now_map['grantType'],
        frequency_in_minutes=service_now_map['query']['frequencyInMinutes'],
        oldest_date_in_days=service_now_map['query']['oldestDateInDays'],
        max_records=service_now_map['query']['maxRecords'],
        filter_=service_now_map['query']['filter'],
        date_fields=service_now_map['query']['dateFields'],
        capture=service_now_map['capture']
    ), emails=Config.Emails(
        sender=emails_map['sender'],
        subject=emails_map['subject'],
        receivers=filter(None, emails_map['receivers']),
    ), smtp=Config.Smtp(
        server=smtp_map['server'],
        username=smtp_map['username'],
        password=smtp_map['password']
    ))
