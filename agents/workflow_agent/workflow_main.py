# agents/workflow_agent/workflow_main.py


class WorkflowAgent:
    """
    Manages workflows. Each workflow has:
      - A 'name'
      - A 'natural_language_prompt' that we pass to SQL/KG to check some condition
    """

    def __init__(self):
        # In-memory store: workflow_name -> prompt
        self.workflows = {}

    def parse_workflow_creation(self, user_text: str):
        """
        Parse user text like:
          'Create a workflow called low_quantity_check that checks if actual_quantity < allowed_range_min'
        Return (workflow_name, success_message) or raise an exception if not parseable.
        """
        # Example naive parse logic or a more sophisticated approach
        if "create a workflow called" not in user_text.lower():
            return None, "Could not parse workflow creation request."

        # Naive approach
        # e.g. "Create a workflow called low_quantity_check that checks if actual_quantity < allowed_range_min"
        parts = user_text.split("called")
        if len(parts) < 2:
            return None, "Could not parse name."
        after_called = parts[1].strip()
        first_space = after_called.find(" ")
        if first_space == -1:
            name = after_called
            prompt = "No prompt found."
        else:
            name = after_called[:first_space]
            rest = after_called[first_space:].strip()
            # rest might say "that checks if actual_quantity < allowed_range_min"
            # We'll store that entire chunk as the prompt
            prompt = rest

        # Store the workflow
        self.workflows[name] = prompt
        return name, f"Workflow '{name}' created successfully!"

    def get_prompt(self, workflow_name: str) -> str:
        """Return the stored natural-language prompt for the given workflow."""
        return self.workflows.get(workflow_name, "Workflow not found.")

    def notify_user(self, workflow_name: str, message: str) -> str:
        """In reality, might send an email or Slack. Here we just return a string."""
        return f"Notification for workflow '{workflow_name}': {message}"
