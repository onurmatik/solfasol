from django.shortcuts import render

from .services import list_calendar_entries


def agenda(request):
    return render(request, "calendar/agenda.html", {"entries": list_calendar_entries()})
