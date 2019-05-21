"""
Global config file. Change variable below as needed but ensure that the log have the correct permissions.
"""

from datetime import datetime

# file settings
LOG_FILENAME = 'tmp/pymailer.log'
CSV_RETRY_FILENAME = '/tmp/pymailer.csv'
STATS_FILE = 'tmp/pymailer-%s.stat' % str(datetime.now()).replace(' ', '-').replace(':', '-').replace('.', '-')

# ACTION 
# -live for live environment 
# -test for test environment
ACTION = '-test'

# MailTemplate file
HTML_PATH = "mailTemplate_image.html"

# Database File
CSV_PATH = 'database.csv'

# Attachment file path
ATTACHMENT_PATH = 'assests_disable/'
ATTACHMENT_NAME = ''


# Mail Subject
SUBJECT = 'SUBJECT'

# smtp settings
SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = '465'

# the address and name the email comes from

FROM_NAME = 'SENDER_NAME'
FROM_EMAIL = 'EMAIL_ADDRESS'
FROM_PASSWORD = 'PASSWORD'


# test recipients list
TEST_RECIPIENTS = [
    {'name': 'dynamic input 1', 'email':'chocha.ashish@gmail.com', 'GRAPH_IMAGE_TYPE': 'https://via.placeholder.com/300/09f.png/fff%20C/O%20https://placeholder.com/'},
]

#  add or modify category names and links as per your requirements.
CATEGORY_TYPE = {
	'graph1': 'https://drive.google.com/thumbnail?id=1o3SoM3nPXUOnAKYjYiOf_5Ny1Uhu0Zvc&sz=w600-h600',
	'graph2': 'https://drive.google.com/thumbnail?id=1o3SoM3nPXUOnAKYjYiOf_5Ny1Uhu0Zvc&sz=w600-h600',
	'graph3': 'https://drive.google.com/thumbnail?id=1o3SoM3nPXUOnAKYjYiOf_5Ny1Uhu0Zvc&sz=w600-h600',
}