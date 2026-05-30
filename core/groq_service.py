import os
from groq import Groq

def get_client():
    api_key = os.getenv('GROQ_API_KEY')

    if not api_key:
        return None

    return Groq(api_key=api_key)

# All navigable pages with their URL names and descriptions
NAVIGATION_PAGES = {
    'browse_donors':            'Browse or find blood donors',
    'my_requests':              'My blood requests, requests I sent',
    'incoming_requests':        'Incoming donation requests, requests received',
    'cooldown_status':          'Cooldown tracker, donation tracker, my donations',
    'log_donation':             'Log a completed donation',
    'my_application':           'My donor application, application status',
    'apply_donor':              'Apply as a donor, donor application form',
    'profile_setup':            'My profile, edit profile',
    'notifications_page':       'Notifications, my notifications',
    'admin_dashboard':          'Admin dashboard, admin panel',
    'admin_application_queue':  'Review queue, pending applications',
    'admin_manage_users':       'Manage users, all accounts',
    'admin_donor_list':         'Donor list, verified donors',
    'admin_stats':              'Stats, statistics, requests and donations',
    'logout':                   'Logout, log out, sign out',
    'switch_role':              'Switch role, switch to recipient, switch to donor, change role',
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
- Return ONLY the JSON, no explanation, no markdown"""

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