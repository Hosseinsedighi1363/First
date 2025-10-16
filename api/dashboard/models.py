from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

# Automatically create a token for every new user
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

class Profile(models.Model):
    """
    Extends the default User model to store student-specific information.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return self.user.username

class Course(models.Model):
    """
    Represents a course or subject.
    """
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    # Assuming the teacher is also a user in the system
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='taught_courses')

    def __str__(self):
        return self.name

class Assignment(models.Model):
    """
    Represents an assignment for a specific course.
    """
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    due_date = models.DateTimeField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')

    def __str__(self):
        return self.title

class Submission(models.Model):
    """
    Represents a student's submission for an assignment.
    """
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    submitted_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='submissions/')
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        # A student can only submit once for each assignment
        unique_together = ('assignment', 'student')

    def __str__(self):
        return f'{self.student.username} - {self.assignment.title}'

class Quiz(models.Model):
    """
    Represents a quiz for a specific course.
    """
    title = models.CharField(max_length=255)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    duration_minutes = models.PositiveIntegerField(help_text="Duration of the quiz in minutes")

    def __str__(self):
        return self.title

class Question(models.Model):
    """
    Represents a single question in a quiz.
    """
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()

    def __str__(self):
        return self.text[:50] # Return first 50 chars of question

class Choice(models.Model):
    """
    Represents a choice for a multiple-choice question.
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

class QuizAttempt(models.Model):
    """
    Records a student's attempt at a quiz.
    """
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    score = models.FloatField()
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.student.username} attempts {self.quiz.title}'

class Answer(models.Model):
    """
    Records a student's selected answer for a question in an attempt.
    """
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, on_delete=models.CASCADE)

    def __str__(self):
        return f'Answer to "{self.question.text[:30]}..." in attempt {self.attempt.id}'