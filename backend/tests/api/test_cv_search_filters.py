import pytest
from app.db.models.user import User, UserRole
from app.db.models.cv import CV

def test_cv_search_filters(client, db):
    # 1. Create a mock employer
    employer_user = User(
        full_name="Employer User",
        email="employer@example.com",
        role=UserRole.EMPLOYER,
        wallet_address="EmployerWallet123"
    )
    db.add(employer_user)
    db.commit()

    # 2. Create a mock candidate with a CV
    candidate_user = User(
        full_name="Candidate User",
        email="candidate@example.com",
        role=UserRole.JOB_SEEKER,
        wallet_address="CandidateWallet123"
    )
    db.add(candidate_user)
    db.commit()

    cv = CV(
        user_id=candidate_user.id,
        personal_info={"full_name": "Candidate User", "location": "Freetown"},
        summary="Experienced Python developer",
        work_experience=[{"title": "Software Engineer", "company": "Tech Corp", "description": "Python development"}],
        education=[{"degree": "BSc Computer Science", "institution": "University of Sierra Leone"}],
        skills={"technical": ["Python", "FastAPI", "React"]},
        certifications=[{"name": "AWS Solutions Architect"}]
    )
    db.add(cv)
    db.commit()

    # Override current_user dependency for testing
    from app.core.dependencies import get_current_user
    app = client.app
    app.dependency_overrides[get_current_user] = lambda: employer_user

    # 3. Test search by skills
    response = client.post("/api/cv/search", json={
        "skills": ["Python"],
        "experience_level": "Junior"
    })
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert response.json()[0]["cv_id"] == cv.id

    # 4. Test search by education
    response = client.post("/api/cv/search", json={
        "education": "Computer Science",
        "experience_level": "Junior"
    })
    assert response.status_code == 200
    assert len(response.json()) > 0

    # 5. Test search by qualifications
    response = client.post("/api/cv/search", json={
        "qualifications": "AWS",
        "experience_level": "Junior"
    })
    assert response.status_code == 200
    assert len(response.json()) > 0

    # 6. Test search by job title
    response = client.post("/api/cv/search", json={
        "job_title": "Software Engineer",
        "experience_level": "Junior"
    })
    assert response.status_code == 200
    assert len(response.json()) > 0

    # 7. Test negative match (Should be empty due to stricter scoring/filtering)
    response = client.post("/api/cv/search", json={
        "skills": ["Haskell"],
        "education": "Medicine",
        "experience_level": "Senior"
    })
    assert response.status_code == 200
    # Our new logic filters out match_score < 30
    assert len(response.json()) == 0

    app.dependency_overrides.clear()
