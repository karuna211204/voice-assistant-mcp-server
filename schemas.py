# schemas.py

from pydantic import BaseModel

class AppointmentRequest(BaseModel):
    patient_name: str
    age: int
    gender: str
    phone_number: str
    issue: str
    

class SmsNotifyRequest(BaseModel):
    phone_number: str
    patient_name: str
    appointment_time: str

class HealthRecordRequest(BaseModel):
    patient_name: str
    age: int
    gender: str
    phone_number: str
    symptoms: str
    duration: str
    chronic_conditions: str
    family_history: str
    diagnosis: str
    prescriptions: str
