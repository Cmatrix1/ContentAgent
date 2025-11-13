SUPPORTED_PLATFORMS = ["linkedin", "youtube", "instagram"]


def get_default_platforms() -> list[str]:
    """
    Return a copy of the default platforms list.

    The copy prevents accidental mutations of the module-level constant when
    Django evaluates model field defaults.
    """
    return SUPPORTED_PLATFORMS.copy()


