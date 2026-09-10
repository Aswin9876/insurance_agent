"""Pytest fixtures and path setup."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))


@pytest.fixture
def sample_customer():
    """A valid customer payload matching synthetic data (existing CRM)."""
    return {
        "first_name": "Aarav", "last_name": "Sharma",
        "email": "aarav.sharma1@example.com", "phone": "+1-555-555-1234",
        "age": 34, "gender": "male", "location": "Austin, TX",
        "occupation": "software_engineer", "annual_income": 85000,
        "marital_status": "married", "health_conditions": "asthma",
        "smoker": "no", "insurance_needs": "health,life",
        "budget": 9000, "consent_given": True,
    }


@pytest.fixture
def invalid_customer():
    return {
        "first_name": "", "age": 12, "email": "not-an-email",
        "phone": "123", "annual_income": -5,
        "insurance_needs": "", "gender": "", "location": "",
        "occupation": "", "marital_status": "",
    }