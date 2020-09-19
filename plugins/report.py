from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate, formataddr
from email.header import Header
import smtplib
import csv
from os.path import basename
from plugins.nornir_addon import playbook_dir
import logging
from datetime import date
import shutil
dates = date.today().strftime("%d_%m_%Y")
logger = logging.getLogger(__name__)

# send email report
def send_report(user, send_to, playbook_path, subject, content):
    playbook_name = playbook_path.split('/')[-1]
    output_path = playbook_dir(playbook_name)
    # archive playbook dir
    shutil.make_archive(f'{playbook_name}-{dates}', 'zip', output_path)

    # attach file list
    file_list = [f'{playbook_name}-{dates}.zip', f'{playbook_path}.py']
    logger.info('sending report to {}'.format(','.join(send_to)))

    # init email msg
    msg = MIMEMultipart()
    msg['From'] = formataddr(
        (str(Header(user, 'utf-8')), 'no-reply@x.net.nz'))
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg.attach(MIMEText(content))

    # attach file
    for f in file_list:
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
        msg.attach(part)

    # send email
    with smtplib.SMTP('localhost') as s:
        s.sendmail('no-reply@snap.net.nz', send_to, msg.as_string())

# generate csv report


def generate_report(devices, playbook_name):
    logger.info("Generating report")
    output_path = playbook_dir(playbook_name)
    with open(f'{output_path}/reports.csv', 'w', newline='') as file:
        writer = csv.writer(file)

        # get all host dicts
        host_dicts = devices.inventory.get_hosts_dict()
        for host in host_dicts:
            host_data = host_dicts[host]['data']

            # if report_deatils exists, add into csv report
            if 'report_details' in host_data:
                writer.writerows(host_data['report_details'])

            # if no report_details means pass
            else:
                writer.writerow(
                    [host, host_dicts[host]['hostname'], host_data['description'], 'Pass'])

