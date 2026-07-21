from django.conf import settings
from twilio.rest import Client
from datetime import datetime, timedelta, time
import requests
from .models import TimeSlot, SlotConfig, DayOff


def send_otp(phone, otp):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    message = client.messages.create(
        body=f"Your OTP is {otp}",
        from_=settings.TWILIO_PHONE_NUMBER,
        to=f"+91{phone}"
    )

    return message.sid


def generate_time_slots(start_time, end_time, slot_duration_minutes=30):
    """Generate list of (start, end) time tuples for given range"""
    slots = []
    current = datetime.combine(datetime.today(), start_time)
    end = datetime.combine(datetime.today(), end_time)

    while current + timedelta(minutes=slot_duration_minutes) <= end:
        slot_end = current + timedelta(minutes=slot_duration_minutes)
        slots.append((current.time(), slot_end.time()))
        current = slot_end

    return slots


def generate_slots_for_branch(branch, days_ahead=7):
    """
    Generate slots for a branch for the next X days.
    Uses SlotConfig for operating hours.
    Sunday (weekday=6) is off by default.
    """
    from django.db import IntegrityError

    today = datetime.now().date()
    created_count = 0

    # Get or create default slot configs for branch
    for weekday in range(7):
        config, created = SlotConfig.objects.get_or_create(
            branch=branch,
            weekday=weekday,
            defaults={
                'morning_start': time(6, 0),
                'morning_end': time(11, 30),
                'evening_start': time(16, 0),
                'evening_end': time(20, 0),
                'is_active': weekday != 6  # Sunday off by default
            }
        )

    for day_offset in range(days_ahead):
        target_date = today + timedelta(days=day_offset)
        weekday = target_date.weekday()

        # Check if day is marked as off
        if DayOff.objects.filter(branch=branch, date=target_date).exists():
            continue

        # Get config for this weekday
        try:
            config = SlotConfig.objects.get(branch=branch, weekday=weekday)
            if not config.is_active:
                continue
        except SlotConfig.DoesNotExist:
            continue

        # Generate morning slots
        morning_slots = generate_time_slots(config.morning_start, config.morning_end)
        for start, end in morning_slots:
            try:
                TimeSlot.objects.get_or_create(
                    branch=branch,
                    date=target_date,
                    start_time=start,
                    defaults={'end_time': end, 'status': 'AVAILABLE'}
                )
                created_count += 1
            except IntegrityError:
                pass

        # Generate evening slots
        evening_slots = generate_time_slots(config.evening_start, config.evening_end)
        for start, end in evening_slots:
            try:
                TimeSlot.objects.get_or_create(
                    branch=branch,
                    date=target_date,
                    start_time=start,
                    defaults={'end_time': end, 'status': 'AVAILABLE'}
                )
                created_count += 1
            except IntegrityError:
                pass

    return created_count


def fetch_bca_from_activex(phone_number, date=None):
    """
    Fetch BCA (Body Composition Analysis) data from ActiveX API

    Args:
        phone_number: Phone number in format "9876543210" or "+91-9876543210"
        date: Optional date to fetch BCA from (defaults to empty string for latest)

    Returns:
        dict with BCA data or None if not found
    """
    # Format phone number for ActiveX API (requires +91-XXXXXXXXXX format)
    if not phone_number.startswith('+91'):
        phone_number = f"+91-{phone_number.replace('+91', '').replace('-', '')}"
    elif '+91' in phone_number and '-' not in phone_number:
        phone_number = phone_number.replace('+91', '+91-')

    headers = {
        'x-api-key': settings.ACTIVEX_API_KEY,
        'Content-Type': 'application/json'
    }

    payload = {
        "Date": date if date else "",
        "PhoneNumbers": [phone_number]
    }

    try:
        response = requests.post(
            settings.ACTIVEX_API_URL,
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('result', {}).get('records'):
                return data['result']['records'][0]

        return None
    except Exception as e:
        print(f"ActiveX API Error: {str(e)}")
        return None


def update_customer_bca(customer, bca_data):
    """
    Update customer record with BCA data from ActiveX

    Args:
        customer: Customer model instance
        bca_data: BCA data dict from ActiveX API

    Returns:
        Updated customer instance
    """
    if not bca_data:
        return customer

    # Map ActiveX fields to Customer model fields
    customer.weight_kg = bca_data.get('ppWeightKg')
    customer.height_cm = bca_data.get('ppHeightCm')

    # BCA fields
    customer.bca_weight_kg = bca_data.get('ppWeightKg')
    customer.bca_bmi = bca_data.get('ppBMI')
    customer.bca_bodyFat_percent = bca_data.get('ppFat')
    customer.bca_muscleMass_kg = bca_data.get('ppMuscleKg')
    customer.bca_subcutaneousFat_percent = bca_data.get('ppBodyFatSubCutPercentage')
    customer.bca_visceralFat_level = bca_data.get('ppVisceralFat')
    customer.bca_bodyAge_years = bca_data.get('ppBodyAge')
    customer.bca_bmr_kcal = bca_data.get('ppBMR')
    customer.bca_skeletalMass_kg = bca_data.get('ppBodySkeletalKg')
    customer.bca_muscleMass_percent = bca_data.get('ppMusclePercentage')
    customer.bca_boneMass_kg = bca_data.get('ppBoneKg')
    customer.bca_protein_kg = bca_data.get('ppProteinKg')

    customer.save()
    return customer


def parse_bca_response(bca_data):
    """
    Parse ActiveX BCA response into a cleaner format for frontend

    Args:
        bca_data: Raw BCA data from ActiveX API

    Returns:
        Cleaned dict with key BCA metrics
    """
    if not bca_data:
        return None

    return {
        # Basic Info
        "weight_kg": bca_data.get('ppWeightKg'),
        "height_cm": bca_data.get('ppHeightCm'),
        "age": bca_data.get('ppAge'),
        "sex": bca_data.get('ppSex'),

        # Body Composition
        "bmi": bca_data.get('ppBMI'),
        "body_fat_percent": bca_data.get('ppFat'),
        "body_fat_kg": bca_data.get('ppBodyfatKg'),
        "muscle_kg": bca_data.get('ppMuscleKg'),
        "muscle_percent": bca_data.get('ppMusclePercentage'),
        "bone_kg": bca_data.get('ppBoneKg'),
        "protein_kg": bca_data.get('ppProteinKg'),
        "protein_percent": bca_data.get('ppProteinPercentage'),
        "water_kg": bca_data.get('ppWaterKg'),
        "water_percent": bca_data.get('ppWaterPercentage'),

        # Advanced Metrics
        "bmr": bca_data.get('ppBMR'),
        "body_age": bca_data.get('ppBodyAge'),
        "visceral_fat": bca_data.get('ppVisceralFat'),
        "subcutaneous_fat_kg": bca_data.get('ppBodyFatSubCutKg'),
        "subcutaneous_fat_percent": bca_data.get('ppBodyFatSubCutPercentage'),
        "skeletal_muscle_kg": bca_data.get('ppBodySkeletalKg'),
        "skeletal_muscle_percent": bca_data.get('ppBodySkeletal'),

        # Body Score & Health
        "body_score": bca_data.get('ppBodyScore'),
        "body_type": bca_data.get('ppBodyType'),
        "body_health": bca_data.get('ppBodyHealth'),
        "obesity_percent": bca_data.get('ppObesity'),

        # Heart Rate
        "heart_rate": bca_data.get('ppHeartRate'),

        # Ideal/Target
        "ideal_weight_kg": bca_data.get('ppIdealWeightKg'),
        "standard_weight_kg": bca_data.get('ppBodyStandardWeightKg'),
        "control_weight_kg": bca_data.get('ppControlWeightKg'),
        "fat_control_kg": bca_data.get('ppFatControlKg'),

        # Segmental Analysis (Arms & Legs)
        "muscle_kg_left_arm": bca_data.get('ppMuscleKgLeftArm'),
        "muscle_kg_right_arm": bca_data.get('ppMuscleKgRightArm'),
        "muscle_kg_left_leg": bca_data.get('ppMuscleKgLeftLeg'),
        "muscle_kg_right_leg": bca_data.get('ppMuscleKgRightLeg'),
        "muscle_kg_trunk": bca_data.get('ppMuscleKgTrunk'),

        "fat_kg_left_arm": bca_data.get('ppBodyFatKgLeftArm'),
        "fat_kg_right_arm": bca_data.get('ppBodyFatKgRightArm'),
        "fat_kg_left_leg": bca_data.get('ppBodyFatKgLeftLeg'),
        "fat_kg_right_leg": bca_data.get('ppBodyFatKgRightLeg'),
        "fat_kg_trunk": bca_data.get('ppBodyFatKgTrunk'),

        # Timestamp
        "recorded_at": bca_data.get('insertionDate'),
    }
