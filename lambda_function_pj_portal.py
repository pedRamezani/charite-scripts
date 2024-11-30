# Native libraries
import csv
from datetime import datetime
from io import StringIO
import json
import os

# AWS
import boto3

# Other external libraries (have to be bundled with code)
# BeautifulSoup can be replaced with manual parsing or with native html.parser
from bs4 import BeautifulSoup
import re  # Can be replaced with manual parsing
import requests  # Can be replaced with native urllib.request

# Login E-Mail, stored in the expected environment variable
EMAIL = os.environ['email']
# Login password, stored in the expected environment variable
PASSWORD = os.environ['password']

# Sub Category ID, stored in the expected environment variable
# 1 for Chirurgie
# 2 for Innere Medizin
PJ_SUB_CATEGORY_ID = os.environ['pj_sub_category_id']
# University ID, stored in the expected environment variable
# 6 for Charité - Universitätsmedizin Berlin
UNIVERSITY_ID = os.environ['university_id']

# Gist API Token (i.e. fine-grained personal access tokens with gist read and write access), stored in the expected environment variable
GIST_API_TOKEN = os.environ['gist_api_token']
# Gist ID (found i.e. by listing all gists accessible with gist API token; Gist should host a valid standard CSV file called pj_portal.csv), stored in the expected environment variable
GIST_ID = os.environ['gist_id']

# Destination E-Mail (multiple addresses can be specified with the seperator "; "), stored in the expected environment variable
DESTINATION_EMAIL = os.environ['destination_email']

# AWS SES Client to send email notification
# Change region_name based of your location
client = boto3.client('ses', region_name='eu-north-1')

# Regex pattern to detect free slots: i.e. 12/19 is a free slot but 0/5 or other text isn't
free_slot_pattern = re.compile(r'(?P<free>[1-9]\d*)\/(?P<all>\d+)')


def extract(html):
    ''' Used to extract and return data from the tabular ajax response.
    '''
    data = []

    # We will specify the native parser to make this code cross compatible with other systems used by AWS
    # We will skip the first two table rows (header)
    for row in BeautifulSoup(markup=html, features="html.parser").find_all('tr')[2:]:
        cells = row.find_all('td')

        # First will first extract the hospital name (there is a short and a long version for each hospital)
        hospital = cells[4] \
            .find('span', class_='infobox_inhalt_lang') \
            .get_text("; ", strip=True) \
            .split('; ')[-1]

        # Now we will extract the availability information for the three tertials
        available = [
            entry.text.strip()
            for entry in cells[5:] if entry.text.strip()

        ]
        data.append([hospital, *available])

    return data


def create_html(current_data, previous_data):
    ''' Used to create and return a html table for the email notification.
    '''
    trs = ''

    for current_row, previous_row in zip(current_data, previous_data):
        # Add Hospital to table cells
        tds = '<td style="font-weight: bold; padding: .5rem 1rem">{data}</td>'.format(
            data=current_row[0]
        )

        for current_cell, previous_cell in zip(current_row[1:], previous_row[1:]):
            free_slots = free_slot_pattern.search(current_cell) is not None

            # Change the color from red to green if there is a free slot available
            color = ('#115e59', '#ccfbf1') if free_slots else \
                    ('#991b1b', '#fee2e2')
            # Highlight the cell if the data has changed
            if current_cell != previous_cell:
                # Updated cells are highlighted in yellow
                color = ('#854d0e', '#fef9c3')

            # Append availability cells to the hospital cell
            text_color, bg_color = color
            tds += '<td style="padding: .5rem; color: {text_color}; background-color: {bg_color}">{data}</td>'.format(
                data=current_cell,
                text_color=text_color,
                bg_color=bg_color
            )

        # Create a new table row with the constructed table cells
        trs += f'<tr>{tds}</tr>'

    html = '''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
    <head>
        <!--[if !mso]><!-->
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <!--<![endif]-->
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>PJ Portal Data</title>
        <style type="text/css">
            body {
                margin: 0;
                padding: 0;
                -webkit-text-size-adjust: 100%;
                -ms-text-size-adjust: 100%;
            }
            table,
            td {
                border-collapse: collapse;
                mso-table-lspace: 0pt;
                mso-table-rspace: 0pt;
            }
        </style>
    </head>
    <body>
        <table role="presentation" style="color: #212121">
            <thead style="font-weight: bold">
                <tr>
                    <th>Hospital</th>
                    <th>1. Tertial</th>
                    <th>2. Tertial</th>
                    <th>3. Tertial</th>
                </tr>
            </thead>
            <tbody>''' + trs + '''</tbody>
        </table>
    </body>
</html>
'''

    return html


def send_mail(current_data, previous_data):
    ''' Sends an email notification with Amazon SES and returns the message id.
    '''
    response = client.send_email(
        Destination={
            'ToAddresses': DESTINATION_EMAIL.split('; ')
        },
        Message={
            'Body': {
                'Html': {
                    'Charset': 'UTF-8',
                    'Data': create_html(current_data, previous_data),
                }
            },
            'Subject': {
                'Charset': 'UTF-8',
                'Data': 'PJ-Portal Data',
            },
        },
        Source=EMAIL
    )

    return response['MessageId']


def lambda_handler(event, context):
    pj_portal_session = requests.Session()
    pj_portal_session.headers = {
        # User-Agent': 'Hello there!', THIS WILL ALSO WORK
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.3'
    }

    print('Logging into account {} at {}...'.format(EMAIL, str(datetime.now())))
    try:
        home_page = pj_portal_session.post(
            url='https://www.pj-portal.de/index_be.php',
            data={
                "name_Login": "Login",
                "USER_NAME": EMAIL,
                "PASSWORT": PASSWORD,
                "form_login_submit": "anmelden"
            }
        )
        home_page.raise_for_status()
    except Exception as error:
        print('Login failed!')
        raise error
    else:
        print('Login passed!')

    print('Requesting ajax at {}...'.format(str(datetime.now())))
    try:
        ajax = pj_portal_session.post(
            url='https://www.pj-portal.de/ajax.php',
            data={
                "AJAX_ID": "5101011",
                "UNIVERSITAET_ID": UNIVERSITY_ID,
                "PJ_SUB_CATEGORY_ID": PJ_SUB_CATEGORY_ID,
                "STATUS_CHECKBOX": "0"
            }
        )
        ajax.raise_for_status()
    except Exception as error:
        print('Ajax failed!')
        raise error
    else:
        print('Ajax passed!')

    print('Extracting and comparing availability data at {}'.format(
        str(datetime.now())
    ))
    # Extract current data from the PJ Portal
    current_data = extract(ajax.json()['HTML'])

    try:
        gist_session = requests.Session()
        gist_session.headers.update({
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {GIST_API_TOKEN}',
            'X-GitHub-Api-Version': '2022-11-28'
        })

        pj_portal_gist = gist_session.get(
            f'https://api.github.com/gists/{GIST_ID}',
        )
        pj_portal_gist.raise_for_status()

    except Exception as error:
        print('Loading gist failed!')
        raise error
    else:
        print('Gist loaded!')

    # Load the existing data from the Gist
    reader = csv.reader(
        pj_portal_gist.json()
        ['files']['pj_portal.csv']['content'].split('\n')[:-1]
    )
    previous_data = list(reader)

    ses_message_id = None

    # Compare data and update Gist if changes are found
    changed = False
    for current_row, previous_row in zip(current_data, previous_data):
        if current_row != previous_row:
            changed = True
            break

    if changed:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerows(current_data)

        try:
            patch_response = gist_session.patch(
                url=f'https://api.github.com/gists/{GIST_ID}',
                data=json.dumps({
                    "description": "This is a subset of the PJ Portal data captured at {}.".format(
                        str(datetime.now())
                    ),
                    "files": {
                        "pj_portal.csv": {
                            "content": output.getvalue()
                        }
                    }
                })
            )
            patch_response.raise_for_status()
        except Exception as error:
            print('Gist patch failed!')
            raise error
        else:
            print('Gist patch successful!')

        # Pass both current and previous data
        ses_message_id = send_mail(current_data, previous_data)

    return {
        'data_changed': changed,
        'ses_message_id': ses_message_id
    }
