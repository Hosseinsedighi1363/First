from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Submission, Notification

@receiver(post_save, sender=Submission)
def create_grade_notification(sender, instance, created, **kwargs):
    """
    Create a notification when an assignment submission is graded.
    The signal fires when the `grade` field is populated.
    """
    # Check if the grade exists and was just added or changed
    if instance.grade is not None:
        # We can check if a notification for this specific grading action already exists
        # to avoid duplicate notifications, but for now, we'll keep it simple.

        message = f'نمره شما برای تکلیف "{instance.assignment.title}" ثبت شد: {instance.grade}'

        # Create the notification for the student
        Notification.objects.create(
            recipient=instance.student,
            message=message
        )