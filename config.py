import os

class Config:
    SECRET_KEY = 'B0mb3r0s.*2024'  
    SQLALCHEMY_DATABASE_URI = 'sqlite:///intranet.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de Google reCAPTCHA
    RECAPTCHA_PUBLIC_KEY = '6LcXTWgsAAAAADYMtR_MCxnrzF909RefEBV-mAzD'
    RECAPTCHA_PRIVATE_KEY = '6LcXTWgsAAAAADgamAp2vC_fWLAjCa7IvsAoD3TO'
