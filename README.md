# Start-end Email Automation

## Goals

- the project aims to consume tickets from ServiceNow and email departments every time there are changes.

## Requirements

- Python 3.6.8
- Ansible 2.9

## How to run?

- `cd dist`
- `ansible-playbook playbook.yaml`

### or

- `cd dist`
- `python -m venv .venv`
- `source .venv/bin/activate`
- `pip install -r requirements.txt`
- `python huey_consumer.py email_queue.huey`

---------------------------------------------------------------------------------------------------------------------

- `serviceNow.url`
- `serviceNow.username`
-user authorized to call the API
- `serviceNow.Password`

`ServiceNow.query.frequency.minutes`
`-number of minutes between querying ServiceNow`
`ServiceNow.query.filter`

`-list of fields to filter the API and the list of values`
 -<field_name>
  -<value1>
  -<value2>

- `serviceNow.query.date_fields`
- `serviceNow.query.capture`
 -<field_name>
  -<text to find the value to put on who is impacted>

- `smtp.server`
- `smtp.port`
- `smtp.username`
- `smtp.password`
- `emails.sender`
- `emails.subject`

- `emails.receivers`
-list of emails that will be sent when there are ticket changes

- `emails.technicalIssues`
-list of emails that will be sent when there are technical issues
