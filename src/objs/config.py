from decouple import config

class Config:
    CONNECTION_STRING = config('CONNECTION_STRING')

class DevelopmentConfig(Config):
    DEBUG = config('DEBUG', cast=bool)