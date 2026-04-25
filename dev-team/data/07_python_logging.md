# Python logging Module

## Basic Usage
```python
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename='myapp.log', level=logging.INFO)

logger.info('Application started')
logger.warning('This is a warning')
logger.error('An error occurred')
```

## Logging Levels

| Level | Value | Purpose |
|-------|-------|---------|
| `DEBUG` | 10 | Detailed diagnostic info |
| `INFO` | 20 | Confirmation of normal operation |
| `WARNING` | 30 | Unexpected event or problem |
| `ERROR` | 40 | Serious problem, function failed |
| `CRITICAL` | 50 | Program may not continue |

## Logger Objects
```python
logger = logging.getLogger(__name__)  # Recommended

logger.debug(msg, *args)
logger.info(msg, *args)
logger.warning(msg, *args)
logger.error(msg, *args)
logger.critical(msg, *args)
logger.exception(msg, *args)  # Logs with exception info

logger.setLevel(logging.DEBUG)
logger.addHandler(handler)
```

## Handlers
```python
handler = logging.StreamHandler()          # Console
handler = logging.FileHandler('app.log')   # File

handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
logger.addHandler(handler)
```

## Formatters
```python
formatter = logging.Formatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
```

### Common LogRecord Attributes

| Attribute | Format | Description |
|-----------|--------|-------------|
| `asctime` | `%(asctime)s` | Human-readable time |
| `levelname` | `%(levelname)s` | Level name |
| `message` | `%(message)s` | The logged message |
| `name` | `%(name)s` | Logger name |
| `filename` | `%(filename)s` | Source filename |
| `lineno` | `%(lineno)d` | Source line number |
| `funcName` | `%(funcName)s` | Function name |

## Configuration with basicConfig()
```python
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8',
)
```

## Filters
```python
class ContextFilter(logging.Filter):
    def filter(self, record):
        record.user = 'username'
        return True  # Log it, False to skip
```

## Complete Example
```python
import logging

logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

file_handler = logging.FileHandler('app.log')
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger.addHandler(file_handler)
```

The logging module is thread-safe by default.
