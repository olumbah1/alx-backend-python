#!/usr/bin/env python3
def access_nested_map(nested_map, path):
    """
    Access a value in a nested dictionary using a tuple path.

    Args:
        nested_map (dict): A dictionary that may contain nested dictionaries.
        path (tuple): A sequence of keys representing the path to the desired value.

    Returns:
        The value found at the end of the path.

    Raises:
        KeyError: If any key in the path is not found in the current level of the dictionary.
    """
    # for key in path:
    #     nested_map = nested_map[key]
    # return nested_map

def access_nested_map(nested_map, path):
    for key in path:
        if not isinstance(nested_map, dict):
            raise KeyError(key)
        nested_map = nested_map[key]
    return nested_map
