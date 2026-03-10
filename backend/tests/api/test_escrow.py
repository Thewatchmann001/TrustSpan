import pytest
from fastapi import status
from app.db.models import Investment, Startup, UserRole, User, WithdrawalRequest

@pytest.fixture
def test_startup(db):
    # Create founder
    founder = User(
        full_name="Founder User",
        email="founder@example.com",
        hashed_password="password",
        role=UserRole.STARTUP,
        company_name="Test Startup"
    )
    db.add(founder)
    db.commit()
    db.refresh(founder)

    # Create startup
    startup = Startup(
        founder_id=founder.id,
        startup_id="test_startup_id",
        name="Test Startup",
        sector="Technology",
        withdrawable_balance=0.0
    )
    db.add(startup)
    db.commit()
    db.refresh(startup)
    return startup

@pytest.fixture
def test_investment(db, client, test_user_data, test_startup):
    # Register investor
    client.post("/api/users/register", json=test_user_data)
    investor = db.query(User).filter(User.email == test_user_data["email"]).first()

    investment = Investment(
        startup_id=test_startup.id,
        investor_id=investor.id,
        amount=1000.0,
        escrow_balance=1000.0,
        released_amount=0.0,
        tx_signature="test_sig"
    )
    db.add(investment)
    db.commit()
    db.refresh(investment)
    return investment

def test_release_funds(client, test_user_data, test_investment, db):
    # Login investor
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    }
    login_resp = client.post("/api/users/login", json=login_data)
    token = login_resp.json()["access_token"]

    # Release funds
    release_data = {
        "investment_id": test_investment.id,
        "amount": 400.0
    }
    response = client.post(
        "/api/escrow/release",
        json=release_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["new_escrow_balance"] == 600.0

    # Check startup balance
    db.refresh(test_investment.startup)
    assert test_investment.startup.withdrawable_balance == 400.0

def test_create_withdrawal_request(client, db, test_startup, test_investment):
    # Release some funds first
    test_investment.escrow_balance -= 500.0
    test_investment.released_amount += 500.0
    test_startup.withdrawable_balance += 500.0
    db.commit()

    # Register founder
    reg_data = {
        "full_name": "Founder User 2",
        "email": "founder2@example.com",
        "password": "TestPassword123!",
        "role": "founder",
        "company_name": "Test Startup 2"
    }
    reg_resp = client.post("/api/users/register", json=reg_data)
    token = reg_resp.json()["access_token"]
    founder_id = reg_resp.json()["id"]

    # Update startup to this founder
    test_startup.founder_id = founder_id
    db.commit()

    # Create withdrawal request
    withdraw_data = {
        "startup_id": test_startup.id,
        "amount": 200.0,
        "reason": "Need to pay for servers"
    }
    response = client.post(
        "/api/escrow/withdraw-request",
        json=withdraw_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["amount"] == 200.0

    # Try to double-request (exceeding available)
    response2 = client.post(
        "/api/escrow/withdraw-request",
        json=withdraw_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    # Available was 500. 200 is pending. Now 300 available. 200 is requested. OK.
    assert response2.status_code == status.HTTP_201_CREATED

    # Third request should fail
    response3 = client.post(
        "/api/escrow/withdraw-request",
        json=withdraw_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    # 500 - 200 - 200 = 100 available. Requesting 200. Fail.
    assert response3.status_code == status.HTTP_400_BAD_REQUEST

def test_investor_reclaim_request(client, db, test_user_data, test_investment):
    # Login investor
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    }
    # Need to register first if not done by fixture
    client.post("/api/users/register", json=test_user_data)
    login_resp = client.post("/api/users/login", json=login_data)
    token = login_resp.json()["access_token"]

    # Create reclaim request
    reclaim_data = {
        "investment_id": test_investment.id,
        "amount": 300.0,
        "reason": "Need money back"
    }
    response = client.post(
        "/api/escrow/investor-withdraw-request",
        json=reclaim_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["request_type"] == "investor_reclaim"

    # Try to release funds that are pending reclaim
    # Escrow is 1000. 300 is pending reclaim. 700 available to release.
    release_data = {
        "investment_id": test_investment.id,
        "amount": 800.0
    }
    response_release = client.post(
        "/api/escrow/release",
        json=release_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response_release.status_code == status.HTTP_400_BAD_REQUEST

def test_admin_review_reclaim(client, db, test_startup, test_investment):
    # Create reclaim request
    request = WithdrawalRequest(
        investor_id=test_investment.investor_id,
        investment_id=test_investment.id,
        amount=100.0,
        reason="test",
        request_type="investor_reclaim",
        status="pending"
    )
    db.add(request)
    db.commit()

    # Register an admin
    reg_data = {
        "full_name": "Admin User",
        "email": "admin3@example.com",
        "password": "TestPassword123!",
        "role": "investor"
    }
    reg_resp = client.post("/api/users/register", json=reg_data)
    admin_id = reg_resp.json()["id"]
    admin_user = db.query(User).filter(User.id == admin_id).first()
    admin_user.role = UserRole.ADMIN
    db.commit()

    # Re-login admin
    login_resp = client.post("/api/users/login", json={"email": "admin3@example.com", "password": "TestPassword123!"})
    token = login_resp.json()["access_token"]

    # Review approved
    response = client.post(
        f"/api/escrow/admin/withdraw-requests/{request.id}/review",
        json={"status": "approved", "admin_feedback": "Approved"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_200_OK

    # Verify balance decrement
    db.refresh(test_investment)
    assert test_investment.escrow_balance == 900.0
    assert test_investment.amount == 900.0
