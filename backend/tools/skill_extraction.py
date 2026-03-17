"""
Centralized skill extraction utility for all scrapers.
Uses comprehensive skill catalog with regex word-boundary matching.
"""

import re
import logging
from typing import List, Set

logger = logging.getLogger(__name__)

# ── Comprehensive skill catalog organized by category ──────────────────
COMPREHENSIVE_SKILLS = {
    # Programming Languages
    "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust",
    "PHP", "Ruby", "Swift", "Kotlin", "Scala", "Objective-C", "R", "MATLAB",
    "VB.NET", "Perl", "Haskell", "Elixir", "Clojure", "Groovy", "Lua",
    
    # Web Frameworks & Frontend
    "React", "Vue.js", "Angular", "Next.js", "Svelte", "Ember.js", "Nuxt.js",
    "HTML", "CSS", "Sass", "LESS", "Tailwind", "Bootstrap", "Material Design",
    "jQuery", "AJAX", "GraphQL", "REST API", "WebSocket",
    
    # Backend Frameworks
    "Node.js", "Express.js", "Django", "Flask", "FastAPI", "Spring Boot",
    "Laravel", "Symfony", "Rails", "ASP.NET", "Asp.NET Core", "Fastify",
    "NestJS", "Koa", "Hapi", "Sinatra",
    
    # Databases
    "SQL", "MongoDB", "PostgreSQL", "MySQL", "Redis", "Firebase", "DynamoDB",
    "Cassandra", "Oracle", "SQLServer", "MariaDB", "Elasticsearch", "Neo4j",
    "CouchDB", "DuckDB", "Snowflake", "BigQuery", "Memcached",
    
    # Data Science & ML
    "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "Pandas", "NumPy",
    "SciPy", "Matplotlib", "Seaborn", "Plotly", "Bokeh", "XGBoost",
    "LightGBM", "CatBoost", "Hugging Face", "OpenAI", "Anthropic",
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
    "LLMs", "Transformers", "BERT", "GPT",
    
    # DevOps & Cloud
    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Google Cloud",
    "Heroku", "DigitalOcean", "Linode", "Terraform", "Ansible", "Jenkins",
    "GitLab CI", "GitHub Actions", "CircleCI", "Travis CI", "ArgoCD",
    "ECS", "EKS", "EC2", "S3", "Lambda", "CloudFormation", "Helm",
    
    # Big Data & Streaming
    "Apache Spark", "Spark", "Hadoop", "Kafka", "Flink", "Storm",
    "Databricks", "Hive", "Pig", "MapReduce", "Apache Beam",
    
    # Version Control & Collaboration
    "Git", "GitHub", "GitLab", "Bitbucket", "Mercurial", "SVN",
    
    # Testing & QA
    "Jest", "Mocha", "Pytest", "Unittest", "RSpec", "Selenium", "Cypress",
    "Playwright", "TestNG", "JUnit", "PHPUnit", "Jasmine", "Karma",
    
    # Mobile Development
    "React Native", "Flutter", "Swift", "Kotlin", "Android", "iOS",
    "Ionic", "NativeScript", "Xamarin", "Cordova",
    
    # Linux & System Administration
    "Linux", "Unix", "Bash", "Shell", "Docker", "Kubernetes", "AWS",
    "Networking", "TCP/IP", "DNS", "Load Balancing",
    
    # Other Technologies
    "Linux", "Windows", "macOS", "API", "Microservices", "Blockchain",
    "Solidity", "Web3", "Ethereum", "Smart Contracts", "Cybersecurity",
    "Penetration Testing", "OWASP", "SSL/TLS", "OAuth", "JWT",
    "Message Queues", "RabbitMQ", "ActiveMQ", "Messaging",
    "gRPC", "Protocol Buffers", "XML", "JSON", "YAML", "TOML",
    
    # Design & UI/UX
    "Figma", "Adobe XD", "Sketch", "InVision", "UI Design", "UX Design",
    "Wireframing", "Prototyping", "User Research", "Accessibility",
    
    # Project Management & Soft Skills
    "Agile", "Scrum", "Kanban", "JIRA", "Confluence", "Leadership",
    "Communication", "Problem Solving", "Team Collaboration",
    
    # BI & Analytics
    "Tableau", "Power BI", "Looker", "Qlik", "Datadog", "New Relic",
    "Grafana", "Prometheus", "BI", "Analytics", "Data Warehouse",
    
    # CMS & Platforms
    "WordPress", "Shopify", "Magento", "Drupal", "Joomla", "Ghost",
    "Strapi", "Contentful", "Sanity",
    
    # Popular Libraries & Tools
    "NumPy", "Pandas", "Scikit-learn", "Requests", "Beautiful Soup",
    "Playwright", "Puppeteer", "Lodash", "Moment.js", "D3.js", "Three.js",
    "Webpack", "Vite", "Parcel", "Gulp", "Grunt", "npm", "Yarn", "pnpm",
    "pip", "Poetry", "Conda", "Maven", "Gradle", "Cargo",
    
    # Database ORMs & Query Builders
    "SQLAlchemy", "Sequelize", "TypeORM", "MikroORM", "Prisma",
    "Hibernate", "Entity Framework", "Doctrine", "Eloquent",
    
    # Additional Methodologies
    "Continuous Integration", "Continuous Deployment", "CI/CD",
    "DevOps", "SRE", "Infrastructure as Code", "IaC",
    "Logging", "Monitoring", "Observability", "Tracing", "APM",
}

# ── Skill variations mapping (to normalize different spellings) ────────────
SKILL_VARIATIONS = {
    "javascript": ["js"],
    "typescript": ["ts"],
    "react": ["reactjs"],
    "vue": ["vue.js"],
    "angular": ["angularjs"],
    "node": ["node.js", "nodejs"],
    "dotnet": ["asp.net", "asp.net core", ".net", ".net core"],
    "postgres": ["postgresql"],
    "mongo": ["mongodb"],
    "django": ["djangoproject"],
    "flask": ["python flask"],
    "kubernetes": ["k8s"],
    "docker": ["containerization", "containers"],
    "aws": ["amazon web services"],
    "gcp": ["google cloud", "google cloud platform"],
    "azure": ["microsoft azure"],
    "python": ["py"],
}

def _normalize_skill(skill: str) -> str:
    """Normalize skill name to lowercase and remove extra spaces."""
    return skill.strip().lower()

def extract_skills_from_text(text: str, include_variations: bool = True) -> List[str]:
    """
    Extract all recognized skills from job description text.
    Uses regex word-boundary matching to avoid partial matches.
    
    Args:
        text: Job description text to analyze
        include_variations: If True, normalize skill variations (e.g., js → javascript)
    
    Returns:
        List of found skills (no duplicates, case-preserved from catalog)
    """
    if not text or not text.strip():
        return []
    
    normalized_text = f" {text.lower()} "
    found_skills: Set[str] = set()
    
    # Build a mapping of lowercase skills to their catalog form
    catalog_map = {_normalize_skill(skill): skill for skill in COMPREHENSIVE_SKILLS}
    
    # Add variations if enabled
    if include_variations:
        for canonical, variations in SKILL_VARIATIONS.items():
            for variation in variations:
                catalog_map[_normalize_skill(variation)] = catalog_map.get(canonical, canonical.title())
    
    # Search for each skill with word boundaries
    for skill_lower in sorted(catalog_map.keys(), key=len, reverse=True):
        # Regex pattern: word boundary + skill + word boundary
        # Case-insensitive search
        pattern = rf"(?<![a-z0-9.]){re.escape(skill_lower)}(?![a-z0-9])"
        
        if re.search(pattern, normalized_text):
            # Add the properly-cased skill from catalog
            found_skills.add(catalog_map[skill_lower])
    
    return sorted(list(found_skills))

def extract_skills_from_title_and_description(title: str, description: str) -> List[str]:
    """
    Extract skills from both job title and description.
    Prioritizes skills found in title.
    
    Args:
        title: Job title
        description: Job description
    
    Returns:
        List of found skills
    """
    # Extract from title first (higher priority)
    title_skills = set(extract_skills_from_text(title or ""))
    
    # Extract from description
    desc_skills = set(extract_skills_from_text(description or ""))
    
    # Combine and sort
    all_skills = sorted(list(title_skills | desc_skills))
    
    return all_skills

def get_skill_catalog() -> Set[str]:
    """Return the full skill catalog."""
    return COMPREHENSIVE_SKILLS.copy()
