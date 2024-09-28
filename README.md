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
