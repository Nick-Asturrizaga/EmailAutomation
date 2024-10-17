import re
from logging import getLogger

import pytz
import requests
from dateutil import parser

from models import Ticket


def get_who_is_impacted(capture_expressions, field_value):
    logger.debug("Pattern matching %s", r'({})(.+)'.format('|'.join(capture_expressions)))

    result = re.search(r'({})(.+)'.format('|'.join(capture_expressions)), field_value, re.IGNORECASE | re.MULTILINE)

    if result is None:
        return ""

    return result.group(2).strip()


def format_datetime(dt):
    """
    Format date time according to email format
    @param dt: str
    @return: str
        ex. 09-16-2024 09:00:00 PM
    """
    if dt is None or dt.strip() == '':
        return ''

    dt = parser.parse(dt)
    dt = dt.astimezone(pytz.timezone('America/New_York'))

    return dt.strftime("%m-%d-%Y %I:%M:%S %p")


logger = getLogger(__name__)


def format_datetime_utc(dt):
    """
    Format date time according to ServiceNow format
    @param dt: datetime
    @return: str
    """
    if dt is None:
        return ''

    dt = dt.astimezone(pytz.utc)

    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_datetime(dt):
    return parser.parse(dt)


def get_access_token(config):
    url = f"{config.service_now.url}/oauth_token.do"

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    data = {
        'username': config.service_now.username,
        'password': config.service_now.password,
        'grant_type': config.service_now.grant_type,
        'client_id': config.service_now.client_id,
        'client_secret': config.service_now.client_secret
    }

    response = requests.post(url, headers=headers, data=data)

    return response.json()['access_token']


def create_filter(after_than, filter_):
    """Create the dynamic_filter to restrict the data from ServiceNow
    @param filter_: fields to filter and its values
    @type after_than: datetime
    """

    dynamic_filter = ""

    for field, values in filter_.items():
        if dynamic_filter != "":
            dynamic_filter += "^"

        or_condition = ""

        for value in values:
            if or_condition == "":
                or_condition = "{}={}".format(field, value)
            else:
                or_condition += "^OR{}={}".format(field, value)

        dynamic_filter += or_condition

    logger.debug("Dynamic filter %s", dynamic_filter)

    return ("{}^sys_updated_on>{}ORDERBYsys_updated_on"
            .format(dynamic_filter, format_datetime_utc(after_than))
            )


def get_fields(date_fields, capture):
    return "number,state,sys_updated_on,short_description,{},{}".format(",".join(date_fields), ",".join(capture.keys()))


def get_tickets_from_service_now(after_than, config, access_token):
    """get the tickets from ServiceNow
        @param after_than:
        @param config:
        @param access_token: ServiceNow accessToken
        @return: list of tickets
    """

    api_url = '{}/api/now/table/change_request'.format(config.service_now.url)

    query_strings = {
        'sysparm_limit': config.service_now.max_records,
        'sysparm_exclude_reference_link': False,
        'sysparm_display_value': 'all',
        'sysparm_fields': get_fields(config.service_now.date_fields, config.service_now.capture),
        'sysparm_query': create_filter(after_than, config.service_now.filter_),
    }

    logger.debug(query_strings)

    response = requests.get(api_url, params=query_strings, headers={'Authorization': 'Bearer {}'.format(access_token)})

    if response.status_code != 200:
        logger.error("Error reading from ServiceNow %s", response.text)

        response.raise_for_status()

    data = response.json()

    logger.debug("Data", data)

    tickets = []

    capture_field_name = list(config.service_now.capture.keys())[0]
    capture_expressions = config.service_now.capture[capture_field_name]

    for item in data['result']:
        ticket = Ticket(
            number=item['number']['value'],
            state=item['state']['value'],
            status=item['state']['display_value'],
            when="Date - Start {} and End time {}"
            .format(format_datetime(item[config.service_now.date_fields[0]]['value']),
                    format_datetime(item[config.service_now.date_fields[1]]['value'])),
            who_is_impacted=get_who_is_impacted(capture_expressions, item[capture_field_name]['value']),
            summary=item['short_description']['display_value'],
            sys_updated_on=item['sys_updated_on']['value'],
        )

        tickets.append(ticket)

        logger.debug(ticket)

    return tickets
