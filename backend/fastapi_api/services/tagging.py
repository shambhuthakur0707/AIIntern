def tag_role(title: str, description: str = "") -> str:
    text = f"{title} {description}".lower()

    ai_keywords = ["machine learning", "deep learning", "nlp", "ai", "computer vision"]
    web_keywords = ["frontend", "backend", "full stack", "react", "django", "flask", "web"]
    data_keywords = ["data science", "data analyst", "data engineering", "sql", "pandas"]

    if any(k in text for k in ai_keywords):
        return "AI"
    if any(k in text for k in web_keywords):
        return "Web Dev"
    if any(k in text for k in data_keywords):
        return "Data Science"
    return "General"
