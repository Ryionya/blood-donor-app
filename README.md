# 🩸 BloodLink — Blood Donor Finding Web Application

> "A dating app for blood donation" — connecting verified donors with recipients in need across Laguna, Philippines.

**Live Demo:** [https://appdev-bloodlink-ph.up.railway.app](https://appdev-bloodlink-ph.up.railway.app)

---

## 📋 Table of Contents
- [About the Project](#-about-the-project)
- [Features](#-features)
- [Tech Stack](#️-tech-stack)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [Usage](#-usage)
- [Known Limitations](#-known-limitations)
- [Future Improvements](#-future-improvements)
- [Team](#-team)

---

## 📌 About the Project

BloodLink is a Django-based Progressive Web Application (PWA) that connects blood donors with recipients. The system streamlines the blood donation process by providing a verified donor registry, a structured request workflow, real-time chat, AI-powered recommendations, and voice control navigation in both Filipino and English.

Built as a final project for **Applications Development and Emerging Technologies** at **Polytechnic University of the Philippines – Santa Rosa Campus (PUPSRC)**, Academic Year 2025–2026.

> BloodLink currently serves **Laguna, Philippines** as its initial target area, with plans to expand province by province in future iterations.

---

## ✨ Features

### User Roles
- **Donor** — Register, apply for verification with government ID and medical certificate, toggle availability, track 56-day donation cooldown, log completed donations with proof document
- **Recipient** — Browse verified donors by blood type and location, send blood requests, communicate with accepted donors via in-app chat
- **Admin** — Review and approve/reject donor applications, verify donation logs, manage users, monitor system statistics

### Core Features
- 🔍 Browse and filter verified donors by blood type and location
- 🩸 Blood request system with admin review workflow and urgency detection
- 💬 Real-time chat between donor and recipient after request acceptance
- 🔔 Push notifications for requests, acceptances, and application status updates
- 🎤 Voice control navigation and search (Filipino/English) powered by Web Speech API
- 🤖 AI-powered donor match recommendations and voice intent parsing (Groq AI)
- 📱 PWA — installable on mobile and desktop with offline support
- ☁️ Cloudinary media storage for uploaded documents and profile pictures
- 🔐 Forgot password via email (Gmail SMTP)
- 👤 Role switching — donors can temporarily browse as recipients

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6.0.5 (Python) |
| Database | PostgreSQL (Railway) |
| Frontend | Bootstrap 5, JavaScript |
| AI | Groq API (llama-3.3-70b-versatile) |
| Media Storage | Cloudinary |
| Deployment | Railway |
| PWA | django-pwa, django-webpush |
| Voice | Web Speech API |
| Email | Gmail SMTP |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL
- Git
- Google Chrome or Microsoft Edge (for voice control)

### Installation

**1. Clone the repository:**
```bash
git clone https://github.com/Ryionya/blood-donor-app.git
cd blood-donor-app
```

**2. Create and activate virtual environment:**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

**3. Install dependencies:**
```bash
pip install -r requirements.txt
```

**4. Create `.env` file** — see [Environment Variables](#-environment-variables)

**5. Run migrations:**
```bash
python manage.py migrate
```

**6. Create superuser:**
```bash
python manage.py createsuperuser
```

**7. Run the development server:**
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` to access the app.

---

## 🔐 Environment Variables

Create a `.env` file in the project root:

```env
# Django
SECRET_KEY=your_secret_key_here
DEBUG=True

# Database (PostgreSQL)
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# Cloudinary (Media Storage)
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Groq AI
GROQ_API_KEY=your_groq_api_key

# Email (Gmail SMTP)
EMAIL_HOST_USER=your_gmail@gmail.com
EMAIL_HOST_PASSWORD=your_16_char_app_password

# VAPID Keys (Push Notifications)
VAPID_PUBLIC_KEY=your_vapid_public_key
VAPID_PRIVATE_KEY=your_vapid_private_key
VAPID_ADMIN_EMAIL=your_email@gmail.com
```

> ⚠️ Never commit your `.env` file to GitHub. It is already included in `.gitignore`.

---

## 📖 Usage

### Voice Commands

| Command (English)     | Command (Filipino)                  | Action                   |
|---|---|---|
| "Go to browse page"   | "Pumunta sa browse"                 | Navigate to donor list   |
| "Find A+ in Calamba"  | "Hanapin ang A positive sa Calamba" | Search donors            |
| "My requests"         | "Aking mga kahilingan"              | View sent requests       |
| "Incoming requests"   | "Mga natanggap na kahilingan"       | View received requests   |
| "Log donation"        | "Mag-log ng donasyon"               | Log a completed donation |
| "Switch to recipient" | "Mag-switch sa recipient"           | Switch active role       |
| "Logout"              | "Mag-logout"                        | Log out                  |

### Donor Verification Flow
1. Register as Donor
2. Complete profile setup
3. Submit donor application with Government ID and Medical Certificate
4. Wait for admin approval
5. Receive verified badge — now visible on browse page

### Blood Request Flow
1. Recipient browses verified donors
2. Sends a blood request with hospital details and medical certificate
3. Admin reviews the request
4. Donor accepts or declines
5. If accepted — contact info revealed and chat enabled

---

## ⚠️ Known Limitations

- Voice control requires **Google Chrome** or **Microsoft Edge** (Web Speech API limitation)
- Location filtering is currently scoped to **Laguna, Philippines** only
- Chat uses **simple polling** (every 3 seconds) instead of WebSockets
- Media files use **Cloudinary free tier** — 25GB storage limit
- PDF delivery requires Cloudinary PDF delivery to be enabled in account settings
- Push notifications require **HTTPS** — fully functional on Railway deployment

---

## 🔮 Future Improvements

- Expand location support to all provinces in the Philippines
- Implement **Django Channels + WebSockets** for true real-time chat
- Add **blood type compatibility matrix** for smarter donor filtering
- Integrate **AWS S3** as an alternative media storage option
- Add **two-factor authentication** for enhanced security
- Build a **React Native or Flutter** mobile app
- Implement **recipient medical certificate** requirement per blood request
- Add **donation history export** as PDF report

---

## 👥 Team

| Member | Name | Role |
|---|---|---|
| M1 | John Rycel V. Sumiran | Backend, Database, AI Integration, Voice Control, Deployment |
| M2 | Nash Dave E. Mendoza | Authentication, Admin Panel, Donor Application |
| M3 | Jericho E. Mendez | Recipient Side, Browse & Matching, UI |
| M4 | Gabriel Antonio B. Jose | PWA, Push Notifications, Donor Dashboard |

**Course:** Applications Development and Emerging Technologies
**Institution:** Polytechnic University of the Philippines – Santa Rosa Campus (PUPSRC)
**Section:** BSIT 3-2
**Academic Year:** 2025–2026

---

## 📄 License

This project was developed for educational purposes as part of the BSIT curriculum at PUP Santa Rosa Campus. All rights reserved by the development team.