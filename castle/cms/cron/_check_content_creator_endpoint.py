from AccessControl.SecurityManagement import newSecurityManager
from zope.component.hooks import setSite, getSite
from tendo import singleton
import argparse
import json
import requests
import os


def send_message(error_logs, webhook_url):
    site = getSite()
    message = {
        "cardsV2": [
            {
                "card": {
                    "header": {
                        "title": "Alert: @@Content-Creator endpoint throwing errors",
                        "subtitle": "Please delete the <b>/var/tmp</b> directory for <i>{}</i>".format(site.id),
                    },
                    "sections": [
                        {
                            "widgets": [
                                {
                                    "textParagraph": {
                                        "text": '<pre>{}</pre>'.format(error_logs)
                                    }
                                },
                            ]
                        }
                    ]
                }
            }
        ]
    }

    response = requests.post(
        webhook_url,
        data=json.dumps(message),
        headers={'Content-Type': 'application/json'}
    )

    if response.status_code != 200:
        print('error sending chat message: {}'.format(response.text))


def parse_logs(file_path, num_lines):

    with open(file_path, 'rb') as f:
        f.seek(0, os.SEEK_END)
        file_size = f.tell()
        block_size = 1024
        blocks = -1
        data = []
        lines_found = 0

        while lines_found < num_lines and abs(blocks * block_size) < file_size:
            f.seek(blocks * block_size, os.SEEK_END)
            data.insert(0, f.read(block_size))
            lines_found = ''.join(data).count('\n')
            blocks -= 1

        return ''.join(data).splitlines()[-num_lines:]


def search_lines(file_path, num_lines):
    capture = False
    error_logs = []

    lines = parse_logs(file_path, num_lines)
    for line in lines:
        if not capture:
            if "ERROR" in line and "@@content-creator" in line:
                capture = True
                error_logs.append(line)
        else:
            error_logs.append(line)
            if line.strip() == "------":
                break

    return "\n".join(error_logs) if error_logs else None


def _get_parsed_args():
    parser = argparse.ArgumentParser(description='Parse worker logs for @@content-creator endpoint status')
    parser.add_argument('--site-id', dest='site_id')
    parser.add_argument('--filepath', dest='filepath')
    parser.add_argument('--num-lines', dest='num_lines', default=500)
    parser.add_argument('--webhook-url', dest='webhook_url')
    args, _ = parser.parse_known_args()
    return args


def run(app):
    singleton.SingleInstance('check_content_creator_endpoint')
    args = _get_parsed_args()
    site = app[args.site_id]
    file_path = args.filepath
    num_lines = int(args.num_lines)
    webhook_url = args.webhook_url

    setSite(site)
    print('Set site to {}'.format(args.site_id))

    user = app.acl_users.getUser('admin')  # noqa
    newSecurityManager(None, user.__of__(app.acl_users))  # noqa

    error_logs = search_lines(file_path, num_lines)
    if error_logs:
        send_message(error_logs, webhook_url)


if __name__ == '__main__':
    run(app)  # noqa