def convert_bool(s, rtype):
    """
    Returns:
        rtype=str: 'true' or 'false'
        type=bool: true or false
    """
    if rtype not in (str, bool):
        raise ValueError(f"Invalid return type: {rtype}")
    if (isinstance(s, str) and s.lower() == "true") or s is True:
        if rtype == str:
            return "true"
        return True
    if (isinstance(s, str) and s.lower() == "false") or s is False:
        if rtype == str:
            return "false"
        return False
    raise ValueError(f"Invalid boolean string: {s}")
