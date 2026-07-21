from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import AccessToken
from datetime import datetime, timedelta
from .utils import send_otp, generate_slots_for_branch, fetch_bca_from_activex, update_customer_bca, parse_bca_response
from .models import Customer, TimeSlot, DayOff, SlotConfig, Branch, UserProfile, Session, Invoice, Announcement, TrainerEarning
from .serializers import (
    CustomerSerializer, CustomerDetailSerializer, TrainerSerializer,
    SessionSerializer, TimeSlotSerializer, DayOffSerializer,
    SlotConfigSerializer, BranchSerializer, InvoiceSerializer,
    AnnouncementSerializer, TrainerEarningSerializer, ClientProfileSerializer
)
from django.db.models import Sum, Count
from decimal import Decimal
# Create your views here.


def home(request):
    return HttpResponse("Welcome to Starlet Fitness Backend!")



@api_view(['GET'])
def test(request):
    send_otp('+919897144223', '123456') 
    return Response({"message": "DRF Working!"})


def genrate_4_digit_otp():
    import random
    return str(random.randint(1000, 9999))

@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp_view(request):
    try:
        phone = request.data.get('phone')

        if not phone:
            return Response({"error": "Phone number is required.", "code": "400"}, status=400)

        user = Customer.objects.filter(phone=phone).first()

        if not user:
            return Response({"error": "User with this phone number does not exist.", "code": "400"}, status=400)

        # Use fixed OTP "0000" for localhost testing
        # TODO: Change to genrate_4_digit_otp() and enable Twilio in production
        otp = "0000"

        # Save OTP to user
        user.otp = otp
        user.save()

        # TODO: Enable Twilio SMS when ready
        # otp = genrate_4_digit_otp()
        # message_sid = send_otp(phone, otp)

        return Response({"status": "success", "message": "OTP sent successfully.", "code": "100"}, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)
    

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp_view(request):
    try:
        phone = request.data.get('phone')
        otp = request.data.get('otp')

        if not phone or not otp:
            return Response({"error": "Phone number and OTP are required.", "code": "400"}, status=400)

        user = Customer.objects.filter(phone=phone, otp=otp).first()

        if not user:
            return Response({"error": "Invalid OTP or phone number.", "code": "400"}, status=400)

        user.otp = None
        user.save()

        # Generate access token
        token = AccessToken()
        token['customer_id'] = user.id
        token['phone'] = user.phone
        token['email'] = user.email
        token['role'] = user.role

        return Response({
                "status": "success",
                "message": "OTP verified successfully.",
                "code": "100",
                "access_token": str(token),
                "user": CustomerSerializer(user).data
            }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])
def book_session(request):
    pass


@api_view(['GET'])
@permission_classes([AllowAny])
def get_customer_sessions(request):
    pass


# ==================== MANAGER SLOT MANAGEMENT APIs ====================

def get_manager_branch(request):
    """Helper function to get manager's branch from JWT token"""
    try:
        customer_id = request.auth.get('customer_id') if request.auth else None
        if not customer_id:
            return None, "Authentication required"

        customer = Customer.objects.filter(id=customer_id).first()
        if not customer:
            return None, "User not found"

        if customer.role != 'TRAINER':
            return None, "Only managers can access this"

        if not customer.branch:
            return None, "Manager not assigned to any branch"

        return customer.branch, None
    except Exception as e:
        return None, str(e)


@api_view(['POST'])
@permission_classes([AllowAny])  # TODO: Change to IsAuthenticated after testing
def generate_slots(request):
    """Generate slots for manager's branch for next 7 days"""
    try:
        branch_id = request.data.get('branch_id')
        days_ahead = request.data.get('days_ahead', 7)

        if not branch_id:
            return Response({"error": "branch_id is required", "code": "400"}, status=400)

        branch = Branch.objects.filter(id=branch_id).first()
        if not branch:
            return Response({"error": "Branch not found", "code": "400"}, status=400)

        count = generate_slots_for_branch(branch, days_ahead)

        return Response({
            "status": "success",
            "message": f"Generated {count} slots for next {days_ahead} days",
            "code": "100"
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])  # TODO: Change to IsAuthenticated after testing
def get_slots(request):
    """Get slots for a branch by date"""
    try:
        branch_id = request.query_params.get('branch_id')
        date_str = request.query_params.get('date')  # Format: YYYY-MM-DD

        if not branch_id:
            return Response({"error": "branch_id is required", "code": "400"}, status=400)

        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({"error": "Invalid date format. Use YYYY-MM-DD", "code": "400"}, status=400)
        else:
            target_date = datetime.now().date()

        # Check if day is off
        is_day_off = DayOff.objects.filter(branch_id=branch_id, date=target_date).exists()

        slots = TimeSlot.objects.filter(branch_id=branch_id, date=target_date)
        serializer = TimeSlotSerializer(slots, many=True)

        return Response({
            "status": "success",
            "code": "100",
            "date": str(target_date),
            "is_day_off": is_day_off,
            "slots": serializer.data
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])  # TODO: Change to IsAuthenticated after testing
def block_slot(request):
    """Block or unblock a specific slot"""
    try:
        slot_id = request.data.get('slot_id')
        action = request.data.get('action')  # 'block' or 'unblock'

        if not slot_id or not action:
            return Response({"error": "slot_id and action are required", "code": "400"}, status=400)

        if action not in ['block', 'unblock']:
            return Response({"error": "action must be 'block' or 'unblock'", "code": "400"}, status=400)

        slot = TimeSlot.objects.filter(id=slot_id).first()
        if not slot:
            return Response({"error": "Slot not found", "code": "400"}, status=400)

        if action == 'block':
            if slot.status == 'BOOKED':
                return Response({"error": "Cannot block a booked slot", "code": "400"}, status=400)
            slot.status = 'BLOCKED'
        else:
            slot.status = 'AVAILABLE'

        slot.save()

        return Response({
            "status": "success",
            "message": f"Slot {action}ed successfully",
            "code": "100",
            "slot": TimeSlotSerializer(slot).data
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])  # TODO: Change to IsAuthenticated after testing
def block_time_range(request):
    """Block multiple slots in a time range"""
    try:
        branch_id = request.data.get('branch_id')
        date_str = request.data.get('date')  # Format: YYYY-MM-DD
        start_time_str = request.data.get('start_time')  # Format: HH:MM
        end_time_str = request.data.get('end_time')  # Format: HH:MM
        action = request.data.get('action', 'block')  # 'block' or 'unblock'

        if not all([branch_id, date_str, start_time_str, end_time_str]):
            return Response({
                "error": "branch_id, date, start_time, end_time are required",
                "code": "400"
            }, status=400)

        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()

        slots = TimeSlot.objects.filter(
            branch_id=branch_id,
            date=target_date,
            start_time__gte=start_time,
            start_time__lt=end_time
        )

        if action == 'block':
            updated = slots.exclude(status='BOOKED').update(status='BLOCKED')
        else:
            updated = slots.filter(status='BLOCKED').update(status='AVAILABLE')

        return Response({
            "status": "success",
            "message": f"{updated} slots {action}ed",
            "code": "100"
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])  # TODO: Change to IsAuthenticated after testing
def set_day_off(request):
    """Mark a day as off or remove day off"""
    try:
        branch_id = request.data.get('branch_id')
        date_str = request.data.get('date')  # Format: YYYY-MM-DD
        is_off = request.data.get('is_off', True)  # True = mark as off, False = remove
        reason = request.data.get('reason', '')

        if not branch_id or not date_str:
            return Response({"error": "branch_id and date are required", "code": "400"}, status=400)

        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        branch = Branch.objects.filter(id=branch_id).first()

        if not branch:
            return Response({"error": "Branch not found", "code": "400"}, status=400)

        if is_off:
            # Mark day as off
            day_off, created = DayOff.objects.get_or_create(
                branch=branch,
                date=target_date,
                defaults={'reason': reason}
            )
            if not created:
                day_off.reason = reason
                day_off.save()

            # Block all slots for this day
            TimeSlot.objects.filter(
                branch=branch,
                date=target_date
            ).exclude(status='BOOKED').update(status='BLOCKED')

            return Response({
                "status": "success",
                "message": f"Day off set for {target_date}",
                "code": "100"
            }, status=200)
        else:
            # Remove day off
            DayOff.objects.filter(branch=branch, date=target_date).delete()

            # Unblock all blocked slots
            TimeSlot.objects.filter(
                branch=branch,
                date=target_date,
                status='BLOCKED'
            ).update(status='AVAILABLE')

            return Response({
                "status": "success",
                "message": f"Day off removed for {target_date}",
                "code": "100"
            }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])  # TODO: Change to IsAuthenticated after testing
def get_slot_config(request):
    """Get slot configuration for a branch"""
    try:
        branch_id = request.query_params.get('branch_id')

        if not branch_id:
            return Response({"error": "branch_id is required", "code": "400"}, status=400)

        configs = SlotConfig.objects.filter(branch_id=branch_id).order_by('weekday')
        serializer = SlotConfigSerializer(configs, many=True)

        return Response({
            "status": "success",
            "code": "100",
            "configs": serializer.data
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])  # TODO: Change to IsAuthenticated after testing
def update_slot_config(request):
    """Update slot configuration for a weekday"""
    try:
        branch_id = request.data.get('branch_id')
        weekday = request.data.get('weekday')  # 0-6 (Monday-Sunday)
        is_active = request.data.get('is_active')

        if branch_id is None or weekday is None:
            return Response({"error": "branch_id and weekday are required", "code": "400"}, status=400)

        config = SlotConfig.objects.filter(branch_id=branch_id, weekday=weekday).first()
        if not config:
            return Response({"error": "Config not found", "code": "400"}, status=400)

        # Update fields if provided
        if is_active is not None:
            config.is_active = is_active

        if 'morning_start' in request.data:
            config.morning_start = request.data['morning_start']
        if 'morning_end' in request.data:
            config.morning_end = request.data['morning_end']
        if 'evening_start' in request.data:
            config.evening_start = request.data['evening_start']
        if 'evening_end' in request.data:
            config.evening_end = request.data['evening_end']

        config.save()

        return Response({
            "status": "success",
            "message": "Config updated",
            "code": "100",
            "config": SlotConfigSerializer(config).data
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])  # TODO: Change to IsAuthenticated after testing
def get_week_slots(request):
    """Get slots for entire week for a branch"""
    try:
        branch_id = request.query_params.get('branch_id')
        start_date_str = request.query_params.get('start_date')  # Optional, defaults to today

        if not branch_id:
            return Response({"error": "branch_id is required", "code": "400"}, status=400)

        branch = Branch.objects.filter(id=branch_id).first()
        if not branch:
            return Response({"error": "Branch not found", "code": "400"}, status=400)

        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            start_date = datetime.now().date()

        end_date = start_date + timedelta(days=7)

        # Get all day offs
        days_off = DayOff.objects.filter(
            branch_id=branch_id,
            date__gte=start_date,
            date__lt=end_date
        ).values_list('date', flat=True)

        # Get all slots
        slots = TimeSlot.objects.filter(
            branch_id=branch_id,
            date__gte=start_date,
            date__lt=end_date
        ).order_by('date', 'start_time')

        # Build days array for frontend
        days = []
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            day_slots = [s for s in slots if s.date == current_date]

            days.append({
                "date": str(current_date),
                "day_name": current_date.strftime('%A'),
                "is_off": current_date in days_off,
                "slots": TimeSlotSerializer(day_slots, many=True).data
            })

        return Response({
            "branch_name": branch.name,
            "days": days,
            "code": "100"
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


# ==================== MANAGER DASHBOARD APIs ====================

@api_view(['GET'])
@permission_classes([AllowAny])  # TODO: Change to IsAuthenticated
def get_branch_sessions(request):
    """Get past sessions for a branch with trainer and client info"""
    try:
        branch_id = request.query_params.get('branch_id')
        status_filter = request.query_params.get('status')  # Optional: Completed, Cancelled, etc.
        date_from = request.query_params.get('date_from')  # Optional: YYYY-MM-DD
        date_to = request.query_params.get('date_to')  # Optional: YYYY-MM-DD

        if not branch_id:
            return Response({"error": "branch_id is required", "code": "400"}, status=400)

        sessions = Session.objects.filter(branch_id=branch_id).order_by('-session_date')

        # Apply filters
        if status_filter:
            sessions = sessions.filter(status=status_filter)

        if date_from:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            sessions = sessions.filter(session_date__gte=from_date)

        if date_to:
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
            sessions = sessions.filter(session_date__lte=to_date)

        serializer = SessionSerializer(sessions, many=True)

        return Response({
            "status": "success",
            "code": "100",
            "total": sessions.count(),
            "sessions": serializer.data
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])  # TODO: Change to IsAuthenticated
def get_branch_trainers(request):
    """Get all trainers for a branch"""
    try:
        branch_id = request.query_params.get('branch_id')

        if not branch_id:
            return Response({"error": "branch_id is required", "code": "400"}, status=400)

        trainers = Customer.objects.filter(branch_id=branch_id, role='TRAINER')
        serializer = TrainerSerializer(trainers, many=True)

        return Response({
            "status": "success",
            "code": "100",
            "total": trainers.count(),
            "trainers": serializer.data
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])  # TODO: Change to IsAuthenticated
def get_branch_clients(request):
    """Get all clients for a branch"""
    try:
        branch_id = request.query_params.get('branch_id')

        if not branch_id:
            return Response({"error": "branch_id is required", "code": "400"}, status=400)

        clients = Customer.objects.filter(branch_id=branch_id, role='CLIENT')
        serializer = CustomerDetailSerializer(clients, many=True)

        return Response({
            "status": "success",
            "code": "100",
            "total": clients.count(),
            "clients": serializer.data
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])  # TODO: Change to IsAuthenticated
def enroll_client(request):
    """Enroll a new client at a branch"""
    try:
        branch_id = request.data.get('branch_id')
        name = request.data.get('name')
        email = request.data.get('email')
        phone = request.data.get('phone')
        height_cm = request.data.get('height_cm')
        weight_kg = request.data.get('weight_kg')

        # Validation
        if not all([branch_id, name, email, phone]):
            return Response({
                "error": "branch_id, name, email, and phone are required",
                "code": "400"
            }, status=400)

        # Check if phone or email already exists
        if Customer.objects.filter(phone=phone).exists():
            return Response({"error": "Phone number already registered", "code": "400"}, status=400)

        if Customer.objects.filter(email=email).exists():
            return Response({"error": "Email already registered", "code": "400"}, status=400)

        branch = Branch.objects.filter(id=branch_id).first()
        if not branch:
            return Response({"error": "Branch not found", "code": "400"}, status=400)

        # Create client
        client = Customer.objects.create(
            name=name,
            email=email,
            phone=phone,
            branch=branch,
            role='CLIENT',
            height_cm=height_cm,
            weight_kg=weight_kg
        )

        return Response({
            "status": "success",
            "message": "Client enrolled successfully",
            "code": "100",
            "client": CustomerDetailSerializer(client).data
        }, status=201)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])  # TODO: Change to IsAuthenticated
def enroll_trainer(request):
    """Enroll a new trainer at a branch"""
    try:
        branch_id = request.data.get('branch_id')
        name = request.data.get('name')
        email = request.data.get('email')
        phone = request.data.get('phone')
        is_partner = request.data.get('is_partner', False)
        partner_id = request.data.get('partner_id')

        # Validation
        if not all([branch_id, name, email, phone]):
            return Response({
                "error": "branch_id, name, email, and phone are required",
                "code": "400"
            }, status=400)

        # Check if phone or email already exists
        if Customer.objects.filter(phone=phone).exists():
            return Response({"error": "Phone number already registered", "code": "400"}, status=400)

        if Customer.objects.filter(email=email).exists():
            return Response({"error": "Email already registered", "code": "400"}, status=400)

        branch = Branch.objects.filter(id=branch_id).first()
        if not branch:
            return Response({"error": "Branch not found", "code": "400"}, status=400)

        # Create trainer
        trainer = Customer.objects.create(
            name=name,
            email=email,
            phone=phone,
            branch=branch,
            role='TRAINER',
            is_partner=is_partner,
            partner_id=partner_id
        )

        return Response({
            "status": "success",
            "message": "Trainer enrolled successfully",
            "code": "100",
            "trainer": TrainerSerializer(trainer).data
        }, status=201)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])  # TODO: Change to IsAuthenticated
def get_trainer_sessions(request):
    """Get all sessions for a specific trainer"""
    try:
        trainer_id = request.query_params.get('trainer_id')
        status_filter = request.query_params.get('status')

        if not trainer_id:
            return Response({"error": "trainer_id is required", "code": "400"}, status=400)

        sessions = Session.objects.filter(trainer_id=trainer_id).order_by('-session_date')

        if status_filter:
            sessions = sessions.filter(status=status_filter)

        serializer = SessionSerializer(sessions, many=True)

        return Response({
            "status": "success",
            "code": "100",
            "total": sessions.count(),
            "sessions": serializer.data
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])  # TODO: Change to IsAuthenticated
def get_manager_dashboard(request):
    """Get dashboard summary for manager"""
    try:
        branch_id = request.query_params.get('branch_id')

        if not branch_id:
            return Response({"error": "branch_id is required", "code": "400"}, status=400)

        # Get counts
        total_trainers = Customer.objects.filter(branch_id=branch_id, role='TRAINER').count()
        total_clients = Customer.objects.filter(branch_id=branch_id, role='CLIENT').count()
        total_sessions = Session.objects.filter(branch_id=branch_id).count()
        completed_sessions = Session.objects.filter(branch_id=branch_id, status='Completed').count()

        # Today's sessions
        today = datetime.now().date()
        today_sessions = Session.objects.filter(
            branch_id=branch_id,
            session_date__date=today
        ).order_by('session_date')

        # Available slots today
        available_slots = TimeSlot.objects.filter(
            branch_id=branch_id,
            date=today,
            status='AVAILABLE'
        ).count()

        return Response({
            "status": "success",
            "code": "100",
            "dashboard": {
                "total_trainers": total_trainers,
                "total_clients": total_clients,
                "total_sessions": total_sessions,
                "completed_sessions": completed_sessions,
                "today_sessions": SessionSerializer(today_sessions, many=True).data,
                "available_slots_today": available_slots
            }
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


# ==================== TRAINER BCA (Body Composition Analysis) APIs ====================

@api_view(['GET'])
@permission_classes([AllowAny])  # TODO: Change to IsAuthenticated
def get_client_bca(request):
    """Get BCA data for a client (stored in database)"""
    try:
        client_id = request.query_params.get('client_id')

        if not client_id:
            return Response({"error": "client_id is required", "code": "400"}, status=400)

        client = Customer.objects.filter(id=client_id, role='CLIENT').first()
        if not client:
            return Response({"error": "Client not found", "code": "400"}, status=400)

        bca_data = {
            "client_id": client.id,
            "client_name": client.name,
            "client_phone": client.phone,
            "height_cm": client.height_cm,
            "weight_kg": client.weight_kg,
            "bca": {
                "weight_kg": client.bca_weight_kg,
                "bmi": client.bca_bmi,
                "body_fat_percent": client.bca_bodyFat_percent,
                "muscle_mass_kg": client.bca_muscleMass_kg,
                "muscle_mass_percent": client.bca_muscleMass_percent,
                "subcutaneous_fat_percent": client.bca_subcutaneousFat_percent,
                "visceral_fat_level": client.bca_visceralFat_level,
                "body_age_years": client.bca_bodyAge_years,
                "bmr_kcal": client.bca_bmr_kcal,
                "skeletal_mass_kg": client.bca_skeletalMass_kg,
                "bone_mass_kg": client.bca_boneMass_kg,
                "protein_kg": client.bca_protein_kg,
            },
            "measurements": {
                "chest_cm": client.measurements_chest_cm,
                "upper_waist_cm": client.measurements_upper_waist_cm,
                "mid_waist_cm": client.measurements_mid_waist_cm,
                "lower_waist_cm": client.measurements_lower_waist_cm,
                "right_thigh_cm": client.measurements_rightThigh_cm,
                "left_thigh_cm": client.measurements_leftThigh_cm,
                "right_arm_cm": client.measurements_rightArm_cm,
                "left_arm_cm": client.measurements_leftArm_cm,
            },
            "updated_at": client.updated_at
        }

        return Response({
            "status": "success",
            "code": "100",
            "data": bca_data
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])  # TODO: Change to IsAuthenticated
def sync_client_bca(request):
    """Sync/Fetch BCA data from ActiveX API and update client record"""
    try:
        client_id = request.data.get('client_id')

        if not client_id:
            return Response({"error": "client_id is required", "code": "400"}, status=400)

        client = Customer.objects.filter(id=client_id, role='CLIENT').first()
        if not client:
            return Response({"error": "Client not found", "code": "400"}, status=400)

        # Fetch BCA from ActiveX
        bca_raw = fetch_bca_from_activex(client.phone)

        if not bca_raw:
            return Response({
                "error": "No BCA data found for this phone number in ActiveX",
                "code": "400"
            }, status=400)

        # Update customer record
        update_customer_bca(client, bca_raw)

        # Parse for frontend
        bca_parsed = parse_bca_response(bca_raw)

        return Response({
            "status": "success",
            "message": "BCA data synced successfully",
            "code": "100",
            "bca": bca_parsed
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])  # TODO: Change to IsAuthenticated
def fetch_bca_preview(request):
    """Fetch BCA data from ActiveX without saving (preview only)"""
    try:
        phone = request.data.get('phone')

        if not phone:
            return Response({"error": "phone is required", "code": "400"}, status=400)

        # Fetch BCA from ActiveX
        bca_raw = fetch_bca_from_activex(phone)

        if not bca_raw:
            return Response({
                "error": "No BCA data found for this phone number in ActiveX",
                "code": "400"
            }, status=400)

        # Parse for frontend
        bca_parsed = parse_bca_response(bca_raw)

        return Response({
            "status": "success",
            "code": "100",
            "bca": bca_parsed
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])  # TODO: Change to IsAuthenticated
def update_client_measurements(request):
    """Trainer manually updates client measurements"""
    try:
        client_id = request.data.get('client_id')

        if not client_id:
            return Response({"error": "client_id is required", "code": "400"}, status=400)

        client = Customer.objects.filter(id=client_id, role='CLIENT').first()
        if not client:
            return Response({"error": "Client not found", "code": "400"}, status=400)

        # Update basic info
        if 'height_cm' in request.data:
            client.height_cm = request.data['height_cm']
        if 'weight_kg' in request.data:
            client.weight_kg = request.data['weight_kg']

        # Update measurements
        if 'chest_cm' in request.data:
            client.measurements_chest_cm = request.data['chest_cm']
        if 'upper_waist_cm' in request.data:
            client.measurements_upper_waist_cm = request.data['upper_waist_cm']
        if 'mid_waist_cm' in request.data:
            client.measurements_mid_waist_cm = request.data['mid_waist_cm']
        if 'lower_waist_cm' in request.data:
            client.measurements_lower_waist_cm = request.data['lower_waist_cm']
        if 'right_thigh_cm' in request.data:
            client.measurements_rightThigh_cm = request.data['right_thigh_cm']
        if 'left_thigh_cm' in request.data:
            client.measurements_leftThigh_cm = request.data['left_thigh_cm']
        if 'right_arm_cm' in request.data:
            client.measurements_rightArm_cm = request.data['right_arm_cm']
        if 'left_arm_cm' in request.data:
            client.measurements_leftArm_cm = request.data['left_arm_cm']

        # Update BCA manually if provided
        if 'bca_bmi' in request.data:
            client.bca_bmi = request.data['bca_bmi']
        if 'bca_bodyFat_percent' in request.data:
            client.bca_bodyFat_percent = request.data['bca_bodyFat_percent']
        if 'bca_muscleMass_kg' in request.data:
            client.bca_muscleMass_kg = request.data['bca_muscleMass_kg']
        if 'bca_visceralFat_level' in request.data:
            client.bca_visceralFat_level = request.data['bca_visceralFat_level']
        if 'bca_bodyAge_years' in request.data:
            client.bca_bodyAge_years = request.data['bca_bodyAge_years']
        if 'bca_bmr_kcal' in request.data:
            client.bca_bmr_kcal = request.data['bca_bmr_kcal']

        client.save()

        return Response({
            "status": "success",
            "message": "Client measurements updated",
            "code": "100",
            "client": CustomerDetailSerializer(client).data
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


# ==================== CLIENT APIs ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_client_profile(request):
    """Get client's own profile"""
    try:
        client_id = request.query_params.get('client_id')

        if not client_id:
            return Response({"error": "client_id is required", "code": "400"}, status=400)

        client = Customer.objects.filter(id=client_id).first()
        if not client:
            return Response({"error": "Client not found", "code": "400"}, status=400)

        return Response({
            "status": "success",
            "code": "100",
            "profile": ClientProfileSerializer(client).data
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])
def update_client_profile(request):
    """Update client's own profile"""
    try:
        client_id = request.data.get('client_id')

        if not client_id:
            return Response({"error": "client_id is required", "code": "400"}, status=400)

        client = Customer.objects.filter(id=client_id).first()
        if not client:
            return Response({"error": "Client not found", "code": "400"}, status=400)

        # Update allowed fields
        if 'name' in request.data:
            client.name = request.data['name']
        if 'email' in request.data:
            client.email = request.data['email']
        if 'height_cm' in request.data:
            client.height_cm = request.data['height_cm']
        if 'weight_kg' in request.data:
            client.weight_kg = request.data['weight_kg']

        client.save()

        return Response({
            "status": "success",
            "message": "Profile updated",
            "code": "100",
            "profile": ClientProfileSerializer(client).data
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_client_available_slots(request):
    """Get available slots for client to book"""
    try:
        branch_id = request.query_params.get('branch_id')
        date_str = request.query_params.get('date')

        if not branch_id:
            return Response({"error": "branch_id is required", "code": "400"}, status=400)

        if date_str:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            target_date = datetime.now().date()

        # Check if day is off
        is_day_off = DayOff.objects.filter(branch_id=branch_id, date=target_date).exists()
        if is_day_off:
            return Response({
                "status": "success",
                "code": "100",
                "date": str(target_date),
                "is_day_off": True,
                "slots": []
            }, status=200)

        # Get only available slots
        slots = TimeSlot.objects.filter(
            branch_id=branch_id,
            date=target_date,
            status='AVAILABLE'
        ).order_by('start_time')

        return Response({
            "status": "success",
            "code": "100",
            "date": str(target_date),
            "is_day_off": False,
            "slots": TimeSlotSerializer(slots, many=True).data
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])
def book_session(request):
    """Client books a session"""
    try:
        client_id = request.data.get('client_id')
        slot_id = request.data.get('slot_id')
        trainer_id = request.data.get('trainer_id')
        notes = request.data.get('notes', '')

        if not client_id or not slot_id:
            return Response({"error": "client_id and slot_id are required", "code": "400"}, status=400)

        client = Customer.objects.filter(id=client_id, role='CLIENT').first()
        if not client:
            return Response({"error": "Client not found", "code": "400"}, status=400)

        slot = TimeSlot.objects.filter(id=slot_id).first()
        if not slot:
            return Response({"error": "Slot not found", "code": "400"}, status=400)

        if slot.status != 'AVAILABLE':
            return Response({"error": "Slot is not available", "code": "400"}, status=400)

        trainer = None
        if trainer_id:
            trainer = Customer.objects.filter(id=trainer_id, role='TRAINER').first()

        # Create session
        session_datetime = datetime.combine(slot.date, slot.start_time)
        session = Session.objects.create(
            customer=client,
            trainer=trainer,
            branch=slot.branch,
            session_date=session_datetime,
            status='Scheduled',
            notes=notes
        )

        # Mark slot as booked
        slot.status = 'BOOKED'
        slot.booked_by = client
        slot.save()

        return Response({
            "status": "success",
            "message": "Session booked successfully",
            "code": "100",
            "session": SessionSerializer(session).data
        }, status=201)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])
def cancel_session(request):
    """Client cancels a session"""
    try:
        session_id = request.data.get('session_id')
        client_id = request.data.get('client_id')

        if not session_id:
            return Response({"error": "session_id is required", "code": "400"}, status=400)

        session = Session.objects.filter(id=session_id).first()
        if not session:
            return Response({"error": "Session not found", "code": "400"}, status=400)

        if session.status in ['Completed', 'Cancelled']:
            return Response({"error": "Cannot cancel this session", "code": "400"}, status=400)

        # Find and free the slot
        slot = TimeSlot.objects.filter(
            branch=session.branch,
            date=session.session_date.date(),
            start_time=session.session_date.time(),
            booked_by=session.customer
        ).first()

        if slot:
            slot.status = 'AVAILABLE'
            slot.booked_by = None
            slot.save()

        session.status = 'Cancelled'
        session.save()

        return Response({
            "status": "success",
            "message": "Session cancelled",
            "code": "100"
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_client_sessions(request):
    """Get client's session history"""
    try:
        client_id = request.query_params.get('client_id')
        status_filter = request.query_params.get('status')

        if not client_id:
            return Response({"error": "client_id is required", "code": "400"}, status=400)

        sessions = Session.objects.filter(customer_id=client_id).order_by('-session_date')

        if status_filter:
            sessions = sessions.filter(status=status_filter)

        return Response({
            "status": "success",
            "code": "100",
            "total": sessions.count(),
            "sessions": SessionSerializer(sessions, many=True).data
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


# ==================== TRAINER SPECIFIC APIs ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_trainer_assigned_sessions(request):
    """Get trainer's assigned sessions"""
    try:
        trainer_id = request.query_params.get('trainer_id')

        if not trainer_id:
            return Response({"error": "trainer_id is required", "code": "400"}, status=400)

        sessions = Session.objects.filter(
            trainer_id=trainer_id
        ).order_by('-session_date')

        return Response({
            "status": "success",
            "code": "100",
            "total": sessions.count(),
            "sessions": SessionSerializer(sessions, many=True).data
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_trainer_upcoming_sessions(request):
    """Get trainer's upcoming sessions"""
    try:
        trainer_id = request.query_params.get('trainer_id')

        if not trainer_id:
            return Response({"error": "trainer_id is required", "code": "400"}, status=400)

        now = datetime.now()
        sessions = Session.objects.filter(
            trainer_id=trainer_id,
            session_date__gte=now,
            status='Scheduled'
        ).order_by('session_date')

        return Response({
            "status": "success",
            "code": "100",
            "total": sessions.count(),
            "sessions": SessionSerializer(sessions, many=True).data
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])
def start_session(request):
    """Trainer starts a session"""
    try:
        session_id = request.data.get('session_id')

        if not session_id:
            return Response({"error": "session_id is required", "code": "400"}, status=400)

        session = Session.objects.filter(id=session_id).first()
        if not session:
            return Response({"error": "Session not found", "code": "400"}, status=400)

        session.status = 'In Progress'
        session.session_started_at = datetime.now()
        session.save()

        return Response({
            "status": "success",
            "message": "Session started",
            "code": "100",
            "session": SessionSerializer(session).data
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])
def end_session(request):
    """Trainer ends a session"""
    try:
        session_id = request.data.get('session_id')
        session_amount = request.data.get('session_amount', 500)

        if not session_id:
            return Response({"error": "session_id is required", "code": "400"}, status=400)

        session = Session.objects.filter(id=session_id).first()
        if not session:
            return Response({"error": "Session not found", "code": "400"}, status=400)

        session.status = 'Completed'
        session.save()

        # Create trainer earning record
        if session.trainer:
            TrainerEarning.objects.create(
                trainer=session.trainer,
                session=session,
                session_amount=Decimal(str(session_amount)),
                trainer_percent=Decimal('50'),
                trainer_earning=Decimal(str(session_amount)) * Decimal('0.5'),
                gym_earning=Decimal(str(session_amount)) * Decimal('0.5')
            )

        return Response({
            "status": "success",
            "message": "Session completed",
            "code": "100",
            "session": SessionSerializer(session).data
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_trainer_earnings(request):
    """Get trainer earnings with filters"""
    try:
        trainer_id = request.query_params.get('trainer_id')
        period = request.query_params.get('period', 'all')  # 1month, 6months, all

        if not trainer_id:
            return Response({"error": "trainer_id is required", "code": "400"}, status=400)

        earnings = TrainerEarning.objects.filter(trainer_id=trainer_id)

        if period == '1month':
            start_date = datetime.now() - timedelta(days=30)
            earnings = earnings.filter(created_at__gte=start_date)
        elif period == '6months':
            start_date = datetime.now() - timedelta(days=180)
            earnings = earnings.filter(created_at__gte=start_date)

        total_earnings = earnings.aggregate(total=Sum('trainer_earning'))['total'] or 0
        total_sessions = earnings.count()
        paid_amount = earnings.filter(is_paid=True).aggregate(total=Sum('trainer_earning'))['total'] or 0
        pending_amount = earnings.filter(is_paid=False).aggregate(total=Sum('trainer_earning'))['total'] or 0

        return Response({
            "status": "success",
            "code": "100",
            "summary": {
                "total_earnings": float(total_earnings),
                "total_sessions": total_sessions,
                "paid_amount": float(paid_amount),
                "pending_amount": float(pending_amount)
            },
            "earnings": TrainerEarningSerializer(earnings.order_by('-created_at'), many=True).data
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_trainer_dashboard(request):
    """Get trainer dashboard summary"""
    try:
        trainer_id = request.query_params.get('trainer_id')

        if not trainer_id:
            return Response({"error": "trainer_id is required", "code": "400"}, status=400)

        trainer = Customer.objects.filter(id=trainer_id, role='TRAINER').first()
        if not trainer:
            return Response({"error": "Trainer not found", "code": "400"}, status=400)

        now = datetime.now()
        today = now.date()

        # Stats
        total_clients = Session.objects.filter(trainer_id=trainer_id).values('customer').distinct().count()
        upcoming_sessions = Session.objects.filter(
            trainer_id=trainer_id,
            session_date__gte=now,
            status='Scheduled'
        ).count()
        today_sessions = Session.objects.filter(
            trainer_id=trainer_id,
            session_date__date=today
        )
        total_earnings = TrainerEarning.objects.filter(trainer_id=trainer_id).aggregate(
            total=Sum('trainer_earning')
        )['total'] or 0

        return Response({
            "status": "success",
            "code": "100",
            "dashboard": {
                "trainer_name": trainer.name,
                "total_clients": total_clients,
                "upcoming_sessions": upcoming_sessions,
                "today_sessions": SessionSerializer(today_sessions, many=True).data,
                "total_earnings": float(total_earnings)
            }
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


# ==================== OWNER/MANAGER APIs ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_branches(request):
    """Get all branches"""
    try:
        branches = Branch.objects.all()
        return Response({
            "status": "success",
            "code": "100",
            "branches": BranchSerializer(branches, many=True).data
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])
def create_branch(request):
    """Create a new branch"""
    try:
        name = request.data.get('name')
        location = request.data.get('location')
        city = request.data.get('city')
        state = request.data.get('state')
        zip_code = request.data.get('zip_code')

        if not all([name, location, city, state]):
            return Response({"error": "name, location, city, state are required", "code": "400"}, status=400)

        branch = Branch.objects.create(
            name=name,
            location=location,
            city=city,
            state=state,
            zip_code=zip_code or ''
        )

        return Response({
            "status": "success",
            "message": "Branch created",
            "code": "100",
            "branch": BranchSerializer(branch).data
        }, status=201)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])
def update_branch(request):
    """Update a branch"""
    try:
        branch_id = request.data.get('branch_id')

        if not branch_id:
            return Response({"error": "branch_id is required", "code": "400"}, status=400)

        branch = Branch.objects.filter(id=branch_id).first()
        if not branch:
            return Response({"error": "Branch not found", "code": "400"}, status=400)

        if 'name' in request.data:
            branch.name = request.data['name']
        if 'location' in request.data:
            branch.location = request.data['location']
        if 'city' in request.data:
            branch.city = request.data['city']
        if 'state' in request.data:
            branch.state = request.data['state']
        if 'zip_code' in request.data:
            branch.zip_code = request.data['zip_code']

        branch.save()

        return Response({
            "status": "success",
            "message": "Branch updated",
            "code": "100",
            "branch": BranchSerializer(branch).data
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_branch(request):
    """Delete a branch"""
    try:
        branch_id = request.query_params.get('branch_id')

        if not branch_id:
            return Response({"error": "branch_id is required", "code": "400"}, status=400)

        branch = Branch.objects.filter(id=branch_id).first()
        if not branch:
            return Response({"error": "Branch not found", "code": "400"}, status=400)

        branch.delete()

        return Response({
            "status": "success",
            "message": "Branch deleted",
            "code": "100"
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


# ==================== INVOICE APIs ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_invoices(request):
    """Get invoices"""
    try:
        branch_id = request.query_params.get('branch_id')
        customer_id = request.query_params.get('customer_id')

        invoices = Invoice.objects.all().order_by('-created_at')

        if branch_id:
            invoices = invoices.filter(branch_id=branch_id)
        if customer_id:
            invoices = invoices.filter(customer_id=customer_id)

        return Response({
            "status": "success",
            "code": "100",
            "invoices": InvoiceSerializer(invoices, many=True).data
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])
def create_invoice(request):
    """Create an invoice"""
    try:
        customer_id = request.data.get('customer_id')
        branch_id = request.data.get('branch_id')
        items = request.data.get('items', [])
        gst_percent = request.data.get('gst_percent', 18)
        notes = request.data.get('notes', '')

        if not customer_id or not items:
            return Response({"error": "customer_id and items are required", "code": "400"}, status=400)

        customer = Customer.objects.filter(id=customer_id).first()
        if not customer:
            return Response({"error": "Customer not found", "code": "400"}, status=400)

        branch = None
        if branch_id:
            branch = Branch.objects.filter(id=branch_id).first()

        # Calculate totals
        subtotal = sum(Decimal(str(item.get('price', 0))) * int(item.get('quantity', 1)) for item in items)
        gst_amount = subtotal * (Decimal(str(gst_percent)) / 100)
        total_amount = subtotal + gst_amount

        invoice = Invoice.objects.create(
            customer=customer,
            branch=branch,
            items=items,
            subtotal=subtotal,
            gst_percent=gst_percent,
            gst_amount=gst_amount,
            total_amount=total_amount,
            notes=notes
        )

        return Response({
            "status": "success",
            "message": "Invoice created",
            "code": "100",
            "invoice": InvoiceSerializer(invoice).data
        }, status=201)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


# ==================== ANNOUNCEMENT APIs ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_announcements(request):
    """Get announcements"""
    try:
        branch_id = request.query_params.get('branch_id')
        audience = request.query_params.get('audience')

        announcements = Announcement.objects.filter(is_active=True)

        if branch_id:
            announcements = announcements.filter(branch_id=branch_id)
        if audience:
            announcements = announcements.filter(audience__in=[audience, 'ALL'])

        return Response({
            "status": "success",
            "code": "100",
            "announcements": AnnouncementSerializer(announcements, many=True).data
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])
def create_announcement(request):
    """Create an announcement"""
    try:
        title = request.data.get('title')
        message = request.data.get('message')
        audience = request.data.get('audience', 'ALL')
        branch_id = request.data.get('branch_id')
        created_by_id = request.data.get('created_by_id')

        if not title or not message:
            return Response({"error": "title and message are required", "code": "400"}, status=400)

        branch = None
        if branch_id:
            branch = Branch.objects.filter(id=branch_id).first()

        created_by = None
        if created_by_id:
            created_by = Customer.objects.filter(id=created_by_id).first()

        announcement = Announcement.objects.create(
            title=title,
            message=message,
            audience=audience,
            branch=branch,
            created_by=created_by
        )

        return Response({
            "status": "success",
            "message": "Announcement created",
            "code": "100",
            "announcement": AnnouncementSerializer(announcement).data
        }, status=201)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_announcement(request):
    """Delete an announcement"""
    try:
        announcement_id = request.query_params.get('announcement_id')

        if not announcement_id:
            return Response({"error": "announcement_id is required", "code": "400"}, status=400)

        announcement = Announcement.objects.filter(id=announcement_id).first()
        if not announcement:
            return Response({"error": "Announcement not found", "code": "400"}, status=400)

        announcement.delete()

        return Response({
            "status": "success",
            "message": "Announcement deleted",
            "code": "100"
        }, status=200)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)


# ==================== REPORTS APIs ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_reports(request):
    """Get reports data"""
    try:
        branch_id = request.query_params.get('branch_id')
        report_type = request.query_params.get('type', 'overview')  # overview, attendance, revenue

        filters = {}
        if branch_id:
            filters['branch_id'] = branch_id

        if report_type == 'overview':
            total_sessions = Session.objects.filter(**filters).count()
            completed_sessions = Session.objects.filter(status='Completed', **filters).count()
            cancelled_sessions = Session.objects.filter(status='Cancelled', **filters).count()
            total_trainers = Customer.objects.filter(role='TRAINER', **filters).count()
            total_clients = Customer.objects.filter(role='CLIENT', **filters).count()

            return Response({
                "status": "success",
                "code": "100",
                "report": {
                    "type": "overview",
                    "total_sessions": total_sessions,
                    "completed_sessions": completed_sessions,
                    "cancelled_sessions": cancelled_sessions,
                    "completion_rate": round((completed_sessions / total_sessions * 100) if total_sessions > 0 else 0, 1),
                    "total_trainers": total_trainers,
                    "total_clients": total_clients
                }
            }, status=200)

        elif report_type == 'revenue':
            total_revenue = TrainerEarning.objects.filter(**filters).aggregate(
                total=Sum('session_amount')
            )['total'] or 0
            trainer_payouts = TrainerEarning.objects.filter(**filters).aggregate(
                total=Sum('trainer_earning')
            )['total'] or 0
            gym_revenue = TrainerEarning.objects.filter(**filters).aggregate(
                total=Sum('gym_earning')
            )['total'] or 0

            return Response({
                "status": "success",
                "code": "100",
                "report": {
                    "type": "revenue",
                    "total_revenue": float(total_revenue),
                    "trainer_payouts": float(trainer_payouts),
                    "gym_revenue": float(gym_revenue)
                }
            }, status=200)

        return Response({"error": "Invalid report type", "code": "400"}, status=400)
    except Exception as e:
        return Response({"error": str(e), "code": "400"}, status=400)