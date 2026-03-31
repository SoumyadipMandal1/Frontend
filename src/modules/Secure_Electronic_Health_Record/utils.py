import streamlit as st
import random
import string
from datetime import datetime
from db import get_db

db = get_db()

def generate_ehr_id():
    return "EHR-" + "".join(random.choices(string.digits, k=6))

def generate_audit_id():
    return "LOG-" + "".join(random.choices(string.digits, k=6))

def log_audit(action, resource, status, reason=None):
    db.audit_logs.insert_one({
        "log_id":    generate_audit_id(),
        "timestamp": datetime.now().isoformat(),
        "user":      st.session_state.get("user_name", "unknown"),
        "user_id":   st.session_state.get("user_id", "unknown"),
        "role":      st.session_state.get("role", "unknown"),
        "action":    action,
        "resource":  resource,
        "status":    status,
        "reason":    reason
    })

def has_patient_granted_access(patient_user_id, doctor_user_id, ehr_id=None):
    base = {"patient_user_id": patient_user_id, "doctor_user_id": doctor_user_id, "status": "Granted"}
    broad = db.ehr_consent.find_one({**base, "$or": [{"ehr_id": {"$exists": False}}, {"ehr_id": "ALL"}]})
    if broad:
        return True
    if ehr_id:
        specific = db.ehr_consent.find_one({**base, "ehr_id": ehr_id})
        return specific is not None
    return False

SECURITY_POLICIES = [
    {"policy_id": "POL-001", "name": "Data Encryption at Rest",         "type": "Encryption", "compliance": ["HIPAA", "GDPR"],  "description": "All EHR data must be encrypted using AES-256 encryption at rest.",                                             "status": "Active"},
    {"policy_id": "POL-002", "name": "Access Logging & Monitoring",     "type": "Audit",      "compliance": ["HIPAA"],          "description": "All access to EHR records must be logged with user, timestamp, and action.",                                  "status": "Active"},
    {"policy_id": "POL-003", "name": "Patient Consent Required",        "type": "Access",     "compliance": ["HIPAA", "GDPR"],  "description": "No doctor may access a patient EHR without explicit patient consent except in emergencies.",                 "status": "Active"},
    {"policy_id": "POL-004", "name": "Break-Glass Emergency Access",    "type": "Access",     "compliance": ["HIPAA"],          "description": "Emergency access is permitted without consent but must be logged with reason for review.",                   "status": "Active"},
    {"policy_id": "POL-005", "name": "Data Retention Policy",           "type": "Storage",    "compliance": ["GDPR"],           "description": "EHR records must be retained for minimum 7 years. Deletion requires archiving first.",                       "status": "Active"},
    {"policy_id": "POL-006", "name": "Password & Authentication Policy","type": "Auth",       "compliance": ["ISO 27001"],      "description": "All user passwords must be hashed using bcrypt. Minimum 6 characters required.",                             "status": "Active"},
    {"policy_id": "POL-007", "name": "Data Masking for Sensitive Records","type": "Privacy",  "compliance": ["GDPR", "HIPAA"],  "description": "Sensitive fields like address and contact must be masked during emergency access.",                          "status": "Active"},
    {"policy_id": "POL-008", "name": "Local Healthcare Regulations",    "type": "Compliance", "compliance": ["Local"],          "description": "All data handling must comply with local healthcare data protection regulations.",                             "status": "Active"},
]
