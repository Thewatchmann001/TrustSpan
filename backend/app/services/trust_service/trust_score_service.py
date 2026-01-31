"""
Trust Score Service - Calculates unified trust scores from trust signals.

Trust signals are derived/computed, not manually entered.
This service aggregates them into a unified trust score.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import User, TrustSignal, TrustSignalType, Credential, VerificationStatus
from app.utils.logger import logger


class TrustScoreService:
    """Service for calculating trust scores from trust signals."""

    def calculate_user_trust_score(
        self,
        db: Session,
        user_id: int,
    ) -> Dict[str, Any]:
        """
        Calculate unified trust score for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Dict with trust_score, signals_count, breakdown, and signals list
        """
        signals = (
            db.query(TrustSignal)
            .filter(TrustSignal.user_id == user_id)
            .order_by(TrustSignal.created_at.desc())
            .all()
        )

        if not signals:
            return {
                "trust_score": 0.0,
                "signals_count": 0,
                "breakdown": {},
                "signals": [],
                "confidence": "low",
            }

        # Weighted sum of trust signals
        # Each signal contributes up to 10 points, weighted by its weight
        weighted_score = sum(signal.weight * 10 for signal in signals)

        # Normalize to 0-100 (cap at 100)
        trust_score = min(100.0, weighted_score)

        # Breakdown by signal type
        breakdown = {}
        for signal in signals:
            signal_type = signal.signal_type.value
            if signal_type not in breakdown:
                breakdown[signal_type] = {"count": 0, "total_weight": 0.0, "signals": []}
            breakdown[signal_type]["count"] += 1
            breakdown[signal_type]["total_weight"] += signal.weight
            breakdown[signal_type]["signals"].append(
                {
                    "id": signal.id,
                    "weight": signal.weight,
                    "source": signal.source,
                    "created_at": signal.created_at.isoformat(),
                }
            )

        # Calculate confidence level
        confidence = self._calculate_confidence(signals, trust_score)

        return {
            "trust_score": round(trust_score, 2),
            "signals_count": len(signals),
            "breakdown": breakdown,
            "confidence": confidence,
            "signals": [
                {
                    "id": s.id,
                    "type": s.signal_type.value,
                    "weight": s.weight,
                    "source": s.source,
                    "created_at": s.created_at.isoformat(),
                    "credential_id": s.credential_id,
                }
                for s in signals
            ],
        }

    def _calculate_confidence(
        self,
        signals: List[TrustSignal],
        trust_score: float,
    ) -> str:
        """Calculate confidence level based on signals and score."""
        if trust_score >= 80 and len(signals) >= 3:
            return "high"
        elif trust_score >= 50 and len(signals) >= 2:
            return "medium"
        elif trust_score > 0:
            return "low"
        else:
            return "none"

    def get_user_trust_summary(
        self,
        db: Session,
        user_id: int,
    ) -> Dict[str, Any]:
        """
        Get a summary of user's trust profile.

        Includes:
        - Trust score
        - Verified credentials count
        - Trust signal breakdown
        - Verification rate
        """
        trust_data = self.calculate_user_trust_score(db, user_id)

        # Get verified credentials count
        verified_creds = (
            db.query(Credential)
            .filter(
                Credential.user_id == user_id,
                Credential.verification_status == VerificationStatus.VERIFIED,
            )
            .count()
        )

        total_creds = (
            db.query(Credential).filter(Credential.user_id == user_id).count()
        )

        return {
            **trust_data,
            "verified_credentials_count": verified_creds,
            "total_credentials_count": total_creds,
            "verification_rate": (
                (verified_creds / total_creds * 100) if total_creds > 0 else 0.0
            ),
        }

    def get_trust_leaderboard(
        self,
        db: Session,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get users with highest trust scores.

        Args:
            db: Database session
            limit: Number of users to return

        Returns:
            List of user trust summaries, sorted by trust score
        """
        # Get all users with trust signals
        users_with_signals = (
            db.query(User.id, User.full_name, User.email)
            .join(TrustSignal)
            .distinct()
            .all()
        )

        leaderboard = []
        for user_id, full_name, email in users_with_signals:
            trust_data = self.calculate_user_trust_score(db, user_id)
            leaderboard.append(
                {
                    "user_id": user_id,
                    "full_name": full_name,
                    "email": email,
                    **trust_data,
                }
            )

        # Sort by trust score descending
        leaderboard.sort(key=lambda x: x["trust_score"], reverse=True)

        return leaderboard[:limit]

    def calculate_startup_team_trust_score(
        self,
        db: Session,
        startup_id: int,
    ) -> Dict[str, Any]:
        """
        Calculate aggregate trust score for a startup team.

        Args:
            db: Database session
            startup_id: Startup ID

        Returns:
            Team trust score and breakdown
        """
        from app.db.models import Startup, Employee

        startup = db.query(Startup).filter(Startup.id == startup_id).first()
        if not startup:
            return {"team_trust_score": 0.0, "team_members": []}

        # Get founder trust score
        founder_trust = self.calculate_user_trust_score(db, startup.founder_id)

        # Get employee trust scores
        employees = (
            db.query(Employee).filter(Employee.startup_id == startup_id).all()
        )
        employee_trust_scores = []
        for emp in employees:
            emp_trust = self.calculate_user_trust_score(db, emp.user_id)
            employee_trust_scores.append(
                {
                    "user_id": emp.user_id,
                    "role": emp.role,
                    "trust_score": emp_trust["trust_score"],
                }
            )

        # Calculate team average
        all_scores = [founder_trust["trust_score"]] + [
            e["trust_score"] for e in employee_trust_scores
        ]
        team_trust_score = sum(all_scores) / len(all_scores) if all_scores else 0.0

        return {
            "team_trust_score": round(team_trust_score, 2),
            "founder_trust_score": founder_trust["trust_score"],
            "team_members": [
                {
                    "user_id": startup.founder_id,
                    "role": "Founder",
                    "trust_score": founder_trust["trust_score"],
                }
            ]
            + employee_trust_scores,
        }
