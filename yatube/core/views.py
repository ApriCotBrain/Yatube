from django.shortcuts import render
from django.views.defaults import server_error, page_not_found, permission_denied


def page_not_found(request, exception):
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def csrf_failure(request, reason=''):
    return render(request, 'core/403csrf.html')
