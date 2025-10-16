from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from .models import Course, Enrollment, Assignment, Profile, Submission, Notification, Quiz, QuizAttempt
from rest_framework.authtoken.models import Token

class PermissionTests(APITestCase):
    def setUp(self):
        # Create a teacher user and their profile
        self.teacher_user = User.objects.create_user(username='teacher', password='password')
        self.teacher_profile = Profile.objects.create(user=self.teacher_user, role='TEACHER')
        self.teacher_token = Token.objects.get(user=self.teacher_user) # Get the token created by the signal

        # Create a student user and their profile
        self.student_user = User.objects.create_user(username='student', password='password')
        self.student_profile = Profile.objects.create(user=self.student_user, role='STUDENT')
        self.student_token = Token.objects.get(user=self.student_user)

        # Create another student user and their profile
        self.other_student_user = User.objects.create_user(username='otherstudent', password='password')
        self.other_student_profile = Profile.objects.create(user=self.other_student_user, role='STUDENT')
        self.other_student_token = Token.objects.get(user=self.other_student_user)

        # Create a course taught by the teacher
        self.course = Course.objects.create(name='Test Course', code='TC101', teacher=self.teacher_user)

        # Enroll the first student in the course
        Enrollment.objects.create(student=self.student_user, course=self.course)

        # Create an assignment for the course
        self.assignment = Assignment.objects.create(title='Test Assignment', due_date='2099-12-31T23:59:59Z', course=self.course)

    def test_teacher_can_create_course(self):
        """
        Ensure a user with the TEACHER role can create a course.
        """
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.teacher_token.key)
        url = reverse('course-create')
        data = {'name': 'New Course', 'code': 'NC101'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Course.objects.count(), 2)

    def test_student_cannot_create_course(self):
        """
        Ensure a user with the STUDENT role cannot create a course.
        """
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.student_token.key)
        url = reverse('course-create')
        data = {'name': 'Student Course', 'code': 'SC101'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Course.objects.count(), 1)

    def test_enrolled_student_can_view_assignments(self):
        """
        Ensure an enrolled student can see assignments for their course.
        """
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.student_token.key)
        url = reverse('assignment-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Assignment')

    def test_unenrolled_student_cannot_view_assignments(self):
        """
        Ensure a student who is not enrolled cannot see assignments for a course.
        """
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.other_student_token.key)
        url = reverse('assignment-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The list should be empty for this student
        self.assertEqual(len(response.data), 0)

class NotificationTests(APITestCase):
    def setUp(self):
        # Create teacher and student users
        self.teacher_user = User.objects.create_user(username='teacher2', password='password')
        Profile.objects.create(user=self.teacher_user, role='TEACHER')
        self.teacher_token = Token.objects.get(user=self.teacher_user)

        self.student_user = User.objects.create_user(username='student2', password='password')
        Profile.objects.create(user=self.student_user, role='STUDENT')
        self.student_token = Token.objects.get(user=self.student_user)

        # Create course and assignment
        self.course = Course.objects.create(name='Notify Course', code='NC102', teacher=self.teacher_user)
        self.assignment = Assignment.objects.create(title='Notify Assignment', due_date='2099-12-31T23:59:59Z', course=self.course)

        # Create a submission from the student for the assignment
        self.submission = Submission.objects.create(assignment=self.assignment, student=self.student_user, file='dummy.txt')

    def test_notification_created_on_grading(self):
        """
        Ensure a notification is created automatically when a submission is graded.
        """
        self.assertEqual(Notification.objects.count(), 0)
        # Grade the submission
        self.submission.grade = 95.5
        self.submission.save()

        # Check if the notification was created
        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.first()
        self.assertEqual(notification.recipient, self.student_user)
        self.assertIn('95.5', notification.message)
        self.assertIn('Notify Assignment', notification.message)

    def test_student_can_list_their_notifications(self):
        """
        Ensure a student can retrieve their own notifications.
        """
        # Create a notification manually for the test
        Notification.objects.create(recipient=self.student_user, message="Test notification")

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.student_token.key)
        url = reverse('notification-list')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['message'], "Test notification")

    def test_student_cannot_see_others_notifications(self):
        """
        Ensure a student cannot access notifications of another user.
        """
        # Create a notification for the teacher
        Notification.objects.create(recipient=self.teacher_user, message="Teacher's notification")

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.student_token.key)
        url = reverse('notification-list')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The list should be empty for the student
        self.assertEqual(len(response.data), 0)

    def test_student_can_mark_notification_as_read(self):
        """
        Ensure a student can mark their own notification as read.
        """
        notification = Notification.objects.create(recipient=self.student_user, message="Mark me as read")
        self.assertFalse(notification.is_read)

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.student_token.key)
        url = reverse('notification-read', kwargs={'pk': notification.pk})
        response = self.client.patch(url, format='json') # Using PATCH for partial update

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

class AnalyticsTests(APITestCase):
    def setUp(self):
        # Teacher 1
        self.teacher1 = User.objects.create_user(username='teacher_analytics', password='password')
        Profile.objects.create(user=self.teacher1, role='TEACHER')
        self.teacher1_token = Token.objects.get(user=self.teacher1)

        # Teacher 2
        self.teacher2 = User.objects.create_user(username='teacher_other', password='password')
        Profile.objects.create(user=self.teacher2, role='TEACHER')
        self.teacher2_token = Token.objects.get(user=self.teacher2)

        # Students
        self.student1 = User.objects.create_user(username='student_analytics1', password='password')
        Profile.objects.create(user=self.student1, role='STUDENT')
        self.student1_token = Token.objects.get(user=self.student1)
        self.student2 = User.objects.create_user(username='student_analytics2', password='password')
        Profile.objects.create(user=self.student2, role='STUDENT')

        # Course and Enrollment
        self.course = Course.objects.create(name='Analytics Course', code='AC101', teacher=self.teacher1)
        Enrollment.objects.create(student=self.student1, course=self.course)
        Enrollment.objects.create(student=self.student2, course=self.course)

        # Assignment and Submissions
        self.assignment = Assignment.objects.create(title='Analytics Assignment', due_date='2099-12-31T23:59:59Z', course=self.course)
        Submission.objects.create(assignment=self.assignment, student=self.student1, file='s1.txt', grade=80)
        # Student 2 did not submit

        # Quiz and Attempts
        self.quiz = Quiz.objects.create(title='Analytics Quiz', course=self.course, duration_minutes=10)
        QuizAttempt.objects.create(student=self.student1, quiz=self.quiz, score=90)
        QuizAttempt.objects.create(student=self.student2, quiz=self.quiz, score=70)

    def test_teacher_can_view_course_analytics(self):
        """
        Ensure the course teacher can access the analytics endpoint.
        """
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.teacher1_token.key)
        url = reverse('course-analytics', kwargs={'course_id': self.course.pk})
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['course_id'], self.course.pk)
        self.assertEqual(response.data['total_students'], 2)

        # Check assignment analytics
        self.assertEqual(len(response.data['assignments']), 1)
        self.assertEqual(response.data['assignments'][0]['average_grade'], 80.0)
        self.assertEqual(response.data['assignments'][0]['participation_percentage'], 50.0) # 1 out of 2 students submitted

        # Check quiz analytics
        self.assertEqual(len(response.data['quizzes']), 1)
        self.assertEqual(response.data['quizzes'][0]['average_score'], 80.0) # (90+70)/2

    def test_other_teacher_cannot_view_analytics(self):
        """
        Ensure a teacher cannot view analytics for a course they do not teach.
        """
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.teacher2_token.key)
        url = reverse('course-analytics', kwargs={'course_id': self.course.pk})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_view_analytics(self):
        """
        Ensure a student cannot view course analytics.
        """
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.student1_token.key)
        url = reverse('course-analytics', kwargs={'course_id': self.course.pk})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)