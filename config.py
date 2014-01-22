import os
CSRF_ENABLED = True
SECRET_KEY = '!QAZ123#WSX0456edc'
if os.environ.get('DATABASE_URL') is None:
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://rigbe:Keyboard10@localhost/fastmonkey'
else:
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
