"""
Test ATS scoring with Alim's CV data
"""
import sys
sys.path.insert(0, '/home/lim-kam/Hackathon_Trust_bridge/backend')

from cv.ats_engine import get_ats_engine

# Sample CV data based on Alim's CV
test_cv_data = {
    "personal_info": {
        "full_name": "ALIM ISMAEL KAMARA",
        "email": "alimkamara408@gmail.com",
        "phone": "(+232) 74360026",
        "location": "Freetown, Sierra Leone"
    },
    "summary": "Award-winning Computer Engineer and 2025 Valedictorian with proven expertise in AI/ML, blockchain, fintech, and full-stack development. Led the development of AI-powered, blockchain-integrated platforms focused on real-world use cases in financial technology, credential verification, and career optimization. Designed decentralized solutions for data integrity, investment workflows, and employment-focused systems. Achieved an R² score of 0.90 in predictive models analyzing data from 50 African countries. Passionate about leveraging blockchain and AI to address financial inclusion and employment challenges in emerging markets.",
    "experience": [
        {
            "job_title": "Director of Tech. & Innovation",
            "company": "Center for Africa Financial Inclusion & Advancement (CAFIA)",
            "start_date": "Current",
            "description": "Supported research and data projects on financial inclusion and SME transformation. Contributed to enterprise mapping, policy briefs, and literacy programs. Assisted in developing fintech solutions and digital platforms. Engaged governments, SMEs, investors, and partners to drive inclusion. Promoted capacity building, advisory support, and Islamic finance initiatives."
        },
        {
            "job_title": "Head of developers",
            "company": "BAU Cyprus University",
            "start_date": "01/07/2024",
            "end_date": "20/08/2024",
            "description": "Led team as Database manager, Fullstack developer, and team Leader. Developed comprehensive systems reducing stock discrepancies by 40% and decreasing expired medication waste by 35%. Integrated barcode/QR scanning reduces manual data entry time by 60%."
        }
    ],
    "education": [
        {
            "degree": "Bachelor of Computer Engineering",
            "institution": "Bahcesehir cyprus university (BAU)",
            "field_of_study": "Computer Engineering",
            "start_date": "21/09/2021",
            "end_date": "27/06/2025",
            "grade": "3.93/4.00",
            "honors": "First Class Honours (High Honour) - Valedictorian: Best graduating student"
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
            "name": "Pharmacy Inventory Management System",
            "description": "Built web-based system managing 200+ SKUs with real-time tracking and automated expiry alerts. Reduced stock discrepancies by 40% and decreased expired medication waste by 35%. Integrated barcode/QR scanning reduces manual data entry time by 60%.",
            "technologies": ["Python Flask", "PostgreSQL", "QR Integration"]
        },
        {
            "name": "TrustBridge SL",
            "description": "Revolutionary dual-platform combining AI-powered CV optimization and intelligent job matching with blockchain-verified investment ecosystem. Leverages OpenAI for intelligent career services, Solana blockchain for immutable verification.",
            "technologies": ["FastAPI", "OpenAI API", "Solana", "Next.js", "TypeScript"]
        }
    ],
    "awards": [
        {
            "name": "Valedictorian",
            "issuer": "BAU Cyprus University",
            "date": "27/06/2025",
            "description": "Best graduating student for the entire university"
        }
    ]
}

# Test the ATS engine
engine = get_ats_engine()
result = engine.calculate_ats_score(test_cv_data)

print("=" * 80)
print("ATS SCORING TEST RESULTS")
print("=" * 80)
print(f"\nFinal Score: {result['ats_score']}/100 (Grade: {result['ats_grade']})")
print(f"CV Hash: {result['cv_hash'][:16]}...")

print("\n" + "=" * 80)
print("COMPONENT SCORES")
print("=" * 80)
for component, score in result['component_scores'].items():
    detail = result['component_details'].get(component, {})
    rationale = detail.get('rationale', '')
    print(f"\n{component.replace('_', ' ').title()}: {score}/100")
    if rationale:
        print(f"  → {rationale}")
    
    # Show additional details
    if component == 'keyword_match':
        kw_count = detail.get('keyword_count', 0)
        matched = detail.get('matched_keywords', [])
        print(f"  → Found {kw_count} technical keywords: {', '.join(matched[:5])}")
    elif component == 'experience_quality':
        action_verbs = detail.get('action_verbs_count', 0)
        detailed = detail.get('detailed_descriptions', 0)
        entries = detail.get('experience_entries', 0)
        print(f"  → {entries} roles, {action_verbs} with action verbs, {detailed} detailed descriptions")
    elif component == 'completeness':
        exp_present = detail.get('experience_present', False)
        edu_present = detail.get('education_present', False)
        skills_present = detail.get('skills_present', False)
        contact_complete = detail.get('contact_complete', False)
        print(f"  → Experience: {'✓' if exp_present else '✗'}, Education: {'✓' if edu_present else '✗'}, Skills: {'✓' if skills_present else '✗'}, Contact: {'✓' if contact_complete else '✗'}")

print("\n" + "=" * 80)
print("ISSUES FOUND")
print("=" * 80)
for issue in result['ats_issues']:
    severity_icon = "🔴" if issue['severity'] == 'critical' else "⚠️"
    print(f"{severity_icon} [{issue['category'].upper()}] {issue['message']}")

print("\n" + "=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)
for i, rec in enumerate(result['ats_recommendations'], 1):
    print(f"{i}. {rec}")

print("\n" + "=" * 80)
