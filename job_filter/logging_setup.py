import logging

_CONFIGURED = False


def setup_logging(level: int = logging.INFO) -> None:
    """Единая настройка логирования (идемпотентна)."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    _CONFIGURED = True

