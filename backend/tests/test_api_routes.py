from app.main import app


def test_auth_and_course_routes_are_registered_under_api_prefix() -> None:
    paths = app.openapi()["paths"]

    assert "/api/v1/auth/teacher/login" in paths
    assert "/api/v1/courses" in paths
    assert "/api/v1/courses/manage" in paths
    assert "/api/v1/courses/{course_id}" in paths
    assert "/api/v1/courses/{course_id}/status" in paths
