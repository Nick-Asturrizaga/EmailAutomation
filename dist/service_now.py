import locale
import logging

import pytz
import requests
from dateutil import parser

from models import TicketStatus, Ticket


def get_impact(impact_value, impact_display_value, risk_impact_analysis_display_value):
    logger.debug(impact_display_value)

    if impact_value == '3':
        return "No impact {}".format(risk_impact_analysis_display_value).rstrip()
    elif impact_value == '2':
        return "Medium impact {}".format(risk_impact_analysis_display_value).rstrip()
    elif impact_value == '1':
        return "High impact {}".format(risk_impact_analysis_display_value).rstrip()


def format_datetime(dt):
    if dt is None or dt.strip() == '':
        return ''

    dt = parser.parse(dt)
    dt = dt.astimezone(pytz.timezone('America/New_York'))

    # 09-16-2024 09:00:00 PM
    return dt.strftime("%m-%d-%Y %I:%M:%S %p")


logger = logging.getLogger(__name__)

logger.info(locale.getdefaultlocale())


def format_datetime_utc(dt):
    if dt is None:
        return ''

    dt = dt.astimezone(pytz.utc)

    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_datetime(dt):
    return parser.parse(dt)


def create_filter(after_than):
    """Create the filter to restrict the data from ServiceNow
    @type after_than: datetime
    """

    return ("state={}^ORstate={}^sys_updated_on>{}ORDERBYsys_created_on"
            .format(TicketStatus.Closed, TicketStatus.Scheduled, format_datetime_utc(after_than))
            )


def get_tickets_from_service_now(after_than, url, username, password):
    """get the tickets from ServiceNow
        @param after_than: datetime to filter tickets
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
        # 'sysparm_fields': 'number
        # ,state,short_description,work_start,work_end,impact,risk_impact_analysis',
        'sysparm_query': create_filter(after_than),
        # 'sys_updated_on'
    }

    logger.debug(query_strings)

    r = requests.get(api_url, params=query_strings, auth=(username, password))

    data = r.json()

    logger.debug(data)

    tickets = []

    for item in data['result']:
        ticket = Ticket(
            number=item['number'], state=TicketStatus(item['state']['value']),
            status=item['state']['display_value'],
            when="Date - Start {} and End time {}"
            .format(format_datetime(item['work_start']['value']),
                    format_datetime(item['work_end']['value'])),
            who_is_impacted=get_impact(item['impact']['value'], item['impact']['display_value'],
                                       item['risk_impact_analysis']['display_value']),
            summary=item['short_description']['display_value'],
            sys_updated_on=item['sys_updated_on']['value'],
        )

        tickets.append(ticket)

        logger.debug(ticket)

    return tickets
