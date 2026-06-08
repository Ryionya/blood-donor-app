import os
from groq import Groq
import re

def get_client():
    api_key = os.getenv('GROQ_API_KEY')

    if not api_key:
        return None

    return Groq(api_key=api_key)

# All navigable pages with their URL names and descriptions
NAVIGATION_PAGES = {
    # Accounts (Donors & Recipients)
    'browse_donors':            'Browse Donors, I want to find a donor, show me available donors, looking for blood, find someone who can donate, create a new request, maghanap ng donor, hanapin ang donor',
    'my_requests':              'My Requests, show me the requests I sent, what requests did I make, aking mga request, mga request na sinend ko',
    'incoming_requests':        'Incoming Requests, someone requested from me, who wants my blood, may nag-request sa akin, mga natanggap na request',
    'cooldown_status':          'Cooldown Status, can I donate again, when can I donate next, how long is my cooldown, cooldown ko, kailan ako makakapag-donate ulit',
    'log_donation':             'Log a Donation, I just donated, I already gave blood, record my donation, nag-donate na ako, I donated today',
    'my_application':           'My Application, what is my application status, did my application get approved, status ng application ko',
    'apply_donor':              'Apply as Donor, I want to become a donor, how do I apply, mag-apply bilang donor, gusto kong mag-donate',
    'profile_setup':            'Edit Profile, My Profile, update my info, change my details, i-edit ang profile ko, baguhin ang profile',
    'change_password':          'Change Password, I want to change my password, update my password, palitan ang password ko',
    'faq':                      'FAQ, How it Works, how does this work, I have questions, paano gumagana ito, mga tanong',
    'notifications_page':       'Notifications, show my notifications, any new alerts, mga notipikasyon ko, may bago bang notipikasyon',
    'switch_role':              'Switch Role, I want to be a donor instead, change to recipient, palitan ang role ko, maging donor, maging recipient',
    'send_request':             'Send Request, I want to ask this donor for blood, request blood from this person, mag-request ng dugo, humingi ng donation',
    'download_card':            'Download Card, Donor Card, I want my donor card, print my donor card, i-download ang donor card ko, i-print ang card',
    'logout':                   'Logout, Log Out, I want to sign out, mag-logout, lumabas',

    # Home
    'home':                     'Home, go home, take me to the main page, back to home, pumunta sa home',

    # Admin
    'admin_dashboard':          'Admin Dashboard, go to the dashboard, open admin panel, show me the overview',
    'admin_application_queue':  'Application Queue, show pending applications, who applied, review donor applications, mga aplikasyong naghihintay',
    'admin_manage_users':       'Manage Users, show all accounts, I want to manage users',
    'admin_donor_list':         'Donor List, show all verified donors, who are the donors, lahat ng donor',
    'admin_stats':              'Stats, Statistics, show me the stats, reports, how many donations, mga istatistika',
    'admin_request_queue':      'Request Queue, show pending blood requests, mga kahilingang naghihintay',
    'admin_user_list':          'User List, show all users, full user list, lahat ng users',
    'admin_donation_log_queue': 'Donation Logs, show donation logs, review donation records, pending donation logs',
}


def parse_voice_intent(transcript, user_role, active_role):
    """
    Use Groq to parse the user's voice command and determine intent.
    Returns a dict with 'type' and relevant data.
    """

    client = get_client()
    if not client:
        return {'type': 'unknown'}
    
    pages_description = '\n'.join(
        [f'- {name}: {desc}' for name, desc in NAVIGATION_PAGES.items()]
    )

    system_prompt = f"""You are a voice command interpreter for BloodLink, a blood donor finding web app.
The user is logged in as a '{user_role}' with active role '{active_role}'.

Your job is to interpret voice commands in Filipino or English and return a JSON response.

Available navigation pages:
{pages_description}

Blood types: A+, A-, B+, B-, AB+, AB-, O+, O-
Rules for blood type extraction:
- ALWAYS include the letter (A, B, AB, O) AND the sign (+/-)
- "a positive" = A+, "b negative" = B-, "o positive" = O+, "ab positive" = AB+
- Filipino: "a positibo" = A+, "b negatibo" = B-, "o positibo" = O+
- NEVER return just "positive" or "negative" without the blood type letter
- If only sign is mentioned without letter, return empty blood_type

Return ONLY a valid JSON object in one of these formats:

For navigation:
{{"type": "navigate", "page": "url_name_here"}}

For donor search on browse page:
{{"type": "search", "blood_type": "A+", "location": "Calamba"}}
Note: blood_type and location are optional - only include if mentioned.

For search with only blood type:
{{"type": "search", "blood_type": "O-", "location": ""}}

For search with only location:
{{"type": "search", "blood_type": "", "location": "Santa Rosa"}}

For viewing a specific donor profile:
{{"type": "donor_search", "name": "donor name here"}}

For sending a donation request to current donor:
{{"type": "donor_action", "action": "send_request"}}

For downloading/printing donor card:
{{"type": "donor_action", "action": "download_card"}}

For logout:
{{"type": "logout"}}

For unrecognized commands:
{{"type": "unknown"}}

Rules:
- If the command mentions finding/searching/looking for donors or blood, return search type
- If the command mentions going to/opening/show a page, return navigate type
- Extract Philippine city/municipality names accurately
- Handle Filipino words: "pumunta" = go to, "hanapin" = find, "ipakita" = show, "mag-logout" = logout
- Handle mixed Filipino-English (Taglish)
- Return ONLY the JSON, no explanation, no markdown
- If the command mentions viewing, opening, or checking a specific donor by name, return donor_search type
- Extract the donor's name from the command
- Examples: "view Juan's profile", "open profile of Maria", "tingnan ang profile ni Carlo
- If the command mentions sending a request, asking for blood, or requesting donation, return donor_action with action send_request
- If the command mentions downloading, printing, or saving a donor card, return donor_action with action download_card
- These actions only make sense on a donor profile page
- Filipino: "mag-request" = send request, "i-download" = download, "i-print" = print"""

    try:
        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': f'Voice command: "{transcript}"'}
            ],
            max_tokens=100,
            temperature=0.1,
        )

        import json
        result = response.choices[0].message.content.strip()
        # Clean any markdown if present
        result = result.replace('```json', '').replace('```', '').strip()
        return json.loads(result)

    except Exception as e:
        return {'type': 'unknown'}


def get_donor_recommendation(donors, blood_type_needed, location):
    """
    Use Groq to recommend the best donor match from available donors.
    Returns a recommendation string.
    """
    
    client = get_client()
    if not client:
        return None
    
    if not donors:
        return None

    donor_list = []
    for d in donors[:10]:  # limit to top 10
        donor_list.append(
            f"- {d.user.get_full_name() or d.user.username}, "
            f"Blood Type: {d.blood_type}, "
            f"Location: {d.user.location or 'Unknown'}"
        )

    donors_text = '\n'.join(donor_list)

    prompt = f"""You are a blood donor matching assistant for BloodLink.

A recipient needs blood type: {blood_type_needed or 'Any'}
Location preference: {location or 'Any'}

Available verified donors:
{donors_text}

Give a short 1-2 sentence recommendation on the best match and why.
Be concise, helpful, and compassionate. 
Write in simple English that Filipino users can understand.
Do not include donor names — just describe the best match characteristics."""

    try:
        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=150,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    except Exception:
        return None

def fix_year_mishear(transcript: str) -> str:
    """
    Fix common speech recognition mishearing of years.
    "2016" → "2026", "2015" → "2025", etc.
    """
    current_year = __import__('datetime').date.today().year

    def replace_year(match):
        year = int(match.group())
        if year < current_year:
            corrected = year + 10
            if abs(corrected - current_year) <= 2:
                return str(corrected)
        return str(year)

    return re.sub(r'\b20\d{2}\b', replace_year, transcript)

def parse_form_field_answer(transcript, field_type):
    """
    Use Groq to extract a specific field value from the user's speech.
    field_type: 'hospital_name', 'date', 'blood_bags', 'message'
    """
    client = get_client()
    if not client:
        return {'value': transcript}  # fallback to raw transcript
    
    if field_type == 'date':
        transcript = fix_year_mishear(transcript)

    prompts = {
        'hospital_name': f"""Extract the hospital or clinic name from this speech: "{transcript}"
Return ONLY a JSON object: {{"value": "hospital name here"}}
If no hospital name found, use the entire transcript as the value.
Do not include any other text.""",

        'date': f"""Extract a date from this speech: "{transcript}"
Today is {__import__('datetime').date.today().isoformat()}.
Convert relative dates like "tomorrow", "next week", "June 5" to YYYY-MM-DD format.
Return ONLY a JSON object: {{"value": "YYYY-MM-DD"}}
If no date found, return: {{"value": ""}}
Do not include any other text.""",

        'blood_bags': f"""Extract a number from this speech: "{transcript}"
This represents how many blood bags are needed.
Return ONLY a JSON object: {{"value": 1}}
Use integer only. If no number found, return: {{"value": 1}}
Do not include any other text.""",

        'message': f"""Fix grammar and spelling of this blood donation request message: "{transcript}"
Rules:
- Keep it as close to the original as possible
- Only fix grammar, spelling, and punctuation
- Do NOT make it longer than the original
- Keep the same tone — if casual, keep it casual
- If Filipino or Taglish, keep it Filipino or Taglish
- Return ONLY a JSON object: {{"value": "corrected message here"}}
- Do not include any other text.""",
    }

    try:
        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[
                {'role': 'user', 'content': prompts[field_type]}
            ],
            max_tokens=100,
            temperature=0.1,
        )

        import json
        result = response.choices[0].message.content.strip()
        result = result.replace('```json', '').replace('```', '').strip()
        return json.loads(result)

    except Exception:
        return {'value': transcript}