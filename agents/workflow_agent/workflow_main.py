import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

CUR_DIR = os.path.dirname(os.path.abspath(__file__))


class WorkflowAgent:
    """
    Manages workflows. Each workflow has:
      - A 'name'
      - A 'natural_language_prompt' that we pass to Q&A Agents to check some condition

    Usage:
      - To create a workflow, provide a string in the format:
        "create a workflow called <workflow_name> that <condition/purpose>"
        Example:
          "Create a workflow called low_quantity_check that checks if actual_quantity < allowed_range_min"

      - To fetch the natural language prompt for a workflow:
        Use the `get_prompt(workflow_name)` method with the name of the workflow.

      - To send a notification:
        Use the `notify_user(workflow_name, message, recipient)` method with the workflow name, the message,
        and optionally a recipient email address.

      Note:
        - All workflows persist across sessions and are saved in a file (default: `workflows.json`).
        - Duplicate workflows are not allowed.
    """

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        email_user: str,
        email_password: str,
        default_recipient: str,
        workflows_save_file: str = os.path.join(CUR_DIR, "workflows.json"),
    ):
        """
        Initialize the WorkflowAgent with SMTP settings and persistence logic.

        Args:
          smtp_server (str): SMTP server address (e.g., "smtp.gmail.com")
          smtp_port (int): SMTP port (e.g., 587)
          email_user (str): Email address for sending notifications
          email_password (str): Password or app password for the email account
          default_recipient (str): Default email address for receiving notifications
          workflows_save_file (str): File path to save and load workflows
        """
        self.workflows = {}
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_user = email_user
        self.email_password = email_password
        self.default_recipient = default_recipient
        self.workflows_save_file = workflows_save_file

        self._load_workflows()

    def _load_workflows(self):
        """Load workflows from the persistence file."""
        if os.path.exists(self.workflows_save_file):
            try:
                with open(self.workflows_save_file, "r") as file:
                    self.workflows = json.load(file)
            except Exception as e:
                print(f"Failed to load workflows: {e}")
        else:
            self.workflows = {}

    def _save_workflows(self):
        """Save workflows to the persistence file."""
        try:
            with open(self.workflows_save_file, "w") as file:
                json.dump(self.workflows, file, indent=4)
        except Exception as e:
            print(f"Failed to save workflows: {e}")

    def parse_workflow_creation(self, user_text: str):
        """
        Parse user text to create a workflow.

        Args:
          user_text (str): Natural language description of the workflow

        Returns:
          tuple: (workflow_name, success_message)
        """
        if "create a workflow called" not in user_text.lower():
            return None, "Could not parse workflow creation request."

        parts = user_text.split("called")
        if len(parts) < 2:
            return None, "Could not parse workflow creation request."

        after_called = parts[1].strip()

        # Extract workflow name and remaining details
        first_space = after_called.find(" ")
        if first_space == -1:
            name = after_called
            prompt = "No prompt found."
            email_list = []
        else:
            name = after_called[:first_space]
            rest = after_called[first_space:].strip()

            # Extract email list if present
            if "with email list" in rest:
                email_split = rest.split("with email list")
                prompt = email_split[0].strip()
                email_list = [
                    email.strip().strip("[]'\"")  # Clean up brackets and quotes
                    for email in email_split[1].strip().split(",")
                    if email.strip()
                ]
            else:
                prompt = rest
                email_list = []

        if name in self.workflows:
            return None, f"Workflow '{name}' already exists."

        # Store the workflow details
        self.workflows[name] = {
            "prompt": prompt,
            "email_list": email_list,
        }
        self._save_workflows()

        success_message = f"Workflow '{name}' created successfully!"
        if email_list:
            success_message += (
                f" Notifications will be sent to: {', '.join(email_list)}."
            )

        return name, success_message

    def get_prompt(self, workflow_name: str) -> str:
        """Return the stored natural-language prompt for the given workflow."""
        workflow = self.workflows.get(workflow_name)
        if not workflow:
            return f"Workflow not found."
        return workflow.get("prompt", "Workflow not found.")

    def notify_user(
        self, workflow_name: str, message: str, recipient: Optional[str] = None
    ) -> str:
        """
        Send email notifications for the workflow.

        Args:
          workflow_name (str): Name of the workflow
          message (str): Notification message
          recipient (Optional[str]): Email address of the recipient

        Returns:
          str: Confirmation message
        """
        workflow = self.workflows.get(workflow_name)
        if not workflow:
            return f"Workflow '{workflow_name}' not found."

        # Use recipient or fallback to email list from workflow
        email_list = workflow.get("email_list", [])
        if not email_list:
            return f"No email addresses configured for workflow '{workflow_name}'."

        success_count = 0
        failure_count = 0
        failed_recipients = []

        for recipient_email in email_list:
            try:
                msg = MIMEMultipart()
                msg["From"] = self.email_user
                msg["To"] = recipient_email
                msg["Subject"] = f"Notification for Workflow '{workflow_name}'"

                body = f"Workflow: {workflow_name}\n\nMessage:\n{message}"
                msg.attach(MIMEText(body, "plain"))

                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(self.email_user, self.email_password)
                    server.sendmail(self.email_user, recipient_email, msg.as_string())

                success_count += 1
            except Exception as e:
                failure_count += 1
                failed_recipients.append(f"{recipient_email}: {e}")

        response_message = f"Notifications sent to {success_count} recipients for workflow '{workflow_name}'."
        print(f"Notifications sent to {success_count} recipients for workflow '{workflow_name}'.")
        if failure_count > 0:
            response_message += f" Failed to send to {failure_count} recipients: {', '.join(failed_recipients)}."

        return response_message
