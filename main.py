import logging

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("Hello from user_service!")


if __name__ == "__main__":
    main()
