import logging
import os

import yaml


class Config:
    class ServiceNow:
        def __init__(self, url, username, password, filter_, date_fields, capture, frequency_minutes):
            self.url = url
            self.username = username
            self.password = password
            self.filter_ = filter_
            self.date_fields = date_fields
            self.capture = capture
            self.frequency_minutes = "*/{}".format(frequency_minutes)

        def __repr__(self):
            return "ServiceNow(url={}, username={}, password={})".format(self.url, self.username, self.password)

    class Emails:
        def __init__(self, sender, subject, receivers, technical_issues):
            self.sender = sender
            self.subject = subject
            self.receivers = receivers
            self.technical_issues = technical_issues

        def __repr__(self):
            return "Emails(sender={}, subject={}, receivers={})".format(self.sender, self.subject, self.receivers)

    class Smtp:
        def __init__(self, server, port, username, password):
            self.server = server
            self.port = port
            self.username = username
            self.password = password

    def __init__(self):
        Config.config_log()

        with open('./config/config.yaml', 'r') as f:
            content = yaml.safe_load(f)

        service_now_map = content['serviceNow']

        self.service_now = Config.ServiceNow(
            url=service_now_map['url'],
            username=service_now_map['username'],
            password=service_now_map['password'],
            frequency_minutes=service_now_map['query']['frequency']['minutes'],
            filter_=service_now_map['query']['filter'],
            date_fields=service_now_map['query']['date_fields'],
            capture=service_now_map['capture']
        )

        emails_map = content['emails']

        self.emails = Config.Emails(
            sender=emails_map['sender'],
            subject=emails_map['subject'],
            receivers=filter(None, emails_map['receivers']),
            technical_issues=filter(None, emails_map['technicalIssues'])
        )

        smtp_map = content['smtp']

        self.smtp = Config.Smtp(
            server=smtp_map['server'],
            port=smtp_map['port'],
            username=smtp_map['username'],
            password=smtp_map['password']
        )

    def __repr__(self):
        return "Config ServiceNow {}, Emails {}, Smtp {}".format(self.service_now, self.emails, self.smtp)

    @staticmethod
    def config_log():
        """
            Configure the log level to allow debugging.
            It can be changed by setting the LOG_LEVEL environment variable.
        """

        logging.basicConfig()
        logging.getLogger().setLevel(os.environ.get('LOG_LEVEL', 'INFO'))
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))
        requests_log.propagate = True


if __name__ == '__main__':
    config = Config()
