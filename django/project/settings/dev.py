import mimetypes

from .base import *

if DEBUG:
    mimetypes.add_type("application/javascript", ".js", True)

DEBUG_TOOLBAR_CONFIG = {
    'RESULTS_CACHE_SIZE': 3,
    'SQL_WARNING_THRESHOLD': 100,
    'SHOW_TOOLBAR_CALLBACK': lambda request: True
}
