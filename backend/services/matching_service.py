def match_internships_logic(user_profile):
    try:
        # Extract user skills
        user_skills = user_profile.get("skills", [])

        # 👉 CALL YOUR EXISTING TF-IDF / ML FUNCTION HERE
        # Replace this with your real function
        matched_roles = run_tfidf_matching(user_skills)

        # Calculate missing skills
        missing_skills = calculate_skill_gaps(user_skills, matched_roles)

        return {
            "success": True,
            "data": {
                "matched_roles": matched_roles,
                "missing_skills": missing_skills
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }