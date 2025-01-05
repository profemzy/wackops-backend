def str_to_bool(value: str) -> bool:
    """Convert string to boolean, accepting various truth values."""
    value = value.lower()
    true_values = ("true", "1", "yes", "on", "t")
    false_values = ("false", "0", "no", "off", "f")

    if value in true_values:
        return True
    elif value in false_values:
        return False
    else:
        raise ValueError(f"Invalid boolean value: {value}")
