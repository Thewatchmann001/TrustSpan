#!/usr/bin/env python3
"""
Job Seeding Script
Creates 300-400 diverse jobs in the database for testing and development
"""

import sys
import os
from pathlib import Path
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Job, Startup
from datetime import datetime, timedelta

# Job templates with variations
JOB_TEMPLATES = [
    # Technology Jobs
    {
        "titles": ["Software Engineer", "Senior Software Engineer", "Junior Software Engineer", 
                   "Full Stack Developer", "Backend Developer", "Frontend Developer", 
                   "DevOps Engineer", "Cloud Engineer", "Software Architect"],
        "skills_variations": [
            ["Python", "FastAPI", "PostgreSQL", "Docker"],
            ["JavaScript", "React", "Node.js", "MongoDB"],
            ["Java", "Spring Boot", "MySQL", "Kubernetes"],
            ["Python", "Django", "PostgreSQL", "AWS"],
            ["TypeScript", "Next.js", "Prisma", "Vercel"],
            ["C#", ".NET", "SQL Server", "Azure"],
            ["Go", "Gin", "PostgreSQL", "Docker"],
            ["Ruby", "Rails", "PostgreSQL", "Heroku"],
            ["PHP", "Laravel", "MySQL", "AWS"],
            ["Python", "Flask", "MongoDB", "Docker"],
        ],
        "descriptions": [
            "Build scalable web applications and APIs. Work with modern technologies and best practices.",
            "Develop and maintain backend systems. Ensure code quality and performance optimization.",
            "Create responsive user interfaces and interactive web experiences.",
            "Design and implement cloud infrastructure solutions.",
            "Architect and develop enterprise-grade software systems.",
        ]
    },
    # Healthcare Jobs
    {
        "titles": ["Registered Nurse", "Nurse Practitioner", "Medical Assistant", 
                   "Public Health Officer", "Health Educator", "Medical Laboratory Technician",
                   "Pharmacist", "Pharmacy Technician", "Community Health Worker"],
        "skills_variations": [
            ["Nursing", "Patient Care", "Medical Records", "CPR"],
            ["Public Health", "Health Education", "Community Outreach", "Health Assessment"],
            ["Laboratory Techniques", "Medical Testing", "Equipment Maintenance", "Sample Analysis"],
            ["Pharmacy", "Medication Management", "Patient Counseling", "Inventory Management"],
            ["Community Health", "Health Promotion", "Disease Prevention", "Health Counseling"],
        ],
        "descriptions": [
            "Provide quality healthcare services in community health centers. Must have relevant qualifications.",
            "Develop and implement public health programs. Work on health education initiatives.",
            "Perform laboratory tests and analyze results. Maintain laboratory equipment.",
            "Dispense medications and provide pharmaceutical care to patients.",
            "Promote health and wellness in local communities through education and outreach.",
        ]
    },
    # Education Jobs
    {
        "titles": ["Primary School Teacher", "Secondary School Teacher", "Mathematics Teacher",
                   "English Teacher", "Science Teacher", "Education Program Coordinator",
                   "Curriculum Developer", "School Administrator", "Tutor"],
        "skills_variations": [
            ["Teaching", "Lesson Planning", "Curriculum Development", "Student Assessment"],
            ["Education", "Program Coordination", "Community Engagement", "Educational Leadership"],
            ["Subject Expertise", "Pedagogy", "Classroom Management", "Educational Technology"],
        ],
        "descriptions": [
            "Teach students and develop engaging lesson plans. Assess student progress and provide feedback.",
            "Coordinate educational programs and initiatives. Work with schools and communities.",
            "Develop curriculum materials and educational resources. Support teaching staff.",
        ]
    },
    # Agriculture Jobs
    {
        "titles": ["Agricultural Extension Officer", "Farm Manager", "Agribusiness Manager",
                   "Farm Supervisor", "Agricultural Engineer", "Crop Specialist",
                   "Livestock Manager", "Agricultural Consultant", "Soil Scientist"],
        "skills_variations": [
            ["Agriculture", "Extension Services", "Farm Management", "Crop Production"],
            ["Agribusiness", "Business Management", "Marketing", "Supply Chain"],
            ["Agricultural Engineering", "Irrigation Systems", "Farm Equipment", "Sustainability"],
        ],
        "descriptions": [
            "Provide technical support to farmers. Promote sustainable farming practices.",
            "Manage agricultural business operations. Develop strategies and market products.",
            "Supervise farm operations and workers. Ensure efficient production.",
        ]
    },
    # Engineering Jobs
    {
        "titles": ["Civil Engineer", "Electrical Engineer", "Mechanical Engineer",
                   "Chemical Engineer", "Structural Engineer", "Project Engineer",
                   "Construction Manager", "Site Engineer", "Quality Engineer"],
        "skills_variations": [
            ["Civil Engineering", "Project Management", "Construction", "CAD"],
            ["Electrical Engineering", "System Design", "Maintenance", "Power Systems"],
            ["Mechanical Engineering", "Manufacturing", "Design", "Maintenance"],
            ["Project Management", "Quality Control", "Safety Management", "Budgeting"],
        ],
        "descriptions": [
            "Design and supervise construction projects. Ensure projects meet safety standards.",
            "Design electrical systems and installations. Troubleshoot and maintain equipment.",
            "Design and develop mechanical systems. Ensure quality and efficiency.",
        ]
    },
    # Business & Finance Jobs
    {
        "titles": ["Business Analyst", "Financial Analyst", "Accountant", 
                   "Marketing Manager", "Sales Manager", "Operations Manager",
                   "HR Manager", "Project Manager", "Business Development Manager"],
        "skills_variations": [
            ["Business Analysis", "Data Analysis", "Process Improvement", "Reporting"],
            ["Accounting", "Financial Reporting", "Budgeting", "Taxation"],
            ["Marketing", "Digital Marketing", "Brand Management", "Market Research"],
            ["Sales", "Customer Relations", "Negotiation", "CRM"],
            ["Operations Management", "Process Optimization", "Supply Chain", "Quality Control"],
        ],
        "descriptions": [
            "Analyze business processes and provide recommendations for improvement.",
            "Manage financial records and prepare financial reports. Ensure compliance.",
            "Develop and execute marketing strategies. Build brand awareness.",
        ]
    },
    # Administrative Jobs
    {
        "titles": ["Administrative Assistant", "Office Manager", "Executive Assistant",
                   "Data Entry Clerk", "Receptionist", "Secretary"],
        "skills_variations": [
            ["Office Administration", "Document Management", "Scheduling", "Communication"],
            ["Data Entry", "Record Keeping", "File Management", "Organization"],
        ],
        "descriptions": [
            "Provide administrative support to office operations. Manage documents and schedules.",
            "Handle office reception and administrative tasks. Maintain office organization.",
        ]
    },
    # Sales & Customer Service
    {
        "titles": ["Sales Representative", "Customer Service Representative", "Sales Associate",
                   "Account Manager", "Customer Support Specialist", "Retail Sales Associate"],
        "skills_variations": [
            ["Sales", "Customer Relations", "Communication", "Product Knowledge"],
            ["Customer Service", "Problem Solving", "Communication", "CRM"],
        ],
        "descriptions": [
            "Build relationships with customers and drive sales. Meet sales targets.",
            "Provide excellent customer service and support. Resolve customer inquiries.",
        ]
    },
]

# Locations in Sierra Leone
LOCATIONS = [
    "Freetown, Western Area",
    "Bo, Southern Province",
    "Kenema, Eastern Province",
    "Makeni, Northern Province",
    "Koidu, Kono District",
    "Kabala, Koinadugu District",
    "Port Loko, Port Loko District",
    "Magburaka, Tonkolili District",
    "Pujehun, Pujehun District",
    "Bonthe, Bonthe District",
    "Kailahun, Kailahun District",
    "Moyamba, Moyamba District",
    "Yengema, Kono District",
    "Lunsar, Port Loko District",
    "Kambia, Kambia District",
    "Remote",
]


def generate_jobs(count=350):
    """Generate job data"""
    jobs = []
    used_titles = set()
    
    for i in range(count):
        # Pick random template
        template = random.choice(JOB_TEMPLATES)
        
        # Pick title, avoiding duplicates
        title = random.choice(template["titles"])
        title_variant = f"{title} ({i % 10 + 1})"  # Add variation to avoid exact duplicates
        
        # Pick skills
        skills = random.choice(template["skills_variations"])
        
        # Pick description
        description = random.choice(template["descriptions"])
        
        # Pick location
        location = random.choice(LOCATIONS)
        
        # Pick experience (0-5 years, weighted towards lower)
        min_experience = random.choices(
            [0, 1, 2, 3, 4, 5],
            weights=[30, 25, 20, 15, 7, 3]
        )[0]
        
        # Add some variation to description
        experience_text = f"Minimum {min_experience} year{'s' if min_experience != 1 else ''} of experience required." if min_experience > 0 else "Entry-level position. Training will be provided."
        full_description = f"{description} {experience_text}"
        
        jobs.append({
            "title": title_variant,
            "description": full_description,
            "location": location,
            "skills_required": skills,
            "min_experience": min_experience,
            "company_name": None,  # Will be set based on startup_id
        })
    
    return jobs


def seed_jobs():
    """Seed the database with jobs"""
    db: Session = SessionLocal()
    
    try:
        print("🌱 Seeding jobs database...")
        
        # Get all startups (optional)
        startups = db.query(Startup).all()
        print(f"Found {len(startups)} startups (can proceed without)")
        
        # Generate jobs
        target_count = 350
        jobs_data = generate_jobs(target_count)
        
        print(f"Generated {len(jobs_data)} job listings")
        
        # Assign jobs to startups (or create standalone jobs)
        jobs_created = 0
        for i, job_data in enumerate(jobs_data):
            # 70% chance to assign to a startup, 30% standalone
            if random.random() < 0.7 and startups:
                startup = random.choice(startups)
                job_data["startup_id"] = startup.id
                job_data["company_name"] = None  # Company name comes from startup
            else:
                job_data["startup_id"] = None
                # Generate a company name
                company_types = ["Tech Solutions", "Innovations Ltd", "Global Services", 
                               "Enterprise Solutions", "Digital Services", "Consulting Group",
                               "Solutions Inc", "Business Services", "Professional Services"]
                company_name = f"{random.choice(['Alpha', 'Beta', 'Gamma', 'Delta', 'Omega', 'Prime', 'Apex', 'Summit'])} {random.choice(company_types)}"
                job_data["company_name"] = company_name
            
            # Check if similar job already exists
            existing = db.query(Job).filter(
                Job.title == job_data["title"],
                Job.location == job_data["location"]
            ).first()
            
            if not existing:
                job = Job(**job_data)
                db.add(job)
                jobs_created += 1
                
                if (jobs_created + 1) % 50 == 0:
                    print(f"  Created {jobs_created + 1} jobs...")
        
        db.commit()
        print(f"✅ Created {jobs_created} new jobs")
        print(f"📊 Total jobs in database: {db.query(Job).count()}")
        
    except Exception as e:
        print(f"❌ Error seeding jobs: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_jobs()

