"""
seed.py — Database Seeder
Run once to populate MongoDB with realistic internship listings and sample users.
Usage:  python seed.py
"""
import sys
import os
import bcrypt
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "aiintern_db")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]


INTERNSHIPS = [
    {
        "title": "Machine Learning Engineer Intern",
        "company": "DeepMind Labs",
        "required_skills": ["Python", "TensorFlow", "PyTorch", "Deep Learning", "NumPy", "Pandas"],
        "description": "Work on cutting-edge deep learning models for natural language understanding and computer vision. You will assist senior researchers in designing, training, and evaluating neural network architectures on large-scale datasets.",
        "domain": "Machine Learning",
        "stipend": "₹25,000/month",
        "duration": "6 months",
        "location": "Bangalore (Hybrid)",
        "openings": 3,
    },
    {
        "title": "Data Science Intern",
        "company": "Analytics Nexus",
        "required_skills": ["Python", "SQL", "Pandas", "Data Analysis", "Scikit-learn", "Matplotlib"],
        "description": "Perform exploratory data analysis and build predictive models for business intelligence use cases. Work with structured datasets across e-commerce and fintech verticals.",
        "domain": "Data Science",
        "stipend": "₹18,000/month",
        "duration": "3 months",
        "location": "Remote",
        "openings": 5,
    },
    {
        "title": "Full Stack Web Developer Intern",
        "company": "StartupHub Technologies",
        "required_skills": ["React", "Node.js", "MongoDB", "REST API", "JavaScript", "CSS"],
        "description": "Build and maintain scalable web applications. You will work on both frontend (React) and backend (Node/Express) of the company's SaaS platform serving 10,000+ users.",
        "domain": "Web Development",
        "stipend": "₹15,000/month",
        "duration": "4 months",
        "location": "Pune (On-site)",
        "openings": 4,
    },
    {
        "title": "NLP Research Intern",
        "company": "Cognitive AI Research Institute",
        "required_skills": ["Python", "NLP", "Transformers", "Hugging Face", "PyTorch", "BERT"],
        "description": "Contribute to research in conversational AI and information extraction. Implement and fine-tune transformer models on domain-specific text corpora.",
        "domain": "Natural Language Processing",
        "stipend": "₹20,000/month",
        "duration": "6 months",
        "location": "IIT Delhi Campus",
        "openings": 2,
    },
    {
        "title": "DevOps & Cloud Intern",
        "company": "CloudStack Solutions",
        "required_skills": ["Docker", "Kubernetes", "AWS", "CI/CD", "Linux", "Git", "Terraform"],
        "description": "Automate infrastructure provisioning, manage CI/CD pipelines, and monitor cloud-native applications running on AWS EKS. Collaborate with product and SRE teams.",
        "domain": "DevOps",
        "stipend": "₹20,000/month",
        "duration": "3 months",
        "location": "Remote",
        "openings": 3,
    },
    {
        "title": "Computer Vision Intern",
        "company": "Visera Technologies",
        "required_skills": ["Python", "OpenCV", "PyTorch", "Computer Vision", "NumPy", "Deep Learning"],
        "description": "Build real-time object detection and image segmentation pipelines for autonomous vehicle perception. Work on data augmentation, model optimization, and edge deployment.",
        "domain": "Machine Learning",
        "stipend": "₹22,000/month",
        "duration": "5 months",
        "location": "Chennai (Hybrid)",
        "openings": 2,
    },
    {
        "title": "Cybersecurity Analyst Intern",
        "company": "SecureNet Corp",
        "required_skills": ["Cybersecurity", "Python", "Linux", "Network Security", "SIEM", "Penetration Testing"],
        "description": "Assist in vulnerability assessments, security audits, and threat detection for enterprise clients. Analyze security logs and implement defensive countermeasures.",
        "domain": "Cybersecurity",
        "stipend": "₹16,000/month",
        "duration": "3 months",
        "location": "Hyderabad (On-site)",
        "openings": 4,
    },
    {
        "title": "Android App Developer Intern",
        "company": "MobileFirst Studios",
        "required_skills": ["Java", "Kotlin", "Android", "REST API", "Firebase", "Git"],
        "description": "Design and develop Android features for a productivity app with 500K+ downloads. Implement new API integrations, optimize app performance, and write unit tests.",
        "domain": "Mobile Development",
        "stipend": "₹14,000/month",
        "duration": "3 months",
        "location": "Remote",
        "openings": 6,
    },
    {
        "title": "Data Engineering Intern",
        "company": "PipelineX Analytics",
        "required_skills": ["Python", "Apache Spark", "SQL", "ETL", "AWS", "Airflow", "Kafka"],
        "description": "Build robust data pipelines to ingest, transform, and load terabytes of event data daily. Work on data lakehouse architecture using AWS S3 and Apache Spark.",
        "domain": "Data Engineering",
        "stipend": "₹21,000/month",
        "duration": "4 months",
        "location": "Bangalore (Hybrid)",
        "openings": 3,
    },
    {
        "title": "AI Product Intern",
        "company": "FutureLab AI",
        "required_skills": ["Python", "Machine Learning", "Product Management", "Data Analysis", "SQL", "Communication"],
        "description": "Bridge AI research and product development. Analyze user data, define ML feature requirements, run A/B tests, and work directly with ML engineers to ship AI-powered features.",
        "domain": "AI / Product",
        "stipend": "₹17,000/month",
        "duration": "3 months",
        "location": "Remote",
        "openings": 2,
    },
]


SAMPLE_USERS = [
    {
        "name": "Aryan Sharma",
        "email": "aryan@example.com",
        "password_hash": bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode(),
        "skills": ["Python", "Machine Learning", "Pandas", "NumPy", "Scikit-learn", "SQL"],
        "interests": ["Machine Learning", "Data Science", "AI Research"],
        "experience_level": "intermediate",
        "education": "B.Tech Computer Science, IIT Roorkee (3rd Year)",
        "last_match_result": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    {
        "name": "Priya Singh",
        "email": "priya@example.com",
        "password_hash": bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode(),
        "skills": ["JavaScript", "React", "Node.js", "HTML", "CSS", "Git"],
        "interests": ["Web Development", "Full Stack", "UI/UX"],
        "experience_level": "beginner",
        "education": "B.E. Information Technology, VIT Vellore (2nd Year)",
        "last_match_result": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
]


def seed():
    # Clear existing data
    db.internships.delete_many({})
    db.users.delete_many({})

    # Insert internships
    intern_result = db.internships.insert_many(INTERNSHIPS)
    print(f"✅ Seeded {len(intern_result.inserted_ids)} internships")

    # Insert users
    user_result = db.users.insert_many(SAMPLE_USERS)
    print(f"✅ Seeded {len(user_result.inserted_ids)} sample users")

    print("\n📧 Sample login credentials:")
    print("   Email: aryan@example.com    | Password: password123")
    print("   Email: priya@example.com    | Password: password123")
    print("\n🚀 Seed complete! Run 'python app.py' to start the backend.")


if __name__ == "__main__":
    seed()
