DATABASE_ENGINE = 'postgresql_psycopg2'    # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'ado_mssql'.
DATABASE_NAME = 'another_hubplus'       # Or path to database file if using sqlite3.
DATABASE_USER = 'thehub'             # Not used with sqlite3.
DATABASE_PASSWORD = 'pwfth'         # Not used with sqlite3. 
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

SESSION_COOKIE_DOMAIN = None # ".the-hub.net"
HUBSPACE_COMPATIBLE = True
ROOT_URLCONF = 'hubplus.urls'

PROJECT_THEME='plus'
COPYRIGHT_HOLDER='HubWorld'

HMAC_KEY = "189261893294393751924178342983367596516"
