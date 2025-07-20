# mcp_server.py

import os
import json
import asyncio
import logging
from typing import Callable
from fastmcp import FastMCP
from pydantic import BaseModel
from openpyxl import Workbook, load_workbook
from datetime import datetime
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from twilio.rest import Client
from openpyxl.utils import get_column_letter
from schemas import AppointmentRequest, SmsNotifyRequest, HealthRecordRequest

# ----------- Environment Setup -----------
load_dotenv()
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
os.makedirs(desktop_path, exist_ok=True)
EXCEL_PATH = os.path.join(desktop_path, "appointments.xlsx")
PDF_PATH = os.path.join(desktop_path, "health_record.pdf")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
client = Client(twilio_sid, twilio_token)

# ----------- Logging -----------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ----------- Decorator to register tools -----------
tool_registry = []

def tool(func: Callable):
    tool_registry.append(func)
    return func

# ----------- Utility: Format number -----------
def format_mobile_number_e164(mobile_number, default_country_code="+91"):
    phone = mobile_number.strip().replace(" ", "").replace("-", "")
    if phone.startswith("+"):
        return phone
    if phone.startswith("0"):
        phone = phone[1:]
    if len(phone) == 10 and phone.isdigit():
        return f"{default_country_code}{phone}"
    if len(phone) == 12 and phone.isdigit():
        return f"+{phone}"
    if len(phone) == 11 and phone.startswith("91") and phone.isdigit():
        return f"+{phone}"
    raise ValueError(f"Invalid mobile number for E.164: {mobile_number}")

# ----------- Tool Functions with @tool decorator -----------

@tool
def queue_appointment(input: AppointmentRequest) -> dict:
    try:
        logger.info("Saving appointment to Excel...")
        if not os.path.exists(EXCEL_PATH):
            wb = Workbook()
            ws = wb.active
            ws.append([
                "Patient ID", "Name", "Age", "Gender", "Phone Number",
                "Issue", "Appointment Time", "Queued At"
            ])
            wb.save(EXCEL_PATH)
        wb = load_workbook(EXCEL_PATH)
        ws = wb.active
        ws.append([
            input.patient_id, input.patient_name, input.age, input.gender,
            input.phone_number, input.issue, input.appointment_time,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])
        column_widths = [14, 20, 6, 10, 16, 40, 20, 22]
        for i, width in enumerate(column_widths, start=1):
            ws.column_dimensions[get_column_letter(i)].width = width
        wb.save(EXCEL_PATH)
        logger.info(f"✅ Appointment saved at: {EXCEL_PATH}")
        return {
            "status": "success",
            "message": f"Patient {input.patient_name} queued successfully.",
            "path": os.path.abspath(EXCEL_PATH)
        }
    except Exception as e:
        logger.error(f"❌ Failed to save appointment: {e}")
        return {"status": "error", "message": str(e)}

@tool
def send_appointment_sms(input: SmsNotifyRequest) -> dict:
    try:
        logger.info("Sending SMS notification...")
        to_number = format_mobile_number_e164(input.phone_number)
        body = f"Hello {input.patient_name}, your appointment is scheduled at {input.appointment_time}."
        message = client.messages.create(
            body=body,
            from_=TWILIO_FROM_NUMBER,
            to=to_number
        )
        logger.info(f"✅ SMS sent to {to_number} (SID: {message.sid})")
        return {
            "status": "sent",
            "message": f"SMS sent to {to_number}",
            "sms": body,
            "sid": message.sid
        }
    except Exception as e:
        logger.error(f"❌ SMS sending failed: {e}")
        return {"status": "error", "message": str(e)}

@tool
def generate_health_record(input: HealthRecordRequest) -> dict:
    try:
        logger.info("Generating health record PDF...")
        c = canvas.Canvas(PDF_PATH, pagesize=letter)
        c.setFont("Helvetica", 12)
        y = 750
        line_gap = 20
        entries = [
            f"Patient Name: {input.patient_name}",
            f"Age: {input.age}",
            f"Gender: {input.gender}",
            f"Phone Number: {input.phone_number}",
            f"Symptoms: {input.symptoms}",
            f"Duration: {input.duration}",
            f"Chronic Conditions: {input.chronic_conditions}",
            f"Family History: {input.family_history}",
            f"Diagnosis: {input.diagnosis}",
            f"Prescriptions: {input.prescriptions}"
        ]
        for line in entries:
            c.drawString(30, y, line)
            y -= line_gap
        c.save()
        logger.info(f"✅ PDF generated at: {PDF_PATH}")
        return {
            "status": "success",
            "message": "Health record PDF generated successfully.",
            "path": os.path.abspath(PDF_PATH)
        }
    except Exception as e:
        logger.error(f"❌ Failed to generate PDF: {e}")
        return {"status": "error", "message": str(e)}

# ----------- MCP Init & Run -----------

mcp = FastMCP(
    name="AI-Health-Multilingual-Voice-agent",
    tools=tool_registry
)

if __name__ == "__main__":
    logger.info("🚀 Initializing MCP for AI-Health-Multilingual-Voice-agent...")
    logger.info(f"📂 Excel will be saved to: {EXCEL_PATH}")
    logger.info(f"📂 PDF will be saved to: {PDF_PATH}")
    tools = asyncio.run(mcp.get_tools())
    logger.info(f"📦 Total tools registered: {len(tools)}")
    for name, tool in tools.items():
        logger.info(f"🔧 Tool loaded: {name}")
    mcp.run(transport="sse", host="127.0.0.1", port=8000)
