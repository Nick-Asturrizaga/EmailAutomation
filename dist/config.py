import logging
import os

import yaml


class Config:
    class ServiceNow:
        def __init__(self, url, username, password):
            self.url = url
            self.username = username
            self.password = password

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
        def __init__(self, server, port, username, password):
            self.server = server
            self.port = port
            self.username = username
            self.password = password

    def __init__(self):
        Config.config_log()

        with open('./config/config.yaml', 'r') as f:
            content = yaml.safe_load(f)

        self.service_now = Config.ServiceNow(
            url=content['serviceNow']['url'],
            username=content['serviceNow']['username'],
            password=content['serviceNow']['password']
        )

        self.emails = Config.Emails(
            sender=content['emails']['sender'],
            subject=content['emails']['subject'],
            receivers=filter(None, content['emails']['receivers'])
        )

        self.smtp = Config.Smtp(
            server=content['smtp']['server'],
            port=content['smtp']['port'],
            username=content['smtp']['username'],
            password=content['smtp']['password']
        )

        print(self.smtp)

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
