import json
import logging
import re

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
    if dt is None or dt.strip() == '':
        return ''

    dt = parser.parse(dt)
    dt = dt.astimezone(pytz.timezone('America/New_York'))

    # 09-16-2024 09:00:00 PM
    return dt.strftime("%m-%d-%Y %I:%M:%S %p")


logger = logging.getLogger(__name__)


def format_datetime_utc(dt):
    if dt is None:
        return ''

    dt = dt.astimezone(pytz.utc)

    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_datetime(dt):
    return parser.parse(dt)


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


def get_tickets_from_service_now(after_than, filter_, date_fields, capture, frequency_minutes, url, username, password):
    """get the tickets from ServiceNow
        @param after_than: datetime to filter tickets
        @param filter_: fields to filter and its values
        @param capture: define the capture expression to get who_is_impacted
        @param date_fields: the date fields to construct when field
        @param url: url of ServiceNow server
        @param username: ServiceNow username
        @param password: ServiceNow password
        @return: list of tickets
    """

    api_url = '{}/api/now/table/change_request'.format(url)

    query_strings = {
        'sysparm_limit': 2,
        'sysparm_exclude_reference_link': False,
        'sysparm_display_value': 'all',
        'sysparm_fields': get_fields(date_fields, capture),
        'sysparm_query': create_filter(after_than, filter_),
    }

    logger.debug(query_strings)

    r = requests.get(api_url, params=query_strings, auth=(username, password))
    r.raise_for_status()

    data = r.json()

    logger.debug(data)

    if logger.isEnabledFor(logging.DEBUG):
        with open("./test.json", "w") as f:
            f.write(json.dumps(data))

    tickets = []

    capture_field_name = list(capture.keys())[0]
    capture_expressions = capture[capture_field_name]

    for item in data['result']:
        ticket = Ticket(
            number=item['number']['value'],
            state=item['state']['value'],
            status=item['state']['display_value'],
            when="Date - Start {} and End time {}"
            .format(format_datetime(item[date_fields[0]]['value']),
                    format_datetime(item[date_fields[1]]['value'])),
            who_is_impacted=get_who_is_impacted(capture_expressions, item[capture_field_name]['value']),
            summary=item['short_description']['display_value'],
            sys_updated_on=item['sys_updated_on']['value'],
        )

        tickets.append(ticket)

        logger.debug(ticket)

    return tickets
