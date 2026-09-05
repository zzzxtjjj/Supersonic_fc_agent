def match_metadata(
    metadata: dict,
    filters: dict
) -> bool:

    for key, expected_value in filters.items():
        actual_value = metadata.get(key)

        if expected_value != actual_value:
            return False

    return True
