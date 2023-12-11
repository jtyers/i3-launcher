import logging

import i3ipc
import inject

from .config import Config


logger = logging.getLogger(__name__)


def configure_injector(config: Config, connection: i3ipc.Connection):
    def __configure__(binder: inject.Binder):
        binder.bind(Config, config)
        binder.bind(i3ipc.Connection, connection)

    inject.configure(__configure__)
