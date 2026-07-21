from django.db import models
from django.contrib.auth.models import User


class Branch(models.Model):
    INDIAN_STATES = [
        ("Andhra Pradesh", "Andhra Pradesh"),
        ("Arunachal Pradesh", "Arunachal Pradesh"),
        ("Assam", "Assam"),
        ("Bihar", "Bihar"),
        ("Chhattisgarh", "Chhattisgarh"),
        ("Goa", "Goa"),
        ("Gujarat", "Gujarat"),
        ("Haryana", "Haryana"),
        ("Himachal Pradesh", "Himachal Pradesh"),
        ("Jharkhand", "Jharkhand"),
        ("Karnataka", "Karnataka"),
        ("Kerala", "Kerala"),
        ("Madhya Pradesh", "Madhya Pradesh"),
        ("Maharashtra", "Maharashtra"),
        ("Manipur", "Manipur"),
        ("Meghalaya", "Meghalaya"),
        ("Mizoram", "Mizoram"),
        ("Nagaland", "Nagaland"),
        ("Odisha", "Odisha"),
        ("Punjab", "Punjab"),
        ("Rajasthan", "Rajasthan"),
        ("Sikkim", "Sikkim"),
        ("Tamil Nadu", "Tamil Nadu"),
        ("Telangana", "Telangana"),
        ("Tripura", "Tripura"),
        ("Uttar Pradesh", "Uttar Pradesh"),
        ("Uttarakhand", "Uttarakhand"),
        ("West Bengal", "West Bengal"),
    ]

    name = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, choices=INDIAN_STATES)
    zip_code = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.name} - {self.city}"


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('SUPERADMIN', 'Super Admin'),
        ('FRANCHISEADMIN', 'Franchise Admin'),
        ('BRANCHADMIN', 'Branch Admin'),
        ('MANAGER', 'Branch Manager'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    # Only Manager will have a branch, SuperAdmin can have null
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managers'
    )

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Customer(models.Model):
    ROLE_CHOICES = [
        ('TRAINER', 'Trainer'),
        ('CLIENT', 'Client'),
        ('MANAGER', 'Manager'),
    ]
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customers'
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='CLIENT')
    otp = models.CharField(max_length=6, null=True, blank=True)
    is_partner = models.BooleanField(default=False)

    partner_id = models.CharField(max_length=50, null=True, blank=True)

    height_cm = models.FloatField(null=True, blank=True)
    weight_kg = models.FloatField(null=True, blank=True)

    measurements_chest_cm = models.FloatField(null=True, blank=True)
    measurements_upper_waist_cm = models.FloatField(null=True, blank=True)
    measurements_lower_waist_cm = models.FloatField(null=True, blank=True)
    measurements_mid_waist_cm = models.FloatField(null=True, blank=True)
    measurements_rightThigh_cm = models.FloatField(null=True, blank=True)
    measurements_leftThigh_cm = models.FloatField(null=True, blank=True)

    measurements_rightArm_cm = models.FloatField(null=True, blank=True)
    measurements_leftArm_cm = models.FloatField(null=True, blank=True)

    bca_weight_kg = models.FloatField(null=True, blank=True)
    bca_bmi = models.FloatField(null=True, blank=True)
    bca_bodyFat_percent = models.FloatField(null=True, blank=True)
    bca_muscleMass_kg = models.FloatField(null=True, blank=True)
    bca_subcutaneousFat_percent = models.FloatField(null=True, blank=True)
    bca_visceralFat_level = models.FloatField(null=True, blank=True)
    bca_bodyAge_years = models.FloatField(null=True, blank=True)
    bca_bmr_kcal = models.FloatField(null=True, blank=True)

    bca_skeletalMass_kg = models.FloatField(null=True, blank=True)
    bca_muscleMass_percent = models.FloatField(null=True, blank=True)
    bca_boneMass_kg = models.FloatField(null=True, blank=True)
    bca_protein_kg = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.role})"


class SubscriptionPlan(models.Model):
    DURATION_TYPE_CHOICES = (
        ('month', 'Month'),
        ('year', 'Year'),
    )

    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.IntegerField()  # e.g. 1,3,12
    duration_type = models.CharField(max_length=10, choices=DURATION_TYPE_CHOICES)
    features = models.TextField(blank=True, null=True)  # comma-separated list
    status = models.BooleanField(default=True)  # active/inactive
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    

class CustomerSubscription(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)
    auto_renew = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.email} - {self.plan.name}"



class Session(models.Model):
    PERSON_COUNT_OPTIONS = [
        (1, 'Single Person'),
        (2, 'Two Persons'),
        (3, 'Group Session'),
    ]
    STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    person_count = models.IntegerField(choices=PERSON_COUNT_OPTIONS, default=1)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="sessions")
    trainer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name="trainer_sessions")
    session_date = models.DateTimeField()
    session_started_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Scheduled')
    notes = models.TextField(blank=True, null=True)
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session for {self.customer.email} on {self.session_date.strftime('%Y-%m-%d %H:%M')}"
    


class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('SUBSCRIPTION', 'Subscription'),
        ('SESSION', 'Session'),
        ('OTHER', 'Other')
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    transaction_date = models.DateTimeField(auto_now_add=True)
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    subscription_plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    transaction_reference = models.CharField(max_length=100, null=True, blank=True)
    gst_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    invoice_number = models.CharField(max_length=100, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    def __str__(self):
        return f"Transaction of {self.amount} for {self.customer.email} on {self.transaction_date.strftime('%Y-%m-%d')}"


class TimeSlot(models.Model):
    """Individual 30-min slots for each day at a branch"""
    SLOT_STATUS = [
        ('AVAILABLE', 'Available'),
        ('BOOKED', 'Booked'),
        ('BLOCKED', 'Blocked'),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='time_slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=10, choices=SLOT_STATUS, default='AVAILABLE')
    booked_by = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='booked_slots'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['branch', 'date', 'start_time']
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.branch.name} - {self.date} {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')} ({self.status})"


class DayOff(models.Model):
    """Mark entire day as off for a branch"""
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='days_off')
    date = models.DateField()
    reason = models.CharField(max_length=255, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['branch', 'date']

    def __str__(self):
        return f"{self.branch.name} - Day Off on {self.date}"


class SlotConfig(models.Model):
    """Default slot configuration for a branch (operating hours)"""
    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='slot_configs')
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    morning_start = models.TimeField(default='06:00')
    morning_end = models.TimeField(default='11:30')
    evening_start = models.TimeField(default='16:00')
    evening_end = models.TimeField(default='20:00')
    is_active = models.BooleanField(default=True)  # False = day off by default

    class Meta:
        unique_together = ['branch', 'weekday']

    def __str__(self):
        day_name = dict(self.WEEKDAY_CHOICES)[self.weekday]
        return f"{self.branch.name} - {day_name}"


class Invoice(models.Model):
    """Invoice for customer payments"""
    invoice_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='invoices')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, related_name='invoices')

    items = models.JSONField(default=list)  # [{description, quantity, price}]
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=18)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name='created_invoices')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            import uuid
            self.invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice_number} - {self.customer.name}"


class Announcement(models.Model):
    """Announcements from admin/manager"""
    AUDIENCE_CHOICES = [
        ('ALL', 'All Users'),
        ('TRAINERS', 'Trainers Only'),
        ('CLIENTS', 'Clients Only'),
    ]

    title = models.CharField(max_length=200)
    message = models.TextField()
    audience = models.CharField(max_length=10, choices=AUDIENCE_CHOICES, default='ALL')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True, related_name='announcements')

    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name='created_announcements')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.audience})"


class TrainerEarning(models.Model):
    """Track trainer earnings per session"""
    trainer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='earnings')
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='trainer_earnings')

    session_amount = models.DecimalField(max_digits=10, decimal_places=2)
    trainer_percent = models.DecimalField(max_digits=5, decimal_places=2, default=50)
    trainer_earning = models.DecimalField(max_digits=10, decimal_places=2)
    gym_earning = models.DecimalField(max_digits=10, decimal_places=2)

    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.trainer_earning = self.session_amount * (self.trainer_percent / 100)
        self.gym_earning = self.session_amount - self.trainer_earning
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.trainer.name} - ₹{self.trainer_earning}"