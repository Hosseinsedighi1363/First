from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from .models import Profile, Assignment, Submission, Quiz, Question, Choice, QuizAttempt, Answer
from .serializers import (
    UserSerializer, ProfileSerializer, AssignmentSerializer, SubmissionSerializer,
    QuizSerializer, QuizDetailSerializer, SubmitQuizSerializer
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

class ProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for retrieving and updating user profile.
    """
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Return the profile of the currently logged-in user
        return self.request.user.profile

class AssignmentListView(generics.ListAPIView):
    """
    API endpoint to list all assignments for the current user.
    """
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # This is a simplified example. In a real app, you'd filter assignments
        # based on the courses the user is enrolled in.
        return Assignment.objects.all()

class SubmissionCreateView(generics.CreateAPIView):
    """
    API endpoint for submitting a file for an assignment.
    """
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Associate the submission with the current user
        serializer.save(student=self.request.user)

class QuizListView(generics.ListAPIView):
    """
    API endpoint to list all available quizzes.
    """
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]

class QuizDetailView(generics.RetrieveAPIView):
    """
    API endpoint to retrieve the details of a single quiz, including questions and choices.
    """
    queryset = Quiz.objects.all()
    serializer_class = QuizDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

class SubmitQuizView(APIView):
    """
    API endpoint to submit answers for a quiz and get the result.
    """
    permission_classes = [permissions.IsAuthenticated]

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