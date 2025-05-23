import boto3
from datetime import datetime, timedelta
from tabulate import tabulate
import pytz
import pandas as pd
import openpyxl
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText


# Create empty List for unused snapashot
Unused_snapshots = []
account_name = boto3.client('iam').list_account_aliases()['AccountAliases'][0]
print(f"Fetching Unused Snapshot Details for AWS account: {account_name}")

# Define time difference (last 6 months ago)
timedifference = datetime.now(pytz.utc) - timedelta(days=183)
print("Gathering Snapshots Details older than Date:", timedifference)


def snapshot_logic(region):
    # Get latest information of all AWS region
    try:
        ec2 = boto3.client('ec2', region_name=region)

        # Get latest information of all available EBS snapshots
        response = ec2.describe_snapshots(OwnerIds=['self'])['Snapshots']
        print(f"Found {len(response)} snapshot in {region}")
    except:
        return

    # Get latest information of all available EBS volume
    available_volume = ec2.describe_volumes()['Volumes']
    available_volume_id = {volume['VolumeId'] for volume in available_volume}
    print(f"Found {len(available_volume_id)} volumes in {region}")

    # Filter snapshots not associated with Volume and not in use since last 6 months
    for snapshot in response:
        if (snapshot['VolumeId'] is None or snapshot['VolumeId'] not in available_volume_id) and snapshot['StartTime'] < timedifference:
            print(f"Processing Snapshot:{snapshot['SnapshotId']}")
            try:
                volume_name_tag = 'N/A'
                if snapshot['VolumeId']:
                    volume = ec2.describe_volumes(VolumeIds=[snapshot['VolumeId']])['Volumes'][0]
                    volume_name_tag = next((tag['Value'] for tag in volume['Tags'] if tag['Key'] == 'Name'), 'N/A')
            except:
                print('Volume Tags Not available for Decomm Volumes')

            # Put All available information together
            Unused_snapshots.append(
                [region, snapshot['Description'], snapshot['SnapshotId'], snapshot['StartTime'].strftime('%Y-%m-%d'),
                 snapshot['VolumeId'] if snapshot['VolumeId'] else 'N/A', volume_name_tag, snapshot['VolumeSize']])


# Gather Information for All AWS regions
for region in boto3.Session().get_available_regions('ec2'):
    snapshot_logic(region)

# Printing Unused snapshot in Tabular format
output = tabulate(Unused_snapshots,
                  headers=['Region', 'Snapshot Description', 'Snapshot ID', "Date of Snapshot", "Associated Volume ID",
                           "Volume Name", "Snapshot Size(in GB)"],
                  tablefmt="orgtbl")
print(output)

# Printing Unused snapshot in Excel format, Excel file will get saved at location from where Script is executed
excel_output = pd.DataFrame(Unused_snapshots, columns=['Region', 'Snapshot Description', 'Snapshot ID', "Date of Snapshot", "Associated Volume ID", "Volume Name", "Snapshot Size(in GB)"])
excel_sheet = excel_output.to_excel(f'Unused_snapshots_{timedifference.strftime("%Y%m%d")}.xlsx', index=False)
excel_sheet_standard = excel_output.to_html()

#Email HTML formatting
def create_html_body(Unused_snapshots):
    html_body_1 = ("""\
            <html>
                <head></head>
                <body>
                    <p> Please find Unused Stale Snapshot Details for AWS account: """
                    + account_name +
                    """
                    </p>
                </body>
            </html>
            """)
    complete_body = html_body_1 + excel_sheet_standard 
    return complete_body


#Email Configuration details
def send_mail(Unused_snapshots, from_addr):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "AWS Stale Snapshot Report using BOTO3 module"
    recipients = ["soham.newalkar@sas.com","iaasopsnotifications@sas.com","ken.weaver@sas.com","steve.nickerson@sas.com","ajinkya.kulkarni@sas.com","prashant.gondkar@sas.com","keith.mccrae@sas.com","ryan.mccauley@sas.com"]
    msg['To'] = ",".join(recipients)
    msg['From'] = "replies-disabled@sas.com"
    msg_html = create_html_body(Unused_snapshots)

    pt2 = MIMEText(msg_html, 'html')

    msg.attach(pt2)

    # Attach Excel file
    with open(f'Unused_snapshots_{timedifference.strftime("%Y%m%d")}.xlsx', 'rb') as f:
        xls = MIMEApplication(f.read(), _subtype='xlsx')
        xls.add_header('content-disposition', 'attachment', filename=f'Unused_snapshots_{timedifference.strftime("%Y%m%d")}.xlsx')
        msg.attach(xls)

    mail_client = smtplib.SMTP("osmtp.vsp.sas.com", port=25)
    mail_client.ehlo()
    mail_client.starttls()
    mail_client.ehlo()
    mail_client.sendmail(from_addr, recipients, msg=msg.as_string())
    mail_client.quit()


if Unused_snapshots:
    send_mail(Unused_snapshots, from_addr="replies-disabled@sas.com")
