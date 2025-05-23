import subprocess
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import socket

# Function to send an email
def send_email(subject, body):
    # SMTP configuration
    smtp_server = "osmtp.vsp.sas.com"
    smtp_port = 25
    from_address = "iaasopsnotifications@sas.com"
    to_address = "iaasopsnotifications@sas.com"

    # Create email
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg['To'] = to_address
    msg['Subject'] = subject

    # Attach the body with the email
    msg.attach(MIMEText(body, 'plain'))

    # Send email using SMTP
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.sendmail(from_address, to_address, msg.as_string())
        print(f"Email sent: {subject}")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Get hostname
hostname = socket.gethostname()

# Check nginx service status
status = subprocess.getoutput("systemctl is-active nginx")

if status != "active":
    # Try to restart nginx service
    subprocess.run(["systemctl", "restart", "nginx.service"])
    time.sleep(20)

    # Get nginx configuration failure reason
    config_test = subprocess.getoutput("nginx -t 2>&1 | tail -3")

    # Nginx service status
    nginx_status = subprocess.getoutput("systemctl status nginx.service 2>&1 | head -3")

    # Re-check nginx service status
    restatus = subprocess.getoutput("systemctl is-active nginx")

    if restatus != "active":
        # Nginx service failed again, send failure email
        subject = "NGINX Service Failure"
        body = f"""The NGINX service on the server {hostname} is not in Active State

Nginx Service Status-
{nginx_status}

Latest Logs for Nginx Service
{config_test}

Please fix the Nginx Configuration on Priority

This is automated Notification Workflow Configured by sonewa on host {hostname}

Regards,
Iaas HostOps
"""
        send_email(subject, body)
    else:
        # Nginx service successfully restarted, send recovery email
        subject = "NGINX Service Recovery"
        body = f"""The NGINX service on the server {hostname} was in a failed state but has been successfully restarted and is now active.

This is automated Notification Workflow Configured by sonewa on host {hostname}

Regards,
Iaas HostOps
"""
        send_email(subject, body)
