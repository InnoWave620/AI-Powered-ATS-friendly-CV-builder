from keyword_extraction import extract_keywords
import re
from difflib import SequenceMatcher

def similarity(a, b):
    """Calculate similarity between two strings"""
    return SequenceMatcher(None, a, b).ratio()

def match_keywords(resume_text, job_description):
    """Enhanced keyword matching with weighted scoring and partial matches"""
    resume_words = extract_keywords(resume_text)
    job_words = extract_keywords(job_description)

    print("🔹 Extracted Resume Keywords:", len(resume_words), "keywords")
    print("🔹 Extracted Job Description Keywords:", len(job_words), "keywords")

    # Direct matches
    exact_matches = resume_words.intersection(job_words)
    
    # Partial matches (similarity >= 0.8)
    partial_matches = set()
    for job_word in job_words:
        if job_word not in exact_matches:
            for resume_word in resume_words:
                if similarity(job_word, resume_word) >= 0.8:
                    partial_matches.add((job_word, resume_word))
                    break
    
    # Synonym/related term matches
    synonym_matches = set()
    synonym_map = {
        'javascript': ['js', 'ecmascript'],
        'python': ['py'],
        'artificial intelligence': ['ai', 'machine learning', 'ml'],
        'machine learning': ['ml', 'ai', 'artificial intelligence'],
        'database': ['db', 'sql', 'mysql', 'postgresql'],
        'frontend': ['front-end', 'front end', 'ui', 'user interface'],
        'backend': ['back-end', 'back end', 'server-side'],
        'devops': ['dev ops', 'development operations'],
        'ci/cd': ['continuous integration', 'continuous deployment'],
        'agile': ['scrum', 'kanban'],
        'leadership': ['management', 'team lead', 'supervisor'],
        'communication': ['interpersonal', 'collaboration'],
        'problem solving': ['analytical', 'troubleshooting'],
    }
    
    for job_word in job_words:
        if job_word not in exact_matches:
            # Check if job word has synonyms in resume
            if job_word in synonym_map:
                for synonym in synonym_map[job_word]:
                    if synonym in resume_words:
                        synonym_matches.add((job_word, synonym))
                        break
            
            # Check if resume words are synonyms of job word
            for resume_word in resume_words:
                if resume_word in synonym_map and job_word in synonym_map[resume_word]:
                    synonym_matches.add((job_word, resume_word))
                    break
    
    # Calculate realistic weighted score
    total_job_keywords = len(job_words)
    if total_job_keywords == 0:
        return 0, set(), []
    
    # More generous scoring weights
    exact_weight = 2.0  # Increased weight for exact matches
    partial_weight = 1.5  # Increased weight for partial matches
    synonym_weight = 1.0  # Increased weight for synonym matches
    
    # Calculate raw score
    raw_score = (
        len(exact_matches) * exact_weight +
        len(partial_matches) * partial_weight +
        len(synonym_matches) * synonym_weight
    )
    
    # Use a more achievable scoring formula
    # Focus on match quality rather than total coverage
    total_matches = len(exact_matches) + len(partial_matches) + len(synonym_matches)
    
    # Base score calculation - more generous
    if total_job_keywords <= 50:
        # For smaller keyword sets, use traditional percentage
        base_score = min(100, int((raw_score / total_job_keywords) * 100))
    else:
        # For larger keyword sets, use a more achievable formula
        # Focus on having good coverage of the most important terms
        coverage_ratio = total_matches / total_job_keywords
        if coverage_ratio >= 0.4:  # 40%+ coverage is excellent for large sets
            base_score = 85 + min(15, int((coverage_ratio - 0.4) * 50))
        elif coverage_ratio >= 0.3:  # 30%+ coverage is very good
            base_score = 75 + int((coverage_ratio - 0.3) * 100)
        elif coverage_ratio >= 0.2:  # 20%+ coverage is good
            base_score = 60 + int((coverage_ratio - 0.2) * 150)
        else:
            base_score = int(coverage_ratio * 300)  # Below 20% gets lower scores
    
    # Quality bonus for having many exact matches
    quality_bonus = 0
    if len(exact_matches) >= 20:
        quality_bonus = 10
    elif len(exact_matches) >= 15:
        quality_bonus = 7
    elif len(exact_matches) >= 10:
        quality_bonus = 5
    elif len(exact_matches) >= 5:
        quality_bonus = 3
    
    final_score = min(100, base_score + quality_bonus)
    
    # Combine all matches for reporting
    all_matches = exact_matches.copy()
    for partial_match in partial_matches:
        all_matches.add(f"{partial_match[0]} (~{partial_match[1]})")
    for synonym_match in synonym_matches:
        all_matches.add(f"{synonym_match[0]} (≈{synonym_match[1]})")
    
    # Calculate missing keywords (only those without any match)
    matched_job_words = exact_matches.copy()
    matched_job_words.update([pm[0] for pm in partial_matches])
    matched_job_words.update([sm[0] for sm in synonym_matches])
    
    missing_keywords = job_words - matched_job_words
    missing_keywords_list = list(missing_keywords)[:15]  # Reduced to focus on most critical
    
    print("✅ Exact Matches:", len(exact_matches))
    print("🔸 Partial Matches:", len(partial_matches))
    print("🔗 Synonym Matches:", len(synonym_matches))
    print("❌ Missing Keywords:", len(missing_keywords))
    print("🎯 Final ATS Score:", final_score)
    
    return final_score, all_matches, missing_keywords_list