from rest_framework import permissions

class IsTeacher(permissions.BasePermission):
    """
    Allows access only to users with the 'TEACHER' role.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.profile.role == 'TEACHER'

class IsStudent(permissions.BasePermission):
    """
    Allows access only to users with the 'STUDENT' role.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.profile.role == 'STUDENT'

class IsProfileOwner(permissions.BasePermission):
    """
    Allows a user to edit their own profile only.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed to the owner of the profile.
        return obj.user == request.user

class IsEnrolledOrTeacher(permissions.BasePermission):
    """
    - Teachers of a course have full access.
    - Enrolled students have read-only access to course content (e.g., assignments).
    """
    def has_object_permission(self, request, view, obj):
        # obj is the course, assignment, or quiz object
        course = None
        if hasattr(obj, 'course'): # This handles Assignments and Quizzes
            course = obj.course
        elif hasattr(obj, 'name'): # This handles the Course object itself
            course = obj
        else:
            return False # Should not happen if applied correctly

        if not request.user or not request.user.is_authenticated:
            return False

        # Teacher of the course has full access
        if course.teacher == request.user:
            return True

        # Enrolled students have access
        is_enrolled = course.students.filter(pk=request.user.pk).exists()

        # For safe methods (GET, HEAD, OPTIONS), enrolled students are allowed
        if request.method in permissions.SAFE_METHODS and is_enrolled:
            return True

        return False