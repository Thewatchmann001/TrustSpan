#!/usr/bin/env python3
"""
Database seeding script for TrustSpan
Creates sample data for testing and development
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import User, Startup, Job, Investment
from app.core.security import get_password_hash
from app.db.models.user import UserRole
from app.blockchain.startup_client import StartupClient
from datetime import datetime
import time

def seed_database():
    """Seed the database with sample data"""
    db: Session = SessionLocal()
    
    try:
        print("🌱 Seeding database...")
        
        # Create Users - Diverse professions
        print("Creating users...")
        users_data = [
            # Job Seekers - Tech
            {
                "full_name": "Alice Johnson",
                "email": "alice@example.com",
                "password": "password123",
                "role": UserRole.JOB_SEEKER,
                "wallet_address": "4mq4nxkHic2TomA529TnYAcoAnPGaweayX5UVZzK7yDf",
                "university": "Fourah Bay College, University of Sierra Leone",
            },
            # Job Seekers - Healthcare
            {
                "full_name": "Fatmata Bangura",
                "email": "fatmata@example.com",
                "password": "password123",
                "role": UserRole.JOB_SEEKER,
                "wallet_address": "AH5CyerJwBPaVbimNJNHmyo9HTUi85rMrqTftQA2QNT5",
                "university": "College of Medicine and Allied Health Sciences",
            },
            # Job Seekers - Education
            {
                "full_name": "Mohamed Kamara",
                "email": "mohamed@example.com",
                "password": "password123",
                "role": UserRole.JOB_SEEKER,
                "wallet_address": "GHLf67UbZyhTQReGVwF1MVDCvJTphbgKE4fpJ6xG9MXn",
                "university": "Fourah Bay College, University of Sierra Leone",
            },
            # Job Seekers - Agriculture
            {
                "full_name": "Mariatu Sesay",
                "email": "mariatu@example.com",
                "password": "password123",
                "role": UserRole.JOB_SEEKER,
                "wallet_address": "BW7XpTzMhgkVNPRuF6S1oApA24E3XADzewok6XxdZEpv",
                "university": "Njala University",
            },
            # Job Seekers - Business
            {
                "full_name": "Ibrahim Koroma",
                "email": "ibrahim@example.com",
                "password": "password123",
                "role": UserRole.JOB_SEEKER,
                "wallet_address": "3ifwb7tjkFMibUH6t6Y5vr9WSUpHSDy6YFqiUcQF4C5K",
                "university": "Fourah Bay College, University of Sierra Leone",
            },
            # Job Seekers - Engineering
            {
                "full_name": "Aminata Conteh",
                "email": "aminata@example.com",
                "password": "password123",
                "role": UserRole.JOB_SEEKER,
                "wallet_address": "nao8kDPUhVz1qJeJ8rkKzG85zKgK7yToNLNTqoE9gbZ",
                "university": "Fourah Bay College, University of Sierra Leone",
            },
            # Founders (Startups)
            {
                "full_name": "David Founder",
                "email": "david@startup.com",
                "password": "password123",
                "role": UserRole.STARTUP,
                "wallet_address": "BhLh32RvnYxF3qesVxkjgKjPpg9gUF24oFUPDM3VkwW6",
                "company_name": "TechInnovate SL",
            },
            {
                "full_name": "Hawa Mansaray",
                "email": "hawa@startup.com",
                "password": "password123",
                "role": UserRole.STARTUP,
                "wallet_address": "AcYnQ3GHDHF5e8NojkCZVGo294RpJNSqqSgNkWnCQDzH",
                "company_name": "HealthConnect Sierra Leone",
            },
            # Investors
            {
                "full_name": "Frank Investor",
                "email": "frank@investor.com",
                "password": "password123",
                "role": UserRole.INVESTOR,
                "wallet_address": "FwJVofSALMXyNZXwGoCkVvPkUk435gCtfCgR8Gj9LG2b",
            },
            {
                "full_name": "Kadiatu Fofanah",
                "email": "kadiatu@investor.com",
                "password": "password123",
                "role": UserRole.INVESTOR,
                "wallet_address": "9xKpLmNqR2sTvW4yZ6aB8cD1eF3gH5jK7mN9pQ2r",
            },
        ]
        
        users = []
        updated_count = 0
        for user_data in users_data:
            existing = db.query(User).filter(User.email == user_data["email"]).first()
            if not existing:
                user = User(
                    full_name=user_data["full_name"],
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    role=user_data["role"],
                    wallet_address=user_data["wallet_address"],
                    university=user_data.get("university"),
                    company_name=user_data.get("company_name"),
                )
                db.add(user)
                users.append(user)
            else:
                # Update existing user's wallet address and other fields if they're missing or outdated
                updated = False
                # Always update wallet address if provided and different (seed script is source of truth)
                if user_data.get("wallet_address"):
                    current_wallet = existing.wallet_address or ""
                    new_wallet = user_data["wallet_address"].strip()
                    
                    # Check if wallet needs updating:
                    # 1. Current wallet is invalid (contains "Wallet" or wrong length)
                    # 2. Current wallet is different from seed data
                    is_invalid = "Wallet" in current_wallet or len(current_wallet) < 32 or len(current_wallet) > 44
                    is_different = current_wallet != new_wallet
                    
                    if is_invalid or (is_different and new_wallet):
                        # Check if new wallet address is not already taken by another user
                        wallet_taken = db.query(User).filter(
                            User.wallet_address == new_wallet,
                            User.id != existing.id
                        ).first()
                        if not wallet_taken:
                            existing.wallet_address = new_wallet
                            updated = True
                            print(f"  Updated wallet for {existing.email}: {current_wallet[:20] if current_wallet else 'None'}... → {new_wallet[:20]}...")
                if user_data.get("university") and not existing.university:
                    existing.university = user_data.get("university")
                    updated = True
                if user_data.get("company_name") and not existing.company_name:
                    existing.company_name = user_data.get("company_name")
                    updated = True
                if updated:
                    updated_count += 1
                users.append(existing)
        
        db.commit()
        print(f"✅ Created/Updated {len(users)} users ({updated_count} updated)")
        
        # Certificates removed - not part of core solutions
        # Education information is now stored in User.university field and CV education section
        
        # Create Startups - Diverse sectors
        print("Creating startups...")
        startups_data = [
            {
                "founder_id": users[6].id,  # David
                "startup_id": None,  # Will be generated by blockchain
                "name": "TechInnovate SL",
                "sector": "Technology",
                "country": "Sierra Leone",
                "employees_verified": 2,
                "credibility_score": 85.5,
                "transaction_signature": None,  # Will be set when registered on-chain
                "description": "TechInnovate SL is a leading software development company in Sierra Leone, specializing in custom web and mobile applications for local businesses. We help SMEs digitize their operations, improve customer engagement, and scale their businesses through innovative technology solutions. Our team of experienced developers has delivered over 50 successful projects across various industries including retail, healthcare, education, and finance.",
                "website": "https://techinnovate-sl.com",
                "contact_email": "contact@techinnovate-sl.com",
                "phone": "+232 76 123 456",
                "address": "123 Siaka Stevens Street, Freetown, Sierra Leone",
                "year_founded": 2020,
                "team_size": 15,
                "mission": "To empower Sierra Leonean businesses with cutting-edge technology solutions that drive growth and innovation. We believe every business, regardless of size, deserves access to world-class technology that can transform their operations and unlock their potential.",
                "vision": "To become the leading technology partner for businesses across West Africa by 2030, creating a thriving digital economy that generates employment opportunities and drives sustainable economic development.",
                "products_services": "Custom software development (web and mobile applications), e-commerce platforms, business management systems, cloud migration services, IT consulting, digital transformation strategies, and ongoing technical support and maintenance.",
                "funding_goal": 500000.0,
                "pitch_deck_url": "https://techinnovate-sl.com/pitch-deck.pdf",
            },
            {
                "founder_id": users[7].id,  # Hawa
                "startup_id": None,  # Will be generated by blockchain
                "name": "HealthConnect Sierra Leone",
                "sector": "Healthcare",
                "country": "Sierra Leone",
                "employees_verified": 1,
                "credibility_score": 78.0,
                "transaction_signature": None,
                "description": "HealthConnect provides telemedicine services and health information management systems to improve healthcare access in rural Sierra Leone. Our platform connects patients in remote areas with qualified doctors via video consultations, reducing travel costs and wait times. We've served over 5,000 patients across 12 districts, improving healthcare outcomes and reducing mortality rates in underserved communities.",
                "website": "https://healthconnect-sl.com",
                "contact_email": "info@healthconnect-sl.com",
                "phone": "+232 76 234 567",
                "address": "45 Main Road, Bo, Sierra Leone",
                "year_founded": 2021,
                "team_size": 8,
                "mission": "To make quality healthcare accessible to every Sierra Leonean through innovative technology solutions. We bridge the gap between rural communities and medical professionals, ensuring no one is left behind due to geographical or financial constraints.",
                "vision": "A Sierra Leone where distance and cost are no longer barriers to quality healthcare. We envision a future where every citizen can access medical consultations, health records, and preventive care services from their mobile devices.",
                "products_services": "Telemedicine platform with video consultations, electronic health records (EHR) system, health data analytics and reporting, mobile health clinics coordination, prescription management, appointment scheduling, and health education resources.",
                "funding_goal": 300000.0,
                "pitch_deck_url": "https://healthconnect-sl.com/pitch-deck.pdf",
            },
            {
                "founder_id": users[6].id,  # David
                "startup_id": None,  # Will be generated by blockchain
                "name": "AgriTech Solutions",
                "sector": "Agriculture",
                "country": "Sierra Leone",
                "employees_verified": 1,
                "credibility_score": 72.0,
                "transaction_signature": None,
                "description": "AgriTech Solutions helps farmers increase crop yields through precision agriculture, market access platforms, and agricultural training. We work with over 2,000 smallholder farmers across Sierra Leone, providing them with mobile-based tools to track crops, access weather forecasts, connect with buyers, and receive expert farming advice. Our platform has helped farmers increase their income by an average of 35%.",
                "website": "https://agritech-sl.com",
                "contact_email": "hello@agritech-sl.com",
                "phone": "+232 76 345 678",
                "address": "Farmers Market, Kenema, Sierra Leone",
                "year_founded": 2019,
                "team_size": 12,
                "mission": "To transform agriculture in Sierra Leone through technology and sustainable farming practices. We empower farmers with data-driven insights, market connections, and knowledge that enables them to maximize productivity while preserving the environment for future generations.",
                "vision": "To make Sierra Leone food-secure and a leading agricultural exporter in West Africa. We envision a thriving agricultural sector where technology and traditional knowledge work together to create prosperity for farming communities.",
                "products_services": "Farm management software (crop tracking, inventory management), crop monitoring systems with SMS alerts, market linkage platform connecting farmers to buyers, agricultural advisory services via mobile, weather forecasting, pest and disease identification tools, and financial services for farmers.",
                "funding_goal": 400000.0,
                "pitch_deck_url": "https://agritech-sl.com/pitch-deck.pdf",
            },
            {
                "founder_id": users[7].id,  # Hawa
                "startup_id": None,  # Will be generated by blockchain
                "name": "EduBridge SL",
                "sector": "Education",
                "country": "Sierra Leone",
                "employees_verified": 0,
                "credibility_score": 65.0,
                "transaction_signature": None,
                "description": "EduBridge provides online learning platforms and educational resources to bridge the digital divide in Sierra Leone's education sector. Our platform offers courses aligned with the national curriculum, interactive lessons, and assessment tools. We've partnered with 15 schools and have over 3,000 active student users. Our offline-capable mobile app ensures learning continues even in areas with limited internet connectivity.",
                "website": "https://edubridge-sl.com",
                "contact_email": "contact@edubridge-sl.com",
                "phone": "+232 76 456 789",
                "address": "University Road, Makeni, Sierra Leone",
                "year_founded": 2022,
                "team_size": 6,
                "mission": "To democratize quality education through accessible online learning platforms. We believe every child deserves access to excellent educational content, regardless of their location or socioeconomic background. Our mission is to level the playing field and unlock the potential of Sierra Leone's youth.",
                "vision": "Every Sierra Leonean student should have access to world-class educational resources regardless of location. We envision a future where students in remote villages have the same learning opportunities as those in urban centers, creating a generation of well-educated, globally competitive citizens.",
                "products_services": "Online learning management system (LMS) with course creation tools, educational content library (videos, quizzes, interactive exercises), virtual classrooms with live sessions, teacher training programs, student progress tracking and analytics, offline-capable mobile app, and certification programs.",
                "funding_goal": 250000.0,
                "pitch_deck_url": "https://edubridge-sl.com/pitch-deck.pdf",
            },
            {
                "founder_id": users[6].id,  # David
                "startup_id": None,  # Will be generated by blockchain
                "name": "FinTech Sierra Leone",
                "sector": "Finance",
                "country": "Sierra Leone",
                "employees_verified": 1,
                "credibility_score": 70.0,
                "transaction_signature": None,
                "description": "FinTech Sierra Leone provides digital payment solutions, mobile banking, and financial inclusion services for the unbanked population. Our mobile money platform enables users to send and receive money, pay bills, purchase airtime, and access micro-loans without needing a traditional bank account. With over 25,000 registered users and partnerships with major merchants, we're making financial services accessible to everyone.",
                "website": "https://fintech-sl.com",
                "contact_email": "support@fintech-sl.com",
                "phone": "+232 76 567 890",
                "address": "Bank Street, Freetown, Sierra Leone",
                "year_founded": 2020,
                "team_size": 10,
                "mission": "To bring financial services to every Sierra Leonean through innovative fintech solutions. We're breaking down barriers to financial inclusion by providing secure, affordable, and user-friendly digital financial services that empower individuals and businesses to participate in the digital economy.",
                "vision": "A financially inclusive Sierra Leone where everyone can access banking and payment services. We envision a cashless economy where transactions are seamless, secure, and accessible to all, driving economic growth and reducing poverty.",
                "products_services": "Mobile money platform with USSD and app interfaces, digital wallet with multi-currency support, peer-to-peer money transfers, bill payments (utilities, school fees, taxes), micro-loan services with flexible repayment, merchant payment solutions, savings products, and financial literacy programs.",
                "funding_goal": 600000.0,
                "pitch_deck_url": "https://fintech-sl.com/pitch-deck.pdf",
            },
            {
                "founder_id": users[7].id,  # Hawa
                "startup_id": None,  # Will be generated by blockchain
                "name": "Sierra Tourism Hub",
                "sector": "Tourism",
                "country": "Sierra Leone",
                "employees_verified": 0,
                "credibility_score": 60.0,
                "transaction_signature": None,
                "description": "Sierra Tourism Hub connects tourists with local experiences, accommodations, and tour guides to showcase Sierra Leone's natural beauty and culture. We've curated over 50 unique experiences including beach tours, wildlife safaris, cultural village visits, and historical site tours. Our platform has facilitated over 1,500 bookings and works with 30+ local tour operators and 25+ accommodation providers, ensuring tourists have authentic experiences while supporting local communities.",
                "website": "https://sierratourism-sl.com",
                "contact_email": "bookings@sierratourism-sl.com",
                "phone": "+232 76 678 901",
                "address": "Beach Road, Lumley, Freetown, Sierra Leone",
                "year_founded": 2021,
                "team_size": 5,
                "mission": "To promote sustainable tourism that benefits local communities and preserves Sierra Leone's natural heritage. We believe tourism should be a force for good, creating employment opportunities, preserving cultural traditions, and protecting our beautiful natural environment for future generations.",
                "vision": "To make Sierra Leone a top destination for responsible and authentic travel experiences. We envision a thriving tourism industry that showcases our country's unique attractions while ensuring that local communities are the primary beneficiaries of tourism revenue.",
                "products_services": "Tour booking platform with instant confirmation, accommodation listings (hotels, guesthouses, homestays), verified local guide services, cultural experience packages (dancing, cooking, traditional crafts), travel planning tools and itineraries, transportation booking, and customer support in multiple languages.",
                "funding_goal": 200000.0,
                "pitch_deck_url": "https://sierratourism-sl.com/pitch-deck.pdf",
            },
            {
                "founder_id": users[6].id,  # David
                "startup_id": None,  # Will be generated by blockchain
                "name": "BuildSL Construction",
                "sector": "Construction",
                "country": "Sierra Leone",
                "employees_verified": 2,
                "credibility_score": 75.0,
                "transaction_signature": None,
                "description": "BuildSL Construction provides affordable, quality construction services and building materials for residential and commercial projects. We've completed over 100 projects including schools, clinics, housing developments, and commercial buildings across Sierra Leone. Our commitment to quality, timely delivery, and fair pricing has made us a trusted partner for both private clients and government projects. We source locally-produced building materials whenever possible, supporting the local economy.",
                "website": "https://buildsl-construction.com",
                "contact_email": "info@buildsl-construction.com",
                "phone": "+232 76 789 012",
                "address": "Construction Zone, Koidu, Sierra Leone",
                "year_founded": 2019,
                "team_size": 20,
                "mission": "To build quality, affordable infrastructure that supports Sierra Leone's development goals. We're committed to constructing buildings and infrastructure that are safe, sustainable, and accessible, contributing to the nation's progress while creating employment opportunities for local workers.",
                "vision": "To be the leading construction company known for quality, sustainability, and community impact. We envision a Sierra Leone with modern, well-built infrastructure that serves as a foundation for economic growth and improved quality of life for all citizens.",
                "products_services": "Residential construction (houses, apartments, housing estates), commercial buildings (offices, shops, warehouses), infrastructure projects (roads, bridges, water systems), building materials supply (cement, steel, roofing, plumbing), construction consulting and project management, architectural design services, and maintenance and renovation services.",
                "funding_goal": 800000.0,
                "pitch_deck_url": "https://buildsl-construction.com/pitch-deck.pdf",
            },
        ]
        
        # Initialize blockchain client
        startup_client = StartupClient()
        registered_count = 0
        
        for startup_data in startups_data:
            # Check if startup already exists by name and founder
            existing = db.query(Startup).filter(
                Startup.name == startup_data["name"],
                Startup.founder_id == startup_data["founder_id"]
            ).first()
            
            if existing:
                # Update existing startup with complete information
                print(f"  Updating existing startup: {startup_data['name']}")
                
                # Check if startup needs on-chain registration (has mock signature or no signature)
                needs_registration = (
                    not existing.transaction_signature or 
                    existing.transaction_signature.startswith("mock_")
                )
                
                if needs_registration:
                    # Get founder to register on-chain
                    founder = db.query(User).filter(User.id == startup_data["founder_id"]).first()
                    
                    if founder and founder.wallet_address:
                        from app.utils.helpers import validate_solana_address
                        if validate_solana_address(founder.wallet_address):
                            try:
                                print(f"  Registering {startup_data['name']} on blockchain (replacing mock signature)...")
                                blockchain_result = startup_client.register_startup(
                                    startup_name=startup_data["name"],
                                    sector=startup_data["sector"],
                                    founder_address=founder.wallet_address
                                )
                                
                                # Update with real blockchain transaction
                                existing.startup_id = blockchain_result.get("startup_id", existing.startup_id)
                                existing.transaction_signature = blockchain_result.get("transaction_signature")
                                
                                print(f"  ✅ Registered on-chain: {blockchain_result.get('startup_id')}")
                                if blockchain_result.get('transaction_signature'):
                                    print(f"     Transaction: {blockchain_result.get('transaction_signature')[:30]}...")
                                
                                registered_count += 1
                                time.sleep(2)  # Rate limiting
                            except Exception as e:
                                print(f"  ⚠️  Failed to register on-chain: {str(e)}")
                                print(f"     Keeping existing data...")
                
                # Update other fields
                for key, value in startup_data.items():
                    # Skip startup_id and transaction_signature (already handled above)
                    if key in ["startup_id", "transaction_signature", "founder_id"]:
                        continue
                    if value is not None:
                        setattr(existing, key, value)
                
                db.commit()
                print(f"  ✅ Updated {startup_data['name']} with complete information")
            else:
                # Get founder to get wallet address
                founder = db.query(User).filter(User.id == startup_data["founder_id"]).first()
                
                if founder and founder.wallet_address:
                    # Validate wallet address before attempting registration
                    from app.utils.helpers import validate_solana_address
                    if not validate_solana_address(founder.wallet_address):
                        print(f"  ⚠️  Invalid wallet address for {startup_data['name']}: {founder.wallet_address[:20]}...")
                        print(f"     Skipping blockchain registration...")
                        if not startup_data.get("startup_id"):
                            startup_data["startup_id"] = f"STARTUP-{startup_data['founder_id']}-{int(time.time())}"
                        startup_data["transaction_signature"] = None
                    else:
                        try:
                            # Register startup on blockchain (this generates the startup_id)
                            print(f"  Registering {startup_data['name']} on blockchain...")
                            blockchain_result = startup_client.register_startup(
                                startup_name=startup_data["name"],
                                sector=startup_data["sector"],
                                founder_address=founder.wallet_address
                            )
                            
                            # Use blockchain-generated startup_id and transaction signature
                            startup_data["startup_id"] = blockchain_result.get("startup_id")
                            startup_data["transaction_signature"] = blockchain_result.get("transaction_signature")
                            
                            print(f"  ✅ Registered on-chain: {blockchain_result.get('startup_id')}")
                            if blockchain_result.get('transaction_signature'):
                                print(f"     Transaction: {blockchain_result.get('transaction_signature')[:20]}...")
                            
                            registered_count += 1
                            
                            # Small delay to avoid rate limiting
                            time.sleep(2)
                        except Exception as e:
                            print(f"  ⚠️  Failed to register {startup_data['name']} on-chain: {str(e)}")
                            print(f"     Continuing with database-only registration...")
                            # Generate a fallback startup_id if blockchain fails
                            if not startup_data.get("startup_id"):
                                startup_data["startup_id"] = f"STARTUP-{startup_data['founder_id']}-{int(time.time())}"
                            startup_data["transaction_signature"] = None
                else:
                    print(f"  ⚠️  Founder {startup_data['founder_id']} has no wallet address, skipping blockchain registration")
                    # Generate a fallback startup_id
                    if not startup_data.get("startup_id"):
                        startup_data["startup_id"] = f"STARTUP-{startup_data['founder_id']}-{int(time.time())}"
                    startup_data["transaction_signature"] = None
                
                # Create startup in database
                startup = Startup(**startup_data)
                db.add(startup)
        
        db.commit()
        
        # Clean up old incomplete startups (those without descriptions) that don't match our seed data
        print("Cleaning up old incomplete startups...")
        seed_startup_names = {s["name"] for s in startups_data}
        incomplete_startups = db.query(Startup).filter(
            Startup.description == None
        ).all()
        removed_count = 0
        for old_startup in incomplete_startups:
            # Only remove if it's not in our seed data
            if old_startup.name not in seed_startup_names:
                print(f"  Removing incomplete startup: {old_startup.name} (ID: {old_startup.id})")
                db.delete(old_startup)
                removed_count += 1
        db.commit()
        if removed_count > 0:
            print(f"  ✅ Removed {removed_count} incomplete startups")
        
        print(f"✅ Created/Updated {len(startups_data)} startups ({registered_count} registered on-chain)")
        
        # Create Jobs - DEPRECATED: Jobs now come from external integrations only (RemoteOK, Freelancer.com)
        # Jobs are NOT stored in the database anymore
        print("Skipping job creation - jobs now come from external integrations (RemoteOK, Freelancer.com) only")
        # if False:  # Disabled - jobs from integrations only
        #     startups = db.query(Startup).all()
        #     if startups:
        #         jobs_data = [
        #             # Technology Jobs
        #             {
        #                 "startup_id": startups[0].id,  # TechInnovate
        #                 "title": "Senior Software Engineer",
        #                 "description": "Build scalable backend systems using Python and FastAPI. Work on blockchain integration and API development.",
        #                 "location": "Freetown, Western Area",
        #                 "skills_required": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        #                 "min_experience": 3,
        #             },
        #             {
        #                 "startup_id": startups[0].id,
        #                 "title": "Frontend Developer",
        #                 "description": "Create beautiful user interfaces with React and Next.js. Implement responsive designs and optimize performance.",
        #                 "location": "Bo, Southern Province",
        #                 "skills_required": ["React", "Next.js", "TypeScript", "Tailwind CSS"],
        #                 "min_experience": 2,
        #             },
        #             {
        #                 "startup_id": startups[0].id,
        #                 "title": "Mobile App Developer",
        #                 "description": "Develop mobile applications for iOS and Android platforms. Experience with React Native or Flutter preferred.",
        #                 "location": "Kenema, Eastern Province",
        #                 "skills_required": ["React Native", "Flutter", "Mobile Development"],
        #                 "min_experience": 1,
        #             },
        #             # Healthcare Jobs
        #             {
        #                 "startup_id": startups[1].id,  # HealthConnect
        #                 "title": "Registered Nurse",
        #                 "description": "Provide quality healthcare services in community health centers. Must have nursing qualifications and experience.",
        #                 "location": "Makeni, Northern Province",
        #                 "skills_required": ["Nursing", "Patient Care", "Medical Records"],
        #                 "min_experience": 2,
        #             },
        #             {
        #                 "startup_id": startups[1].id,
        #                 "title": "Public Health Officer",
        #                 "description": "Develop and implement public health programs. Work on health education and community outreach.",
        #                 "location": "Koidu, Kono District",
        #                 "skills_required": ["Public Health", "Health Education", "Community Outreach"],
        #                 "min_experience": 1,
        #             },
        #             {
        #                 "startup_id": startups[1].id,
        #                 "title": "Medical Laboratory Technician",
        #                 "description": "Perform laboratory tests and analyze results. Maintain laboratory equipment and records.",
        #                 "location": "Freetown, Western Area",
        #                 "skills_required": ["Laboratory Techniques", "Medical Testing", "Equipment Maintenance"],
        #                 "min_experience": 1,
        #             },
        #             # Agriculture Jobs
        #             {
        #                 "startup_id": startups[2].id,  # AgriTech
        #                 "title": "Agricultural Extension Officer",
        #                 "description": "Provide technical support to farmers. Promote sustainable farming practices and modern agricultural techniques.",
        #                 "location": "Kabala, Koinadugu District",
        #                 "skills_required": ["Agriculture", "Extension Services", "Farm Management"],
        #                 "min_experience": 2,
        #             },
        #             {
        #                 "startup_id": startups[2].id,
        #                 "title": "Agribusiness Manager",
        #                 "description": "Manage agricultural business operations. Develop business strategies and market agricultural products.",
        #                 "location": "Port Loko, Port Loko District",
        #                 "skills_required": ["Agribusiness", "Business Management", "Marketing"],
        #                 "min_experience": 3,
        #             },
        #             {
        #                 "startup_id": startups[2].id,
        #                 "title": "Farm Supervisor",
        #                 "description": "Supervise farm operations and workers. Ensure efficient production and quality control.",
        #                 "location": "Magburaka, Tonkolili District",
        #                 "skills_required": ["Farm Management", "Supervision", "Crop Production"],
        #                 "min_experience": 1,
        #             },
        #             # Education Jobs
        #             {
        #                 "startup_id": startups[3].id,  # EduBridge
        #                 "title": "Primary School Teacher",
        #                 "description": "Teach primary school students. Develop lesson plans and assess student progress.",
        #                 "location": "Pujehun, Pujehun District",
        #                 "skills_required": ["Teaching", "Lesson Planning", "Child Development"],
        #                 "min_experience": 1,
        #             },
        #             {
        #                 "startup_id": startups[3].id,
        #                 "title": "Education Program Coordinator",
        #                 "description": "Coordinate educational programs and initiatives. Work with schools and communities.",
        #                 "location": "Bonthe, Bonthe District",
        #                 "skills_required": ["Program Coordination", "Education", "Community Engagement"],
        #                 "min_experience": 2,
        #             },
        #             {
        #                 "startup_id": startups[3].id,
        #                 "title": "Mathematics Teacher",
        #                 "description": "Teach mathematics to secondary school students. Help students prepare for examinations.",
        #                 "location": "Kailahun, Kailahun District",
        #                 "skills_required": ["Mathematics", "Teaching", "Curriculum Development"],
        #                 "min_experience": 2,
        #             },
        #             # Engineering Jobs
        #             {
        #                 "startup_id": startups[0].id,  # TechInnovate
        #                 "title": "Civil Engineer",
        #                 "description": "Design and supervise construction projects. Ensure projects meet safety and quality standards.",
        #                 "location": "Freetown, Western Area",
        #                 "skills_required": ["Civil Engineering", "Project Management", "Construction"],
        #                 "min_experience": 3,
        #             },
        #             {
        #                 "startup_id": startups[0].id,
        #                 "title": "Electrical Engineer",
        #                 "description": "Design electrical systems and installations. Troubleshoot and maintain electrical equipment.",
        #                 "location": "Bo, Southern Province",
        #                 "skills_required": ["Electrical Engineering", "System Design", "Maintenance"],
        #                 "min_experience": 2,
        #             },
        #         ]
        #
        #         for job_data in jobs_data:
        #             job = Job(**job_data)
        #             db.add(job)
        #
        #         db.commit()
        #         print(f"✅ Created {len(jobs_data)} jobs")
        
        # Create Investments - Skip mock investments
        # Real investments should be made through the UI which will create proper blockchain transactions
        print("Skipping mock investments - real investments should be made through the UI")
        # Note: Investments are now created through the /api/startups/{startup_id}/invest endpoint
        # which properly records them on the blockchain with real transaction signatures
        
        print("\n🎉 Database seeding completed successfully!")
        print("\n📋 Sample Login Credentials:")
        print("  Job Seekers:")
        print("    - alice@example.com / password123 (Tech - Fourah Bay College)")
        print("    - fatmata@example.com / password123 (Healthcare - College of Medicine)")
        print("    - mohamed@example.com / password123 (Education - Fourah Bay College)")
        print("    - mariatu@example.com / password123 (Agriculture - Njala University)")
        print("    - ibrahim@example.com / password123 (Business - Fourah Bay College)")
        print("    - aminata@example.com / password123 (Engineering - Fourah Bay College)")
        print("  Startup Founders:")
        print("    - david@startup.com / password123 (TechInnovate SL, AgriTech, FinTech, BuildSL)")
        print("    - hawa@startup.com / password123 (HealthConnect, EduBridge, Sierra Tourism)")
        print("  Investors:")
        print("    - frank@investor.com / password123")
        print("    - kadiatu@investor.com / password123")
        print("\n💡 Note: Certificates are no longer part of the system.")
        print("   Education information is stored in User.university and CV education sections.")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

