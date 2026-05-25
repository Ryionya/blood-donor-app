from django.shortcuts import render

def browse_donors_view(request):
    # Placeholder donor data for now
    # M3 Day 3 will replace this with real database queries
    placeholder_donors = [
        {
            'name': 'Juan dela Cruz',
            'blood_type': 'A+',
            'location': 'Santa Rosa, Laguna',
            'is_available': True,
            'bio': 'Happy to help anyone in need.',
        },
        {
            'name': 'Maria Santos',
            'blood_type': 'O-',
            'location': 'Calamba, Laguna',
            'is_available': True,
            'bio': 'Regular donor since 2020.',
        },
        {
            'name': 'Carlo Reyes',
            'blood_type': 'B+',
            'location': 'Biñan, Laguna',
            'is_available': False,
            'bio': 'Currently on cooldown period.',
        },
        {
            'name': 'Ana Lim',
            'blood_type': 'AB+',
            'location': 'San Pedro, Laguna',
            'is_available': True,
            'bio': 'Type AB+ universal plasma donor.',
        },
        {
            'name': 'Ramon Garcia',
            'blood_type': 'O+',
            'location': 'Santa Rosa, Laguna',
            'is_available': True,
            'bio': 'Available on weekends.',
        },
        {
            'name': 'Sofia Torres',
            'blood_type': 'A-',
            'location': 'Cabuyao, Laguna',
            'is_available': False,
            'bio': 'Currently unavailable.',
        },
    ]

    # Basic filtering from GET params (placeholder logic)
    blood_type = request.GET.get('blood_type', '')
    location = request.GET.get('location', '')

    if blood_type:
        placeholder_donors = [d for d in placeholder_donors if d['blood_type'] == blood_type]
    if location:
        placeholder_donors = [d for d in placeholder_donors if location.lower() in d['location'].lower()]

    blood_type_choices = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

    return render(request, 'recipients/browse.html', {
        'donors': placeholder_donors,
        'blood_type_choices': blood_type_choices,
        'selected_blood_type': blood_type,
        'selected_location': location,
    })