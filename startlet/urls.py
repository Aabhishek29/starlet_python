from django.urls import path
from . import views as view


urlpatterns = [
    path('', view.home, name='home'),
    path('api/testing/', view.test, name='test'),
    path('api/send-otp/', view.send_otp_view, name='send_otp'),
    path('api/verify-otp/', view.verify_otp_view, name='verify_otp'),

    # Slot Management APIs (Manager/Trainer)
    path('api/slots/generate/', view.generate_slots, name='generate_slots'),
    path('api/slots/', view.get_slots, name='get_slots'),
    path('api/slots/week/', view.get_week_slots, name='get_week_slots'),
    path('api/slots/block/', view.block_slot, name='block_slot'),
    path('api/slots/block-range/', view.block_time_range, name='block_time_range'),
    path('api/slots/day-off/', view.set_day_off, name='set_day_off'),
    path('api/slots/config/', view.get_slot_config, name='get_slot_config'),
    path('api/slots/config/update/', view.update_slot_config, name='update_slot_config'),

    # Client APIs
    path('api/client/profile/', view.get_client_profile, name='client_profile'),
    path('api/client/profile/update/', view.update_client_profile, name='update_client_profile'),
    path('api/client/available-slots/', view.get_client_available_slots, name='client_available_slots'),
    path('api/client/sessions/', view.get_client_sessions, name='client_sessions'),
    path('api/sessions/book/', view.book_session, name='book_session'),
    path('api/sessions/cancel/', view.cancel_session, name='cancel_session'),

    # Trainer APIs
    path('api/trainer/dashboard/', view.get_trainer_dashboard, name='trainer_dashboard'),
    path('api/trainer/assigned-sessions/', view.get_trainer_assigned_sessions, name='trainer_assigned_sessions'),
    path('api/trainer/upcoming-sessions/', view.get_trainer_upcoming_sessions, name='trainer_upcoming_sessions'),
    path('api/trainer/earnings/', view.get_trainer_earnings, name='trainer_earnings'),
    path('api/trainer/start-session/', view.start_session, name='start_session'),
    path('api/trainer/end-session/', view.end_session, name='end_session'),
    path('api/trainer/client-bca/', view.get_client_bca, name='get_client_bca'),
    path('api/trainer/sync-bca/', view.sync_client_bca, name='sync_client_bca'),
    path('api/trainer/preview-bca/', view.fetch_bca_preview, name='preview_bca'),
    path('api/trainer/update-measurements/', view.update_client_measurements, name='update_measurements'),

    # Manager Dashboard APIs
    path('api/manager/dashboard/', view.get_manager_dashboard, name='manager_dashboard'),
    path('api/manager/sessions/', view.get_branch_sessions, name='branch_sessions'),
    path('api/manager/trainers/', view.get_branch_trainers, name='branch_trainers'),
    path('api/manager/clients/', view.get_branch_clients, name='branch_clients'),
    path('api/manager/enroll-client/', view.enroll_client, name='enroll_client'),
    path('api/manager/enroll-trainer/', view.enroll_trainer, name='enroll_trainer'),
    path('api/manager/trainer-sessions/', view.get_trainer_sessions, name='trainer_sessions'),

    # Branch CRUD APIs (Owner)
    path('api/branches/', view.get_branches, name='get_branches'),
    path('api/branches/create/', view.create_branch, name='create_branch'),
    path('api/branches/update/', view.update_branch, name='update_branch'),
    path('api/branches/delete/', view.delete_branch, name='delete_branch'),

    # Invoice APIs
    path('api/invoices/', view.get_invoices, name='get_invoices'),
    path('api/invoices/create/', view.create_invoice, name='create_invoice'),

    # Announcement APIs
    path('api/announcements/', view.get_announcements, name='get_announcements'),
    path('api/announcements/create/', view.create_announcement, name='create_announcement'),
    path('api/announcements/delete/', view.delete_announcement, name='delete_announcement'),

    # Reports APIs
    path('api/reports/', view.get_reports, name='get_reports'),
]
