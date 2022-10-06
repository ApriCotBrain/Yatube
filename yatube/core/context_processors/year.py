from django.utils import timezone


def year(request):

    today = timezone.now().year
    return {
        'year': int(today)
    }
