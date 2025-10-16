from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from .models import Course, Enrollment, Assignment, Profile
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