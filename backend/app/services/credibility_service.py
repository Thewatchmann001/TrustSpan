from typing import Dict, Any
from sqlalchemy.orm import Session
from app.db.models import Startup, Investment, User, Attestation
from app.utils.logger import logger


class CredibilityService:
    """Service for calculating startup credibility scores with multiple verification paths."""
    
    def calculate_startup_credibility(
        self,
        db: Session,
        startup_id: int
    ) -> Dict[str, Any]:
        """
        Calculate credibility score for a startup based on multiple verification paths:
        - Team Credibility (25 points max): Verified employees + founder experience
        - Business Legitimacy (25 points max): Document verification + business registration
        - Product Traction (25 points max): MVP status + user base + revenue
        - Investment Traction (15 points max): Investor backing
        - On-Chain Verification (10 points): Blockchain registration (optional bonus)
        - Attestation Verification (35 points max): Identity (10) + Business (15) + Both Bonus (5) + On-Chain Bonus (5)
        
        Total: 100+ points possible (capped at 100, but attestations can push above)
        """
        logger.info(f"Calculating credibility for startup {startup_id}")
        
        startup = db.query(Startup).filter(Startup.id == startup_id).first()
        if not startup:
            return {"credibility_score": 0.0, "factors": {}}
        
        factors = {}
        score = 0.0
        
        # ===== FACTOR 1: TEAM CREDIBILITY (25 points max) =====
        team_score = 0.0
        
        # Verified employees (15 points max)
        employees_verified = startup.employees_verified or 0
        employee_points = min(15, employees_verified * 3)  # 3 points per employee (up to 5)
        team_score += employee_points
        
        # Founder experience (10 points max) - Now uses credentials (single source of truth)
        founder = db.query(User).filter(User.id == startup.founder_id).first()
        
        # Get founder's verified credentials
        from app.services.trust_service import CredentialService, TrustScoreService
        from app.db.models import CredentialType, VerificationStatus
        
        credential_service = CredentialService()
        trust_service = TrustScoreService()
        
        # Get founder's verified credentials
        founder_creds = credential_service.get_user_credentials(
            db, startup.founder_id, verification_status=VerificationStatus.VERIFIED
        )
        
        # Get founder's trust score
        founder_trust = trust_service.calculate_user_trust_score(db, startup.founder_id)
        
        # Calculate founder points based on verified credentials
        # Multiple paths to earn founder points:
        # 1. High trust score (80+) with verified credentials (10 points)
        # 2. Verified education + verified employment (10 points)
        # 3. Verified education OR verified employment (7 points)
        # 4. On-chain verified founder (10 points)
        # 5. Founder with 5+ years experience (8 points)
        # 6. Founder with 3-5 years experience (5 points)
        # 7. Founder profile verified (3 points)
        founder_points = 0
        
        verified_education = [c for c in founder_creds if c.type == CredentialType.EDUCATION]
        verified_employment = [c for c in founder_creds if c.type == CredentialType.EMPLOYMENT]
        verified_startup_roles = [c for c in founder_creds if c.type == CredentialType.STARTUP_ROLE]
        
        if founder and founder.verified_on_chain == "verified":
            founder_points = 10
        elif founder_trust["trust_score"] >= 80 and len(founder_creds) >= 2:
            founder_points = 10
        elif len(verified_education) > 0 and len(verified_employment) > 0:
            founder_points = 10
        elif len(verified_education) > 0 or len(verified_employment) > 0:
            founder_points = 7
        elif startup.founder_experience_years and startup.founder_experience_years >= 5:
            founder_points = 8
        elif startup.founder_experience_years and startup.founder_experience_years >= 3:
            founder_points = 5
        elif startup.founder_profile_verified:
            founder_points = 3
        elif len(verified_startup_roles) > 0:
            founder_points = 3  # At least has startup role credential
        
        team_score += founder_points
        
        factors["team_credibility"] = {
            "verified_employees": employees_verified,
            "employee_points": employee_points,
            "founder_experience_years": startup.founder_experience_years or 0,
            "founder_profile_verified": startup.founder_profile_verified,
            "founder_points": founder_points,
            "founder_trust_score": founder_trust.get("trust_score", 0.0),
            "founder_verified_credentials": len(founder_creds),
            "total": team_score
        }
        score += team_score
        
        # ===== FACTOR 2: BUSINESS LEGITIMACY (25 points max) =====
        legitimacy_score = 0.0
        
        # Business registration verification (10 points)
        if startup.business_registration_verified:
            legitimacy_score += 10
        
        # Company website & contact info (15 points)
        if startup.website and startup.contact_email and startup.address:
            legitimacy_score += 15
        
        factors["business_legitimacy"] = {
            "business_registration_verified": startup.business_registration_verified,
            "has_website_contact_address": (
                bool(startup.website) and 
                bool(startup.contact_email) and 
                bool(startup.address)
            ),
            "documents_verified": bool(startup.documents_url),
            "total": legitimacy_score
        }
        score += legitimacy_score
        
        # ===== FACTOR 3: PRODUCT TRACTION (25 points max) =====
        traction_score = 0.0
        
        # MVP/Product status (10 points)
        if startup.has_mvp:
            traction_score += 10
        
        # User base (10 points max)
        user_base = startup.user_base_count or 0
        user_points = 0
        if user_base > 0:
            # 10 points for 100+ users, scales linearly
            user_points = min(10, (user_base / 100) * 10)
            traction_score += user_points
        
        # Revenue/Monetization (5 points max)
        monthly_revenue = startup.monthly_revenue or 0.0
        revenue_points = 0
        if monthly_revenue > 0:
            # 5 points for 1000+ USDC/month
            revenue_points = min(5, (monthly_revenue / 1000) * 5)
            traction_score += revenue_points
        
        factors["product_traction"] = {
            "has_mvp": startup.has_mvp,
            "mvp_points": 10 if startup.has_mvp else 0,
            "user_base_count": user_base,
            "user_points": user_points,
            "monthly_revenue": monthly_revenue,
            "revenue_points": revenue_points,
            "total": traction_score
        }
        score += traction_score
        
        # ===== FACTOR 4: INVESTMENT TRACTION (15 points max) =====
        investments = db.query(Investment).filter(
            Investment.startup_id == startup_id
        ).all()
        total_investment = sum(inv.amount for inv in investments)
        
        # Scale: 15 points for 50k USDC
        investment_score = min(15, (total_investment / 50000) * 15)
        
        factors["investment_traction"] = {
            "total_investments": len(investments),
            "total_amount": total_investment,
            "score": investment_score
        }
        score += investment_score
        
        # ===== FACTOR 5: ON-CHAIN VERIFICATION (10 points - BONUS) =====
        on_chain_score = 0
        if startup.transaction_signature:
            on_chain_score = 10
        
        factors["on_chain_legitimacy"] = {
            "registered_on_chain": startup.transaction_signature is not None,
            "score": on_chain_score
        }
        score += on_chain_score
        
        # ===== FACTOR 6: ATTESTATION VERIFICATION (10 points - BONUS) =====
        attestation_score = 0.0
        attestation_details = {}
        
        # Check for attestations
        try:
            founder_attestations = db.query(Attestation).filter(
                Attestation.user_id == startup.founder_id,
                Attestation.status == "verified"
            ).all()
            
            logger.info(f"Found {len(founder_attestations)} verified attestations for founder {startup.founder_id}")
            for att in founder_attestations:
                logger.info(f"  - Schema: {att.schema}, Status: {att.status}, On-chain: {att.on_chain}")
            
            # Business ownership attestation (15 points - significant trust signal)
            has_business_attestation = any(
                att.schema == "business_ownership" and att.status == "verified"
                for att in founder_attestations
            )
            if has_business_attestation:
                attestation_score += 15
                attestation_details["business_attestation"] = True
                logger.info(f"Business attestation found: +15 points")
            
            # Identity/KYC attestation (10 points - important trust signal)
            # Check for both "identity" and "kyc_identity" schemas for compatibility
            has_identity_attestation = any(
                (att.schema == "identity" or att.schema == "kyc_identity") and att.status == "verified"
                for att in founder_attestations
            )
            if has_identity_attestation:
                attestation_score += 10
                attestation_details["identity_attestation"] = True
                logger.info(f"Identity attestation found: +10 points")
            
            # Bonus for having BOTH identity AND business verified (5 points)
            if has_business_attestation and has_identity_attestation:
                attestation_score += 5
                attestation_details["both_verified"] = True
                logger.info(f"Both identity and business verified: +5 bonus points")
            
            # On-chain attestation (5 points bonus - shows blockchain commitment)
            has_on_chain_attestation = any(
                att.on_chain and att.status == "verified"
                for att in founder_attestations
            )
            if has_on_chain_attestation:
                attestation_score += 5
                attestation_details["on_chain_attestation"] = True
                logger.info(f"On-chain attestation found: +5 bonus points")
            
            logger.info(f"Total attestation score: {attestation_score} points")
            
            factors["attestation_verification"] = {
                "total_attestations": len(founder_attestations),
                "verified_attestations": len([att for att in founder_attestations if att.status == "verified"]),
                "details": attestation_details,
                "score": attestation_score
            }
        except Exception as e:
            logger.warning(f"Error checking attestations for startup {startup_id}: {e}")
            factors["attestation_verification"] = {
                "total_attestations": 0,
                "verified_attestations": 0,
                "details": {},
                "score": 0.0
            }
        
        score += attestation_score
        
        # Cap at 100 points (attestations are bonus, so they can push score above 100, but we cap it)
        final_score = min(100, round(score, 2))
        
        # Update startup credibility score
        startup.credibility_score = final_score
        db.commit()
        
        logger.info(f"Startup {startup_id} credibility score: {final_score}")
        
        return {
            "credibility_score": final_score,
            "factors": factors,
            "grade": self._get_credibility_grade(final_score),
            "summary": self._get_credibility_summary(final_score, factors)
        }
    
    def _get_credibility_grade(self, score: float) -> str:
        """Get credibility grade based on score."""
        if score >= 85:
            return "A+"
        elif score >= 75:
            return "A"
        elif score >= 65:
            return "B"
        elif score >= 50:
            return "C"
        elif score >= 35:
            return "D"
        else:
            return "F"
    
    def _get_credibility_summary(self, score: float, factors: Dict) -> Dict[str, Any]:
        """Get human-readable credibility summary with recommendations."""
        recommendations = []
        
        # Team recommendations
        if factors.get("team_credibility", {}).get("total", 0) < 15:
            recommendations.append("Add verified team members to boost credibility")
        
        # Business legitimacy recommendations
        if not factors.get("business_legitimacy", {}).get("business_registration_verified"):
            recommendations.append("Verify your business registration documents")
        
        # Product traction recommendations
        if not factors.get("product_traction", {}).get("has_mvp"):
            recommendations.append("Launch an MVP/working prototype to demonstrate viability")
        if factors.get("product_traction", {}).get("user_base_count", 0) == 0:
            recommendations.append("Build a user base (100+ users for better credibility)")
        
        # Investment recommendations
        if factors.get("investment_traction", {}).get("total_amount", 0) == 0:
            recommendations.append("Attract investor backing to increase credibility")
        
        # On-chain recommendations (optional)
        if not factors.get("on_chain_legitimacy", {}).get("registered_on_chain"):
            recommendations.append("(Optional) Register on blockchain for additional credibility")
        
        return {
            "score": score,
            "grade": self._get_credibility_grade(score),
            "recommendations": recommendations,
            "next_milestone": self._get_next_milestone(score, factors)
        }
    
    def get_investor_credibility_view(
        self,
        db: Session,
        startup_id: int
    ) -> Dict[str, Any]:
        """
        Get a comprehensive credibility breakdown for investors.
        Shows what's verified, what's missing, and investment risk assessment.
        """
        startup = db.query(Startup).filter(Startup.id == startup_id).first()
        if not startup:
            return {"error": "Startup not found"}
        
        founder = db.query(User).filter(User.id == startup.founder_id).first()
        investments = db.query(Investment).filter(Investment.startup_id == startup_id).all()
        
        # Get full credibility calculation
        credibility_data = self.calculate_startup_credibility(db, startup_id)
        score = credibility_data["credibility_score"]
        grade = credibility_data["grade"]
        
        # Build investor-friendly breakdown
        verification_checklist = {
            "team": {
                "title": "Team & Leadership",
                "icon": "👥",
                "items": [
                    {
                        "label": "Founder Experience",
                        "verified": startup.founder_experience_years is not None and startup.founder_experience_years > 0,
                        "value": f"{startup.founder_experience_years} years" if startup.founder_experience_years else "Not specified",
                        "required": True,
                        "description": "Founder track record and industry experience"
                    },
                    {
                        "label": "Founder Profile Verified",
                        "verified": startup.founder_profile_verified,
                        "value": "LinkedIn/Social verified" if startup.founder_profile_verified else "Not verified",
                        "required": False,
                        "description": "Social proof and professional background check"
                    },
                    {
                        "label": "Team Members",
                        "verified": (startup.employees_verified or 0) > 0,
                        "value": f"{startup.employees_verified} verified employees" if startup.employees_verified else "No team yet",
                        "required": False,
                        "description": "Verified team members with professional background"
                    }
                ],
                "completion": self._calculate_completion([
                    startup.founder_experience_years is not None and startup.founder_experience_years > 0,
                    startup.founder_profile_verified,
                    (startup.employees_verified or 0) > 0
                ])
            },
            "business": {
                "title": "Business Legitimacy",
                "icon": "🏢",
                "items": [
                    {
                        "label": "Business Registration",
                        "verified": startup.business_registration_verified,
                        "value": "Verified" if startup.business_registration_verified else "Not verified",
                        "required": True,
                        "description": "Legal business registration and incorporation documents"
                    },
                    {
                        "label": "Professional Details",
                        "verified": bool(startup.website and startup.contact_email and startup.address),
                        "value": "Complete" if (startup.website and startup.contact_email and startup.address) else "Incomplete",
                        "required": False,
                        "description": "Website, email, and business address listed"
                    }
                ],
                "completion": self._calculate_completion([
                    startup.business_registration_verified,
                    bool(startup.website and startup.contact_email and startup.address)
                ])
            },
            "product": {
                "title": "Product & Traction",
                "icon": "🚀",
                "items": [
                    {
                        "label": "MVP/Product",
                        "verified": startup.has_mvp,
                        "value": "Live" if startup.has_mvp else "In development",
                        "required": True,
                        "description": "Working MVP or live product available"
                    },
                    {
                        "label": "User Base",
                        "verified": (startup.user_base_count or 0) > 0,
                        "value": f"{startup.user_base_count} users" if startup.user_base_count else "0 users",
                        "required": False,
                        "description": "Active users or customers using the product"
                    },
                    {
                        "label": "Revenue",
                        "verified": (startup.monthly_revenue or 0) > 0,
                        "value": f"${startup.monthly_revenue}/month" if startup.monthly_revenue else "$0/month",
                        "required": False,
                        "description": "Monthly recurring revenue in USDC"
                    }
                ],
                "completion": self._calculate_completion([
                    startup.has_mvp,
                    (startup.user_base_count or 0) > 0,
                    (startup.monthly_revenue or 0) > 0
                ])
            },
            "blockchain": {
                "title": "On-Chain Verification",
                "icon": "⛓️",
                "items": [
                    {
                        "label": "Blockchain Registration",
                        "verified": bool(startup.transaction_signature),
                        "value": "Registered" if startup.transaction_signature else "Not registered",
                        "required": False,
                        "description": "Verified on Solana blockchain (optional, adds credibility)"
                    }
                ],
                "completion": self._calculate_completion([
                    bool(startup.transaction_signature)
                ])
            }
        }
        
        # Investment risk assessment
        risk_level = self._assess_investment_risk(score, verification_checklist)
        
        return {
            "startup_name": startup.name,
            "credibility_score": score,
            "credibility_grade": grade,
            "verification_checklist": verification_checklist,
            "risk_assessment": risk_level,
            "investor_summary": self._get_investor_summary(score, verification_checklist),
            "red_flags": self._identify_red_flags(startup, verification_checklist),
            "green_flags": self._identify_green_flags(startup, verification_checklist),
            "investment_history": {
                "total_investors": len(set(inv.investor_id for inv in investments)),
                "total_raised": sum(inv.amount for inv in investments),
                "number_of_investments": len(investments)
            }
        }
    
    def _calculate_completion(self, items_list: list) -> int:
        """Calculate percentage completion of items."""
        if not items_list:
            return 0
        completed = sum(1 for item in items_list if item)
        return int((completed / len(items_list)) * 100)
    
    def _assess_investment_risk(self, score: float, checklist: Dict) -> Dict[str, Any]:
        """Assess investment risk level based on credibility factors."""
        if score >= 85:
            return {
                "level": "LOW",
                "color": "green",
                "emoji": "✅",
                "description": "Well-documented startup with strong credibility signals"
            }
        elif score >= 75:
            return {
                "level": "MODERATE",
                "color": "blue",
                "emoji": "ℹ️",
                "description": "Good fundamentals, some areas could be stronger"
            }
        elif score >= 65:
            return {
                "level": "MEDIUM",
                "color": "yellow",
                "emoji": "⚠️",
                "description": "Early stage with developing credibility"
            }
        elif score >= 50:
            return {
                "level": "HIGH",
                "color": "orange",
                "emoji": "⚠️ ⚠️",
                "description": "Early stage, requires investor due diligence"
            }
        else:
            return {
                "level": "VERY HIGH",
                "color": "red",
                "emoji": "🚨",
                "description": "Very early stage, minimal verification"
            }
    
    def _get_investor_summary(self, score: float, checklist: Dict) -> str:
        """Get a one-sentence investor-friendly summary."""
        if score >= 85:
            return "Highly credible startup with comprehensive verification across all areas."
        elif score >= 75:
            return "Strong credentials with good team and business fundamentals in place."
        elif score >= 65:
            return "Established business with working product, needs more traction."
        elif score >= 50:
            return "Early stage startup with some verification, higher investment risk."
        else:
            return "Very early stage startup, requires significant due diligence before investment."
    
    def _identify_red_flags(self, startup: Any, checklist: Dict) -> list:
        """Identify red flags that might concern investors."""
        red_flags = []
        
        # Business concerns
        if not startup.business_registration_verified:
            red_flags.append("⚠️ Business registration not verified")
        
        # Team concerns
        if not startup.founder_experience_years or startup.founder_experience_years < 2:
            red_flags.append("⚠️ Founder has limited industry experience")
        if (startup.employees_verified or 0) == 0:
            red_flags.append("⚠️ No verified team members")
        
        # Product concerns
        if not startup.has_mvp:
            red_flags.append("⚠️ No MVP or working product yet")
        if (startup.user_base_count or 0) == 0:
            red_flags.append("⚠️ No active user base")
        
        # Contact concerns
        if not startup.contact_email or not startup.website or not startup.address:
            red_flags.append("⚠️ Incomplete contact information")
        
        return red_flags
    
    def _identify_green_flags(self, startup: Any, checklist: Dict) -> list:
        """Identify positive signals that attract investors."""
        green_flags = []
        
        if startup.founder_experience_years and startup.founder_experience_years >= 5:
            green_flags.append("✅ Experienced founder (5+ years)")
        if startup.founder_profile_verified:
            green_flags.append("✅ Founder profile verified")
        if startup.business_registration_verified:
            green_flags.append("✅ Business legally registered")
        if startup.has_mvp:
            green_flags.append("✅ MVP/product live")
        if (startup.user_base_count or 0) > 100:
            green_flags.append(f"✅ {startup.user_base_count} active users")
        if (startup.monthly_revenue or 0) > 0:
            green_flags.append(f"✅ Generating ${startup.monthly_revenue}/month revenue")
        if startup.transaction_signature:
            green_flags.append("✅ Blockchain verified")
        if (startup.employees_verified or 0) >= 3:
            green_flags.append(f"✅ Team of {startup.employees_verified} verified members")
        
        return green_flags
    
    def _get_next_milestone(self, score: float, factors: Dict) -> str:
        """Get the next credibility milestone to aim for."""
        if score < 35:
            return "Verify business documents (aim for D+ grade)"
        elif score < 50:
            return "Build a team and launch MVP (aim for C grade)"
        elif score < 65:
            return "Get first users/customers (aim for B grade)"
        elif score < 75:
            return "Secure investor backing (aim for A grade)"
        elif score < 85:
            return "Scale user base and revenue (aim for A+ grade)"
        else:
            return "Maintain excellence and continue growth!"


