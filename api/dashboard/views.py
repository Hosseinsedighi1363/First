from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import generics, status, permissions
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from .models import Profile, Assignment, Submission, Quiz, Question, Choice, QuizAttempt, Answer
from .serializers import (
    UserSerializer, ProfileSerializer, AssignmentSerializer, SubmissionSerializer,
    QuizSerializer, QuizDetailSerializer, SubmitQuizSerializer, CourseSerializer,
    NotificationSerializer
)
from .permissions import IsTeacher, IsStudent, IsProfileOwner, IsEnrolledOrTeacher, IsCourseTeacher
from .models import Course, Notification, Assignment, Quiz
from django.db.models import Avg, Count
from drf_spectacular.utils import extend_schema

@extend_schema(
    summary="Register a new user",
    description="Create a new user account. A profile and an authentication token will be created automatically."
)
class RegisterView(generics.CreateAPIView):
    """
    API endpoint for user registration.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        user = serializer.instance
        token, created = Token.objects.get_or_create(user=user)
        headers = self.get_success_headers(serializer.data)
        return Response({'token': token.key, 'user_id': user.id, 'username': user.username}, status=status.HTTP_201_CREATED, headers=headers)

@extend_schema(summary="Login a user", description="Authenticate a user and receive an auth token.")
class LoginView(ObtainAuthToken):
    """
    API endpoint for user login. Returns auth token.
    """
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email
        })

@extend_schema(summary="Retrieve or update user profile", description="Allows users to view or edit their own profile.")
@method_decorator(cache_page(60 * 10), name='get') # Cache GET requests for 10 minutes
class ProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for retrieving and updating user profile.
    """
    queryset = Profile.objects.select_related('user').all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsProfileOwner]

    def get_object(self):
        # Return the profile of the currently logged-in user
        return self.request.user.profile

@extend_schema(summary="Create a new course (Teachers only)", description="Allows users with the 'TEACHER' role to create a new course.")
class CourseCreateView(generics.CreateAPIView):
    """
    API endpoint for teachers to create new courses.
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer # We need to create this
    permission_classes = [permissions.IsAuthenticated, IsTeacher]

    def perform_create(self, serializer):
        # Set the current user as the teacher of the course
        serializer.save(teacher=self.request.user)

@extend_schema(summary="List assignments", description="Lists assignments for the courses the user is enrolled in (for students) or teaches (for teachers).")
@method_decorator(cache_page(60 * 5), name='get') # Cache for 5 minutes
class AssignmentListView(generics.ListAPIView):
    """
    API endpoint to list all assignments for the current user's enrolled courses.
    """
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.profile.role == 'STUDENT':
            # Students see assignments for their enrolled courses
            enrolled_courses = user.enrolled_courses.all()
            return Assignment.objects.filter(course__in=enrolled_courses).select_related('course')
        elif user.profile.role == 'TEACHER':
            # Teachers see assignments for the courses they teach
            return Assignment.objects.filter(course__teacher=user).select_related('course')
        return Assignment.objects.none()

@extend_schema(summary="Submit an assignment (Students only)", description="Allows students to upload a file as a submission for an assignment.")
class SubmissionCreateView(generics.CreateAPIView):
    """
    API endpoint for submitting a file for an assignment. Only for students.
    """
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def perform_create(self, serializer):
        # Associate the submission with the current user
        serializer.save(student=self.request.user)

@extend_schema(summary="List quizzes", description="Lists quizzes for the courses the user is enrolled in (for students) or teaches (for teachers).")
@method_decorator(cache_page(60 * 5), name='get') # Cache for 5 minutes
class QuizListView(generics.ListAPIView):
    """
    API endpoint to list all available quizzes for the user.
    """
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.profile.role == 'STUDENT':
            enrolled_courses = user.enrolled_courses.all()
            return Quiz.objects.filter(course__in=enrolled_courses).select_related('course')
        elif user.profile.role == 'TEACHER':
            return Quiz.objects.filter(course__teacher=user).select_related('course')
        return Quiz.objects.none()

@extend_schema(summary="Retrieve a quiz", description="Gets the details of a specific quiz, including its questions and choices. Access is restricted to enrolled students or the course teacher.")
@method_decorator(cache_page(60 * 10), name='get') # Cache for 10 minutes
class QuizDetailView(generics.RetrieveAPIView):
    """
    API endpoint to retrieve the details of a single quiz.
    Access is restricted to enrolled students or the teacher.
    """
    queryset = Quiz.objects.prefetch_related('questions__choices').all()
    serializer_class = QuizDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsEnrolledOrTeacher]

@extend_schema(summary="Submit a quiz (Students only)", description="Allows a student to submit their answers for a quiz and receive their score immediately.")
class SubmitQuizView(APIView):
    """
    API endpoint to submit answers for a quiz. Only for students.
    """
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def post(self, request, quiz_id, *args, **kwargs):
        serializer = SubmitQuizSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            quiz = Quiz.objects.get(pk=quiz_id)
        except Quiz.DoesNotExist:
            return Response({'error': 'Quiz not found.'}, status=status.HTTP_404_NOT_FOUND)

        answers_data = serializer.validated_data['answers']
        correct_answers = 0
        total_questions = quiz.questions.count()

        with transaction.atomic():
            # Create a QuizAttempt record
            attempt = QuizAttempt.objects.create(student=request.user, quiz=quiz, score=0)

            for answer_data in answers_data:
                question = Question.objects.get(pk=answer_data['question_id'])
                selected_choice = Choice.objects.get(pk=answer_data['choice_id'])

                # Save the user's answer
                Answer.objects.create(
                    attempt=attempt,
                    question=question,
                    selected_choice=selected_choice
                )

                if selected_choice.is_correct:
                    correct_answers += 1

            # Calculate and save the final score
            score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
            attempt.score = score
            attempt.save()

        return Response({
            'message': 'Quiz submitted successfully!',
            'score': attempt.score,
            'correct_answers': correct_answers,
            'total_questions': total_questions
        }, status=status.HTTP_200_OK)

@extend_schema(summary="List user notifications", description="Retrieves a list of all notifications for the currently logged-in user.")
@method_decorator(cache_page(60 * 2), name='get') # Cache for 2 minutes
class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.notifications.select_related('recipient').all()

@extend_schema(summary="Mark a notification as read", description="Marks a specific notification as read.")
class MarkNotificationAsReadView(generics.UpdateAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Ensure users can only affect their own notifications
        return self.request.user.notifications.all()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_read = True
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

@extend_schema(
    summary="Get course analytics (Teacher only)",
    description="Retrieves detailed analytics for a specific course, including student count, assignment participation, and average grades. Access is restricted to the teacher of the course."
)
class CourseAnalyticsView(APIView):
    """
    Provides analytics for a specific course. Only accessible by the course teacher.
    """
    permission_classes = [permissions.IsAuthenticated, IsCourseTeacher]

    def get(self, request, course_id, *args, **kwargs):
        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return Response({'error': 'Course not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Check object-level permissions
        self.check_object_permissions(request, course)

        total_students = course.students.count()

        # Assignment analytics
        assignment_analytics = []
        for assignment in course.assignments.all():
            submissions = assignment.submissions
            participation_count = submissions.count()
            participation_percentage = (participation_count / total_students) * 100 if total_students > 0 else 0
            average_grade = submissions.aggregate(avg_grade=Avg('grade'))['avg_grade']

            assignment_analytics.append({
                'assignment_id': assignment.id,
                'title': assignment.title,
                'average_grade': average_grade or 0,
                'participation_percentage': round(participation_percentage, 2)
            })

        # Quiz analytics
        quiz_analytics = []
        for quiz in course.quizzes.all():
            attempts = quiz.attempts
            average_score = attempts.aggregate(avg_score=Avg('score'))['avg_score']

            quiz_analytics.append({
                'quiz_id': quiz.id,
                'title': quiz.title,
                'average_score': average_score or 0
            })

        analytics_data = {
            'course_id': course.id,
            'course_name': course.name,
            'total_students': total_students,
            'assignments': assignment_analytics,
            'quizzes': quiz_analytics
        }

        return Response(analytics_data, status=status.HTTP_200_OK)