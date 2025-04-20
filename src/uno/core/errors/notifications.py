from typing import Dict, Any, List, Callable
from datetime import datetime, timedelta
from uno.core.errors.framework import FrameworkError
from uno.core.errors.monitoring import error_aggregator

class NotificationRule:
    """Class for defining notification rules."""
    
    def __init__(
        self,
        name: str,
        condition: Callable[[FrameworkError], bool],
        threshold: int = 1,
        timeframe: timedelta = timedelta(minutes=5),
        notification_channels: List[str] = ["slack", "email"]
    ):
        self.name = name
        self.condition = condition
        self.threshold = threshold
        self.timeframe = timeframe
        self.notification_channels = notification_channels
        self.last_notification: Optional[datetime] = None
        self.error_count = 0
        
    def should_notify(self, error: FrameworkError) -> bool:
        """Check if notification should be sent for this error."""
        if not self.condition(error):
            return False
            
        self.error_count += 1
        
        # Reset count if timeframe has passed
        if self.last_notification and \
           datetime.utcnow() - self.last_notification > self.timeframe:
            self.error_count = 1
            
        # Check if threshold is met
        if self.error_count >= self.threshold:
            self.last_notification = datetime.utcnow()
            self.error_count = 0
            return True
            
        return False

class ErrorNotifier:
    """Class for handling error notifications."""
    
    def __init__(self):
        self.rules: List[NotificationRule] = []
        
    def add_rule(self, rule: NotificationRule) -> None:
        """Add a notification rule."""
        self.rules.append(rule)
        
    def notify(self, error: FrameworkError, context: Dict[str, Any]) -> None:
        """Send notifications based on rules."""
        for rule in self.rules:
            if rule.should_notify(error):
                self._send_notifications(
                    rule.notification_channels,
                    error,
                    context,
                    rule.name
                )
                
    def _send_notifications(
        self,
        channels: List[str],
        error: FrameworkError,
        context: Dict[str, Any],
        rule_name: str
    ) -> None:
        """Send notifications to specified channels."""
        message = self._create_notification_message(error, context, rule_name)
        
        for channel in channels:
            if channel == "slack":
                self._send_slack_notification(message)
            elif channel == "email":
                self._send_email_notification(message)
            # Add more channels as needed
                
    def _create_notification_message(
        self,
        error: FrameworkError,
        context: Dict[str, Any],
        rule_name: str
    ) -> Dict[str, Any]:
        """Create notification message content."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "rule": rule_name,
            "error_code": error.code,
            "error_message": error.message,
            "severity": error.severity.value,
            "category": error.category.value,
            "context": context
        }
        
    def _send_slack_notification(self, message: Dict[str, Any]) -> None:
        """Send notification to Slack."""
        # TODO: Implement Slack notification
        pass
        
    def _send_email_notification(self, message: Dict[str, Any]) -> None:
        """Send notification via email."""
        # TODO: Implement email notification
        pass

# Create singleton instance
error_notifier = ErrorNotifier()
