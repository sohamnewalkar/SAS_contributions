import subprocess
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import socket
import time

# Function to execute system commands
def run_command(command):
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return '', str(e)

# Function to send email
def send_email(subject, body, recipient):
    try:
        # Setup the MIME
        msg = MIMEMultipart()
        msg['From'] = 'iaasopsnotifications@sas.com'
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Set up the SMTP server
        server = smtplib.SMTP('osmtp.vsp.sas.com', 25)
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.quit()
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")

# Main logic
def main():
    # Get the hostname
    hostname = socket.gethostname()

    # Check Squid service status
    status_output, _ = run_command(['systemctl', 'is-active', 'squid'])
    status = status_output.strip()

    if status != 'active':
        # Restart the Squid service
        _, _ = run_command(['systemctl', 'restart', 'squid.service'])
        time.sleep(20)

        # Parse Squid status and config
        config_parse_output, _ = run_command(['/usr/sbin/squid', 'status'])
        # config_test_output, _ = run_command(['squid', '-t'])  # Uncomment if you need this

        # Get the Squid service status after restart attempt
        squid_status_output, _ = run_command(['systemctl', 'status', 'squid.service'])
        squid_status = '\n'.join(squid_status_output.splitlines()[:3])

        # Final check for service status
        final_status_output, _ = run_command(['systemctl', 'is-active', 'squid'])
        final_status = final_status_output.strip()

        if final_status != 'active':
            # Prepare email for failed restart
            subject = "Squid Service Failure"
            body = f"""
            The Squid service on server {hostname} is not in an Active state.

            Squid Service Status:
            {squid_status}

            Latest Logs for Squid Service:
            {config_parse_output}

            Please address the Squid configuration issue as a priority.

            This is an automated notification configured for the host {hostname}.

            Regards,
            IaaS HostOps
            """
            send_email(subject, body, 'iaasopsnotifications@sas.com')

        else:
            # Prepare email for successful restart
            subject = "Squid Service Restarted Successfully"
            body = f"""
            The Squid service on server {hostname} had previously encountered a failure state but has now been successfully restarted.

            This is an automated notification configured for the host {hostname}.

            Regards,
            IaaS HostOps
            """
            send_email(subject, body, 'iaasopsnotifications@sas.com')

if __name__ == "__main__":
    main()
