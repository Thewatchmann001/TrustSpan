"""
Test script to see how your CV is being parsed and what the ATS sees
"""
import json

# Sample CV data based on your actual CV text
test_cv = {
    "personal_info": {
        "full_name": "ALIM ISMAEL KAMARA",
        "email": "alimkamara408@gmail.com",
        "phone": "(+232) 74360026",
        "location": "Freetown, Sierra Leone"
    },
    "summary": "Award-winning Computer Engineer and 2025 Valedictorian with proven expertise in AI/ML, blockchain, fintech, and full-stack development. Achieved R² score of 0.90 in predictive models.",
    "experience": [
        {
            "job_title": "Director of Tech. & Innovation",
            "company": "Center for Africa Financial Inclusion & Advancement (CAFIA)",
            "start_date": "Current",
            "description": "Supported research and data projects. Developed fintech solutions and digital platforms."
        },
        {
            "job_title": "Head of developers",
            "company": "BAU Cyprus University",
            "start_date": "01/07/2024",
            "end_date": "20/08/2024",
            "description": "Led team as Database manager and Fullstack developer. Reduced stock discrepancies by 40%."
        }
    ],
    "education": [
        {
            "degree": "Bachelor of Computer Engineering",
            "institution": "Bahcesehir cyprus university",
            "field_of_study": "Computer Engineering",
            "start_date": "21/09/2021",
            "end_date": "27/06/2025",
            "grade": "3.93/4.00"
        }
    ],
    "skills": {
        "technical": ["Python", "JavaScript", "C", "C++", "Java", "SQL", "MATLAB"],
        "computer_skills": ["Flask", "TensorFlow", "OpenAI API", "Flutter", "React", "Web3.js", "Next.js", "Node.js", "scikit-learn"],
        "programming_skills": ["Solana", "Smart Contracts", "Decentralized Identity", "Web3 Integration"],
        "job_related_skills": ["Git", "Docker", "Linux", "RESTful APIs", "Jupyter", "SQLite", "PostgreSQL", "Database Design"],
        "languages": ["English (C2)", "Krio (Native)"]
    },
    "projects": [
        {
            "name": "Pharmacy Inventory Management",
            "description": "Built system managing 200+ SKUs with barcode scanning reducing data entry by 60%"
        },
        {
            "name": "TrustSpan",
            "description": "AI-powered CV optimization and blockchain investment platform"
        }
    ],
    "awards": [
        {
            "name": "Valedictorian",
            "issuer": "BAU Cyprus University",
            "date": "27/06/2025"
        }
    ]
}

# Test the completeness check
print("=" * 80)
print("CV STRUCTURE ANALYSIS")
print("=" * 80)

# Check experience
exp_list = test_cv.get("experience", []) or []
work_exp_list = test_cv.get("work_experience", []) or []
experience_entries = exp_list + work_exp_list
print(f"\nExperience entries: {len(experience_entries)}")
for i, exp in enumerate(experience_entries, 1):
    has_title = bool(exp.get("job_title") or exp.get("position") or exp.get("title"))
    has_company = bool(exp.get("company") or exp.get("employer") or exp.get("organization"))
    print(f"  Entry {i}: title={has_title}, company={has_company}")

# Check education
edu_list = test_cv.get("education", []) or []
print(f"\nEducation entries: {len(edu_list)}")
for i, edu in enumerate(edu_list, 1):
    has_degree = bool(edu.get("degree") or edu.get("qualification"))
    has_institution = bool(edu.get("institution") or edu.get("school") or edu.get("university"))
    print(f"  Entry {i}: degree={has_degree}, institution={has_institution}")

# Check skills - THIS IS THE PROBLEM
skills_data = test_cv.get("skills", {}) or test_cv.get("personal_skills", {})
print(f"\nSkills structure:")
total_skills = 0
for skill_type, skill_list in skills_data.items():
    if isinstance(skill_list, list):
        count = len(skill_list)
        total_skills += count
        print(f"  {skill_type}: {count} skills")
        if count > 0:
            print(f"    → {', '.join(str(s)[:30] for s in skill_list[:3])}...")
    elif isinstance(skill_list, str):
        skills_as_list = [s.strip() for s in skill_list.split(',')]
        count = len(skills_as_list)
        total_skills += count
        print(f"  {skill_type}: {count} skills (STRING FORMAT)")
        print(f"    → {', '.join(skills_as_list[:3])}...")

print(f"\nTOTAL SKILLS COUNTED: {total_skills}")
print("\n" + "=" * 80)
print("COMPLETENESS CHECK")
print("=" * 80)

has_summary = bool(test_cv.get("summary") or test_cv.get("professional_summary"))
has_experience = len(experience_entries) > 0
has_education = len(edu_list) > 0
has_skills = bool(skills_data and any(
    (isinstance(v, list) and len(v) > 0) or (isinstance(v, str) and v.strip()) 
    for v in skills_data.values()
))

print(f"Summary: {'✓' if has_summary else '✗'}")
print(f"Experience: {'✓' if has_experience else '✗'} ({len(experience_entries)} entries)")
print(f"Education: {'✓' if has_education else '✗'} ({len(edu_list)} entries)")
print(f"Skills: {'✓' if has_skills else '✗'} ({total_skills} skills)")
print(f"\nCompleteness: {sum([has_summary, has_experience, has_education, has_skills])}/4 sections")

# Check contact
personal = test_cv.get("personal_info", {}) or {}
has_email = bool(personal.get("email"))
print(f"Contact (Email): {'✓' if has_email else '✗'}")
