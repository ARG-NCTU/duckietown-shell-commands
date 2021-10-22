DEFAULT_INDEX_URL = "https://pypi.org/simple"


def get_pip_index_url() -> str:
    pip_index_url = os.environ.get("PIP_INDEX_URL", DEFAULT_INDEX_URL)
    if pip_index_url != DEFAULT_INDEX_URL:
        dtslogger.warning(f"Using custom PIP_INDEX_URL='{pip_index_url}'.")
    return pip_index_url
