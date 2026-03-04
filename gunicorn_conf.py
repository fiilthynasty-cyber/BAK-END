import os
bind = "0.0.0.0:" + (os.environ.get("PORT") or "10000")
workers = 2
threads = 4
timeout = 120
graceful_timeout = 30
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = "info"

