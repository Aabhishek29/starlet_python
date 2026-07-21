from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import (
    Branch, UserProfile, Customer, SubscriptionPlan, CustomerSubscription, Session, Transaction,
    TimeSlot, DayOff, SlotConfig, Invoice, Announcement, TrainerEarning,
)

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline, )
    list_display = ('username', 'email', 'is_staff', 'get_role', 'get_branch')
    list_filter = ('is_staff', 'userprofile__role', 'userprofile__branch')

    def get_role(self, obj):
        return obj.userprofile.role if hasattr(obj, 'userprofile') else "-"
    get_role.short_description = 'Role'

    def get_branch(self, obj):
        return obj.userprofile.branch if hasattr(obj, 'userprofile') else "-"
    get_branch.short_description = 'Branch'


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'state')
    search_fields = ('name', 'city', 'state')
    list_filter = ('state',)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'role', 'branch', 'is_partner')
    list_filter = ('role', 'branch', 'is_partner')
    search_fields = ('name', 'email', 'phone')


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration', 'duration_type', 'status')
    list_filter = ('duration_type', 'status')
    search_fields = ('name',)


@admin.register(CustomerSubscription)
class CustomerSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('customer', 'plan', 'start_date', 'end_date', 'active')
    list_filter = ('active', 'plan')
    search_fields = ('customer__email',)

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('customer', 'trainer', 'session_date', 'status', 'branch')
    list_filter = ('status', 'branch')
    search_fields = ('customer__email', 'trainer__email')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('customer', 'amount', 'transaction_type', 'transaction_date', 'branch', 'subscription_plan')
    list_filter = ('transaction_type', 'branch')
    search_fields = ('customer__email', 'transaction_reference', 'invoice_number')


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('branch', 'date', 'start_time', 'end_time', 'status', 'booked_by')
    list_filter = ('status', 'branch', 'date')
    search_fields = ('branch__name', 'booked_by__email')


@admin.register(DayOff)
class DayOffAdmin(admin.ModelAdmin):
    list_display = ('branch', 'date', 'reason', 'created_by')
    list_filter = ('branch',)
    search_fields = ('branch__name', 'reason')


@admin.register(SlotConfig)
class SlotConfigAdmin(admin.ModelAdmin):
    list_display = ('branch', 'weekday', 'morning_start', 'morning_end', 'evening_start', 'evening_end', 'is_active')
    list_filter = ('branch', 'weekday', 'is_active')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer', 'branch', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'branch')
    search_fields = ('invoice_number', 'customer__email', 'customer__name')


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'audience', 'branch', 'is_active', 'created_by', 'created_at')
    list_filter = ('audience', 'is_active', 'branch')
    search_fields = ('title', 'message')


@admin.register(TrainerEarning)
class TrainerEarningAdmin(admin.ModelAdmin):
    list_display = ('trainer', 'session', 'session_amount', 'trainer_earning', 'gym_earning', 'is_paid', 'paid_at')
    list_filter = ('is_paid',)
    search_fields = ('trainer__email', 'trainer__name')
