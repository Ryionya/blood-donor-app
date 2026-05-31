"""
BloodLink — Demo Seed Script
Run with: python manage.py shell < seed_demo.py

Creates:
  - 1 superuser/admin
  - 8 verified donors (one per blood type, spread across Laguna cities)
  - 2 unverified/pending donors
  - 4 recipients
  - Blood requests in various statuses
  - Notifications
"""

from django.contrib.auth import get_user_model
from donors.models import DonorProfile, DonorApplication, Notification
from recipients.models import BloodRequest, RecipientProfile
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

print("🩸 Starting BloodLink demo seed...")

# ─────────────────────────────────────────────
#  HELPER
# ─────────────────────────────────────────────

def make_user(username, password, role, first_name, last_name, location, phone, active_role=None):
    if User.objects.filter(username=username).exists():
        print(f"  ↩  {username} already exists, skipping.")
        return User.objects.get(username=username)
    user = User.objects.create_user(
        username=username,
        password=password,
        role=role,
        active_role=active_role or role,
        first_name=first_name,
        last_name=last_name,
        location=location,
        phone_number=phone,
        email=f"{username}@bloodlink.demo",
    )
    print(f"  ✅ Created user: {username} ({role})")
    return user


# ─────────────────────────────────────────────
#  ADMIN
# ─────────────────────────────────────────────

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        password='admin1234',
        email='admin@bloodlink.demo',
        role='admin',
        active_role='admin',
    )
    print("  ✅ Created superuser: admin / admin1234")
else:
    print("  ↩  admin already exists, skipping.")


# ─────────────────────────────────────────────
#  VERIFIED DONORS — one per blood type
# ─────────────────────────────────────────────

donor_data = [
    # (username, password, first, last, blood_type, location, phone, bio)
    ('juan_aplus',  'donor1234', 'Juan',    'dela Cruz',  'A+',  'Santa Rosa',  '09171234001', 'Happy to help anyone in need. Available most weekends.'),
    ('maria_aminus','donor1234', 'Maria',   'Santos',     'A-',  'Calamba',     '09171234002', 'Regular donor since 2022. A- is rare, reach out anytime.'),
    ('carlo_bplus', 'donor1234', 'Carlo',   'Reyes',      'B+',  'Biñan',       '09171234003', 'Gym-goer, healthy lifestyle. Happy to donate.'),
    ('liza_bminus', 'donor1234', 'Liza',    'Mercado',    'B-',  'Cabuyao',     '09171234004', 'B- donor. Available on weekdays.'),
    ('ramon_abplus','donor1234', 'Ramon',   'Garcia',     'AB+', 'San Pedro',   '09171234005', 'Universal plasma donor. Always ready.'),
    ('sofia_abminus','donor1234','Sofia',   'Torres',     'AB-', 'Calamba',     '09171234006', 'AB- is rare. I donate whenever I can.'),
    ('pedro_oplus', 'donor1234', 'Pedro',   'Villanueva', 'O+',  'Santa Rosa',  '09171234007', 'O+ available. Can donate on short notice.'),
    ('ana_ominus',  'donor1234', 'Ana',     'Lim',        'O-',  'Los Baños',   '09171234008', 'Universal donor. Available for emergencies.'),
]

for uname, pwd, fn, ln, bt, loc, phone, bio in donor_data:
    user = make_user(uname, pwd, 'donor', fn, ln, loc, phone)
    profile, created = DonorProfile.objects.get_or_create(user=user)
    if created or not profile.is_verified:
        profile.blood_type  = bt
        profile.location    = loc
        profile.is_verified = True
        profile.is_available = True
        profile.bio         = bio
        profile.save()
        print(f"    🩸 DonorProfile: {uname} ({bt}) — verified")


# ─────────────────────────────────────────────
#  PENDING DONORS — not yet verified
# ─────────────────────────────────────────────

pending_data = [
    ('ben_pending',  'donor1234', 'Benjamin', 'Cruz',   'B+', 'Cabuyao', '09181234001'),
    ('rosa_pending', 'donor1234', 'Rosario',  'Flores', 'O+', 'Biñan',   '09181234002'),
]

for uname, pwd, fn, ln, bt, loc, phone in pending_data:
    user = make_user(uname, pwd, 'donor', fn, ln, loc, phone)
    profile, created = DonorProfile.objects.get_or_create(user=user)
    if created or not profile.blood_type:
        profile.blood_type   = bt
        profile.location     = loc
        profile.is_verified  = False
        profile.is_available = False
        profile.save()
        print(f"    ⏳ DonorProfile: {uname} ({bt}) — pending")

    # Create a pending application
    if not user.applications.filter(status='pending').exists():
        DonorApplication.objects.create(
            donor=user,
            medical_certificate='applications/certs/sample.pdf',
            status='pending',
        )
        print(f"    📋 DonorApplication created for {uname}")


# ─────────────────────────────────────────────
#  RECIPIENTS
# ─────────────────────────────────────────────

recipient_data = [
    # (username, password, first, last, blood_type, location, phone)
    ('rec_aplus',   'recip1234', 'Ligaya',  'Bautista', 'A+',  'Santa Rosa', '09221234001'),
    ('rec_bplus',   'recip1234', 'Noel',    'Hernandez','B+',  'Calamba',    '09221234002'),
    ('rec_oplus',   'recip1234', 'Cynthia', 'Ramos',    'O+',  'Biñan',      '09221234003'),
    ('rec_abplus',  'recip1234', 'Dante',   'Aquino',   'AB+', 'San Pedro',  '09221234004'),
]

recipient_users = []
for uname, pwd, fn, ln, bt, loc, phone in recipient_data:
    user = make_user(uname, pwd, 'recipient', fn, ln, loc, phone)
    rp, created = RecipientProfile.objects.get_or_create(user=user)
    if created or not rp.blood_type:
        rp.blood_type = bt
        rp.save()
        print(f"    🏥 RecipientProfile: {uname} ({bt})")
    recipient_users.append(user)


# ─────────────────────────────────────────────
#  BLOOD REQUESTS
# ─────────────────────────────────────────────

print("\n  📨 Creating blood requests...")

def make_request(recipient_uname, donor_uname, hospital, urgency, message, status):
    try:
        recipient = User.objects.get(username=recipient_uname)
        donor     = User.objects.get(username=donor_uname)
    except User.DoesNotExist:
        print(f"    ⚠ Skipping request — user not found")
        return

    if BloodRequest.objects.filter(recipient=recipient, donor=donor).exists():
        print(f"    ↩  Request {recipient_uname}→{donor_uname} already exists")
        return

    BloodRequest.objects.create(
        recipient=recipient,
        donor=donor,
        hospital_name=hospital,
        urgency=urgency,
        message=message,
        status=status,
        responded_at=timezone.now() if status in ['accepted', 'declined'] else None,
    )
    print(f"    ✅ Request: {recipient_uname} → {donor_uname} ({status})")


# Accepted request — contact info revealed
make_request(
    'rec_aplus', 'juan_aplus',
    'De La Salle University Medical Center',
    'high',
    'My father needs A+ blood urgently for surgery tomorrow.',
    'accepted',
)

# Pending donor response
make_request(
    'rec_bplus', 'carlo_bplus',
    'Perpetual Help Medical Center',
    'critical',
    'Emergency — patient in ICU needs B+ immediately.',
    'pending',
)

# Pending admin review
make_request(
    'rec_oplus', 'pedro_oplus',
    'Laguna Provincial Hospital',
    'medium',
    'Scheduled surgery next week. O+ blood needed.',
    'pending_admin',
)

# Declined request
make_request(
    'rec_abplus', 'ramon_abplus',
    'St. Patrick Hospital Medical Center',
    'low',
    'Routine transfusion needed for my grandmother.',
    'declined',
)


# ─────────────────────────────────────────────
#  NOTIFICATIONS
# ─────────────────────────────────────────────

print("\n  🔔 Creating notifications...")

def make_notif(username, notif_type, message, is_read=False):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return
    if not Notification.objects.filter(user=user, message=message).exists():
        Notification.objects.create(
            user=user,
            notif_type=notif_type,
            message=message,
            is_read=is_read,
        )
        print(f"    🔔 Notif → {username}: {notif_type}")

# Donor notified of incoming request
make_notif('carlo_bplus',  'request',  'Noel Hernandez sent you a blood donation request for Perpetual Help Medical Center.')
make_notif('pedro_oplus',  'request',  'Cynthia Ramos sent you a blood donation request for Laguna Provincial Hospital.')

# Recipient notified of accepted request
make_notif('rec_aplus',    'accepted', 'Juan dela Cruz accepted your blood request. Contact info is now available.')

# Donor notified of application status
make_notif('ben_pending',  'approved', 'Your donor application is under review by our admin.')
make_notif('rosa_pending', 'approved', 'Your donor application is under review by our admin.')


# ─────────────────────────────────────────────
#  SUMMARY
# ─────────────────────────────────────────────

print("\n" + "─" * 50)
print("✅ Seed complete! Demo accounts:")
print("─" * 50)
print("  ADMIN      admin         / admin1234")
print("  DONORS     juan_aplus    / donor1234  (A+  — Santa Rosa)  ✅ verified")
print("             maria_aminus  / donor1234  (A-  — Calamba)     ✅ verified")
print("             carlo_bplus   / donor1234  (B+  — Biñan)       ✅ verified")
print("             liza_bminus   / donor1234  (B-  — Cabuyao)     ✅ verified")
print("             ramon_abplus  / donor1234  (AB+ — San Pedro)   ✅ verified")
print("             sofia_abminus / donor1234  (AB- — Calamba)     ✅ verified")
print("             pedro_oplus   / donor1234  (O+  — Santa Rosa)  ✅ verified")
print("             ana_ominus    / donor1234  (O-  — Los Baños)   ✅ verified")
print("             ben_pending   / donor1234  (B+  — Cabuyao)     ⏳ pending")
print("             rosa_pending  / donor1234  (O+  — Biñan)       ⏳ pending")
print("  RECIPIENTS rec_aplus     / recip1234  (A+  — Santa Rosa)")
print("             rec_bplus     / recip1234  (B+  — Calamba)")
print("             rec_oplus     / recip1234  (O+  — Biñan)")
print("             rec_abplus    / recip1234  (AB+ — San Pedro)")
print("─" * 50)
