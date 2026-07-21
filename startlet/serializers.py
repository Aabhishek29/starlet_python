from .models import Customer, TimeSlot, DayOff, SlotConfig, Branch, Session, Invoice, Announcement, TrainerEarning
from rest_framework import serializers


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'email', 'phone', 'branch', 'role', 'is_partner', 'partner_id']


class CustomerDetailSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'name', 'email', 'phone', 'branch', 'branch_name', 'role',
                  'is_partner', 'partner_id', 'height_cm', 'weight_kg', 'created_at']


class TrainerSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    total_sessions = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ['id', 'name', 'email', 'phone', 'branch', 'branch_name',
                  'is_partner', 'partner_id', 'total_sessions', 'created_at']

    def get_total_sessions(self, obj):
        return obj.trainer_sessions.count()


class SessionSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    trainer_name = serializers.CharField(source='trainer.name', read_only=True)
    trainer_phone = serializers.CharField(source='trainer.phone', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    class Meta:
        model = Session
        fields = ['id', 'customer', 'customer_name', 'customer_phone',
                  'trainer', 'trainer_name', 'trainer_phone',
                  'branch', 'branch_name', 'session_date', 'session_started_at',
                  'status', 'person_count', 'notes', 'created_at']


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ['id', 'name', 'location', 'city', 'state', 'zip_code']


class TimeSlotSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    booked_by_name = serializers.CharField(source='booked_by.name', read_only=True)
    customer_name = serializers.CharField(source='booked_by.name', read_only=True)
    customer_phone = serializers.CharField(source='booked_by.phone', read_only=True)

    class Meta:
        model = TimeSlot
        fields = ['id', 'branch', 'branch_name', 'date', 'start_time', 'end_time',
                  'status', 'booked_by', 'booked_by_name', 'customer_name', 'customer_phone', 'created_at']
        read_only_fields = ['id', 'created_at']


class DayOffSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    class Meta:
        model = DayOff
        fields = ['id', 'branch', 'branch_name', 'date', 'reason', 'created_at']
        read_only_fields = ['id', 'created_at']


class SlotConfigSerializer(serializers.ModelSerializer):
    weekday_name = serializers.SerializerMethodField()

    class Meta:
        model = SlotConfig
        fields = ['id', 'branch', 'weekday', 'weekday_name', 'morning_start',
                  'morning_end', 'evening_start', 'evening_end', 'is_active']

    def get_weekday_name(self, obj):
        return dict(SlotConfig.WEEKDAY_CHOICES).get(obj.weekday, '')


class InvoiceSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    class Meta:
        model = Invoice
        fields = ['id', 'invoice_number', 'customer', 'customer_name', 'customer_phone',
                  'branch', 'branch_name', 'items', 'subtotal', 'gst_percent', 'gst_amount',
                  'total_amount', 'status', 'notes', 'created_at']
        read_only_fields = ['id', 'invoice_number', 'created_at']


class AnnouncementSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)

    class Meta:
        model = Announcement
        fields = ['id', 'title', 'message', 'audience', 'branch', 'branch_name',
                  'is_active', 'created_by', 'created_by_name', 'created_at']
        read_only_fields = ['id', 'created_at']


class TrainerEarningSerializer(serializers.ModelSerializer):
    trainer_name = serializers.CharField(source='trainer.name', read_only=True)
    session_date = serializers.DateTimeField(source='session.session_date', read_only=True)
    customer_name = serializers.CharField(source='session.customer.name', read_only=True)

    class Meta:
        model = TrainerEarning
        fields = ['id', 'trainer', 'trainer_name', 'session', 'session_date', 'customer_name',
                  'session_amount', 'trainer_percent', 'trainer_earning', 'gym_earning',
                  'is_paid', 'paid_at', 'created_at']
        read_only_fields = ['id', 'trainer_earning', 'gym_earning', 'created_at']


class ClientProfileSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'name', 'email', 'phone', 'branch', 'branch_name', 'role',
                  'height_cm', 'weight_kg',
                  'measurements_chest_cm', 'measurements_upper_waist_cm',
                  'measurements_mid_waist_cm', 'measurements_lower_waist_cm',
                  'measurements_rightThigh_cm', 'measurements_leftThigh_cm',
                  'measurements_rightArm_cm', 'measurements_leftArm_cm',
                  'bca_weight_kg', 'bca_bmi', 'bca_bodyFat_percent',
                  'bca_muscleMass_kg', 'bca_muscleMass_percent',
                  'bca_subcutaneousFat_percent', 'bca_visceralFat_level',
                  'bca_bodyAge_years', 'bca_bmr_kcal', 'bca_skeletalMass_kg',
                  'bca_boneMass_kg', 'bca_protein_kg',
                  'created_at', 'updated_at']