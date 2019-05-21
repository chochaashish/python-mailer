# Bluk Mail sender Script
# To send mail in live environment
# Example: python pymailer.py -live

# To send mail in Test environment
# Example: python pymailer.py -test

import csv
import logging
import os
import re
import smtplib
import sys

from datetime import datetime
from email import message
from time import sleep

import config
import error_logs

from email import encoders 
from email.mime.text import MIMEText 
from email.mime.base import MIMEBase 
from email.mime.multipart import MIMEMultipart

# setup logging to specified log file
logger = error_logs.get_logger(__name__)
class PyMailer():
    """
    A python bulk mailer commandline utility. Takes five arguments: the path to the html file to be parsed; the
    database of recipients (.csv); the subject of the email; email adsress the mail comes from; and the name the email
    is from.
    """
    def __init__(self, html_path, csv_path, subject, *args, **kwargs):
        self.html_path = html_path
        self.csv_path = csv_path
        self.subject = subject
        self.from_name = kwargs.get('from_name', config.FROM_NAME)
        self.from_email = kwargs.get('to_name', config.FROM_EMAIL)

    def _stats(self, message):
        """
        Update stats log with: last recipient (incase the server crashes); datetime started; datetime ended; total
        number of recipients attempted; number of failed recipients; and database used.
        """
        try:
            stats_file = open(config.STATS_FILE, 'w+')
        except IOError:
            raise IOError("Invalid or missing stats file path.")

        stats_entries = stats_file.read().split('\n')

        # check if the stats entry exists if it does overwrite it with the new message
        is_existing_entry = False
        if stats_entries:
            for i, entry in enumerate(stats_entries):
                if entry:
                    if message[:5] == entry[:5]:
                        stats_entries[i] = message
                        is_existing_entry = True

        # if the entry does not exist append it to the file
        if not is_existing_entry:
            stats_entries.append(message)

        stats_file = open(config.STATS_FILE, 'w+')
        for entry in stats_entries:
            if entry:
                stats_file.write("%s\n" % entry)
        stats_file.close()

    def _validate_email(self, email_address):
        """
        Validate the supplied email address.
        """
        if not email_address or len(email_address) < 5:
            print( 1)
            return None
        if not re.match(r'^[a-zA-Z0-9._%-+]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$', email_address):
            return None
        return email_address

    def _html_parser(self, recipient_data):
        """
        Open, parse and substitute placeholders with recipient data.
        """
        try:
            html_file = open(self.html_path, 'r+',encoding="utf-8")
        except IOError:
            raise IOError("Invalid or missing html file path.")

        html_content = html_file.read()
        if not html_content:
            raise Exception("The html file is empty.")

        # replace all placeolders associated to recipient_data keys
        if recipient_data:
            for key, value in recipient_data.items():
                placeholder = "<!--%s-->" % key
                html_content = (html_content).replace(placeholder, value)
                # html_content = str(html_content).replace(placeholder, value)

        return html_content

    def _form_email(self, recipient_data):
        """
        Form the html email, including mimetype and headers.
        """
        # form the recipient and sender headers
        recipient = "%s <%s>" % (recipient_data.get('name'), recipient_data.get('email'),)
        sender = "%s <%s>" % (self.from_name, self.from_email)
        # get the html content
        html_content = self._html_parser(recipient_data)

        # instatiate the email object and assign headers
        email_message = MIMEMultipart()
        email_message.add_header('From', sender)
        email_message.add_header('To', recipient)
        email_message.add_header('Subject', self.subject)
        email_message.add_header('MIME-Version', '1.0')
        email_message.add_header('Content-Type', 'text/html; charset="utf-8"')
        email_message.attach(MIMEText(html_content,'html'))

        attachment_file = os.path.join(config.ATTACHMENT_PATH, config.ATTACHMENT_NAME)
        if os.path.exists(attachment_file):
            # instance of MIMEBase and named as p 
            attachment_part = MIMEBase('application', 'octet-stream') 
            attachment = open(attachment_file, "rb") 
            # To change the payload into encoded form 
            attachment_part.set_payload(attachment.read()) 
              
            # encode into base64 
            encoders.encode_base64(attachment_part) 
               
            attachment_part.add_header('Content-Disposition', "attachment;filename= %s" % config.ATTACHMENT_NAME)
            email_message.attach(attachment_part)
        else :
            logger.warning("attachment file not found")
        return email_message.as_string()

    def _parse_csv(self, csv_path=None):
        """
        Parse the entire csv file and return a list of dicts.
        """
        is_resend = csv_path is not None
        if not csv_path:
            csv_path = self.csv_path

        try:
            csv_file = open(csv_path, 'r+')
        except IOError:
            raise IOError("Invalid or missing csv file path.")

        csv_reader = csv.reader(csv_file)
        recipient_data_list = []
        for i, row in enumerate(csv_reader):
            if i == 0:
                continue
            # test indexes exist and validate email address
            try:
                recipient_name = row[0]
                recipient_email = self._validate_email(row[1])
                GRAPH_IMAGE_TYPE = row[2]
                
            except IndexError:
                recipient_name = ''
                recipient_email = None

            # log missing email addresses and line number
            if not recipient_email:
                logger.warning("Recipient email missing or invalid in line %s" % i)
            else:
                recipient_data_list.append({
                    'name': recipient_name,
                    'email': recipient_email,
                    'GRAPH_IMAGE_TYPE': config.CATEGORY_TYPE.get(GRAPH_IMAGE_TYPE),
                })

        # clear the contents of the resend csv file
        if is_resend:
            csv_file_write = open(csv_path, 'w+')
            csv_file_write.write('')
            csv_file_write.close()

        csv_file.close()

        return recipient_data_list

    def send(self, retry_count=0, recipient_list=None):
        """
        Iterate over the recipient list and send the specified email.
        """
        if not recipient_list:
            recipient_list = self._parse_csv()

        # save the number of recipient and time started to the stats file
        if not retry_count:
            self._stats("TOTAL RECIPIENTS: %s" % len(recipient_list))
            self._stats("START TIME: %s" % datetime.now())

        # instantiate the number of falied recipients
        failed_recipients = 0

        for recipient_data in recipient_list:
            # instantiate the required vars to send email
            message = self._form_email(recipient_data)
            if recipient_data.get('name'):
                recipient = "%s <%s>" % (recipient_data.get('name'), recipient_data.get('email'),)
            else:
                recipient = recipient_data.get('name')
            sender = "%s <%s>" % (self.from_name, self.from_email)

            # send the actual email
            smtp_server = smtplib.SMTP_SSL(host=config.SMTP_HOST, port=config.SMTP_PORT)
            # login to senders account
            smtp_server.login(config.FROM_EMAIL, config.FROM_PASSWORD)
            try:

                smtp_server.sendmail(sender, recipient, message)
                print("Mail sent to Recipient: %s" % recipient)
                logger.info("Mail sent to Recipient: %s" % recipient)
                # save the last recipient to the stats file incase the process fails
                self._stats("LAST RECIPIENT: %s" % recipient)

                # allow the system to sleep for .25 secs to take load off the SMTP server
                sleep(0.25)
            except:
                logger.error("Recipient email address failed: %s" % recipient)

                # save the number of failed recipients to the stats file
                failed_recipients = failed_recipients + 1
                self._stats("FAILED RECIPIENTS: %s" % failed_recipients)

    def send_test(self):
        self.send(recipient_list=config.TEST_RECIPIENTS)

    def resend_failed(self):
        """
        Try and resend to failed recipients two more times.
        """
        for i in range(1, 3):
            self.send(retry_count=i)

    def count_recipients(self, csv_path=None):
        return len(self._parse_csv(csv_path))


def main():

    if not os.path.exists(config.STATS_FILE):
        open(config.STATS_FILE, 'wb').close()

    try:
        action, html_path, csv_path, subject = config.ACTION,config.HTML_PATH,config.CSV_PATH,config.SUBJECT
    except ValueError:
        print( "Not enough argumants supplied. PyMailer requests 1 option and 3 arguments: ./pymailer -s html_path csv_path subject")
        sys.exit()

    if os.path.splitext(html_path)[1] != '.html':
        print( "The html_path argument doesn't seem to contain a valid html file.")
        sys.exit()

    if os.path.splitext(csv_path)[1] != '.csv':
        print( "The csv_path argument doesn't seem to contain a valid csv file.")
        sys.exit()

    pymailer = PyMailer(html_path, csv_path, subject)

    if action == '-live':
        if input("You are about to send to %s recipients. Do you want to continue (yes/no)? " % pymailer.count_recipients()) == 'yes':
            # save the csv file used to the stats file
            pymailer._stats("CSV USED: %s" % csv_path)

            # send the email and try resend to failed recipients
            pymailer.send()
            # pymailer.resend_failed()
        else:
            print( "Aborted.")
            sys.exit()

    elif action == '-test':
        if input("You are about to send a test mail to all recipients as specified in config.py. Do you want to continue (yes/no)? ") == 'yes':
            pymailer.send_test()
        else:
            print( "Aborted.")
            sys.exit()

    else:
        print( "%s option is not support. Use either [-s] to send to all recipients or [-t] to send to test recipients" % action)

    # save the end time to the stats file
    pymailer._stats("END TIME: %s" % datetime.now())

if __name__ == '__main__':
    main()
