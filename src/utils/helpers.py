"""Helper utilities for Archon."""

import re
from typing import Dict, Any, Optional


def format_response(response: str, max_length: int = 1000) -> str:
    """
    Format a response for display.
    
    Args:
        response: The response to format
        max_length: Maximum length before truncation
        
    Returns:
        Formatted response
    """
    if not response:
        return "No response available."
    
    # Truncate if too long
    if len(response) > max_length:
        response = response[:max_length] + "..."
    
    # Clean up formatting
    response = re.sub(r'\n+', '\n', response)  # Remove multiple newlines
    response = response.strip()
    
    return response


def validate_question(question: str) -> Dict[str, Any]:
    """
    Validate a user question.
    
    Args:
        question: The question to validate
        
    Returns:
        Validation result with status and message
    """
    if not question or not question.strip():
        return {
            "valid": False,
            "message": "Please provide a question."
        }
    
    if len(question.strip()) < 3:
        return {
            "valid": False,
            "message": "Question is too short. Please provide more details."
        }
    
    if len(question) > 1000:
        return {
            "valid": False,
            "message": "Question is too long. Please keep it under 1000 characters."
        }
    
    # Check for potentially problematic content
    suspicious_patterns = [
        r'password|secret|confidential',
        r'delete|remove|destroy',
        r'hack|crack|exploit'
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, question.lower()):
            return {
                "valid": False,
                "message": "Question contains potentially inappropriate content."
            }
    
    return {
        "valid": True,
        "message": "Question is valid."
    }


def extract_keywords(text: str) -> list:
    """
    Extract keywords from text.
    
    Args:
        text: Text to extract keywords from
        
    Returns:
        List of keywords
    """
    # Simple keyword extraction (in production, use more sophisticated methods)
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Remove common stop words
    stop_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
        'after', 'above', 'below', 'between', 'among', 'is', 'are', 'was',
        'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
        'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
        'can', 'this', 'that', 'these', 'those', 'a', 'an', 'as', 'if',
        'then', 'than', 'so', 'such', 'very', 'just', 'now', 'here', 'there'
    }
    
    keywords = [word for word in words if word not in stop_words]
    
    # Return unique keywords, sorted by frequency
    from collections import Counter
    word_counts = Counter(keywords)
    return [word for word, count in word_counts.most_common(10)]


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate simple similarity between two texts.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score between 0 and 1
    """
    # Simple Jaccard similarity
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    if len(union) == 0:
        return 0.0
    
    return len(intersection) / len(union)
