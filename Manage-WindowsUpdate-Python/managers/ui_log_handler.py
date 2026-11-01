# managers/ui_log_handler.py

import logging


class UILogHandler(logging.Handler):

    def __init__(self, log_panel):

        super().__init__()

        self.log_panel = log_panel

    def emit(self, record):

        try:

            message = self.format(record)

            if record.levelno >= logging.ERROR:

                self.log_panel.error(
                    message
                )

            elif record.levelno >= logging.WARNING:

                self.log_panel.warning(
                    message
                )

            else:

                self.log_panel.info(
                    message
                )

        except Exception:
            pass
