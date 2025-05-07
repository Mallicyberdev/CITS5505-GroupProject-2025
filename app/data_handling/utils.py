def validate_content(content: str) -> tuple[bool, str]:
    """Validate diary content
    Returns (is_valid, message)
    """
    if not content:
        return False, "Content cannot be empty"
    
    if len(content) > 50000:  # Example limit
        return False, "Content exceeds maximum length"
        
    return True, "Content is valid"