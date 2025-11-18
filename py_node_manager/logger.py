import logging


# Custom log formatter to add colors for different log levels and show line numbers
class ColoredFormatter(logging.Formatter):
    """Custom log formatter to add colors for different log levels and show line numbers"""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',  # cyan
        'INFO': '\033[32m',  # green
        'WARNING': '\033[33m',  # yellow
        'ERROR': '\033[31m',  # red
        'CRITICAL': '\033[35m',  # purple
        'RESET': '\033[0m',  # reset
    }

    def format(self, record: logging.LogRecord) -> str:
        # Obtain the color corresponding to the log level
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']

        # Add color to log level
        record.levelname = f'{log_color}{record.levelname}{reset_color}'

        # Call the format method of the parent class
        return super().format(record)


def get_logger(logger: logging.Logger) -> logging.Logger:
    """
    Configure and return a custom logger with a specific format and color scheme

    Args:
        logger (logging.Logger): The logger to configure.

    Returns:
        logging.Logger: The configured logger.
    """
    # Configure the logger
    logger.setLevel(logging.INFO)

    # Create console processor
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create formatter with function name before line number
    formatter = ColoredFormatter('%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d | %(message)s')
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    return logger
