from django.urls import path
from .views import (
    RegisterView, LoginView, ProfileView, AssignmentListView, SubmissionCreateView,
    QuizListView, QuizDetailView, SubmitQuizView
)

urlpatterns = [
    # Auth
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),

    # Profile
    path('profile/', ProfileView.as_view(), name='profile'),

    # Assignments & Submissions
    path('assignments/', AssignmentListView.as_view(), name='assignment-list'),
    path('submissions/', SubmissionCreateView.as_view(), name='submission-create'),

    # Quizzes
    path('quizzes/', QuizListView.as_view(), name='quiz-list'),
    path('quizzes/<int:pk>/', QuizDetailView.as_view(), name='quiz-detail'),
    path('quizzes/<int:quiz_id>/submit/', SubmitQuizView.as_view(), name='quiz-submit'),
]