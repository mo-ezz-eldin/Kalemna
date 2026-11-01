from prometheus_fastapi_instrumentator import Instrumentator

def setup_instrumentator() -> Instrumentator:
    return Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=False,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics", "/docs", "/openapi.json"]
    )