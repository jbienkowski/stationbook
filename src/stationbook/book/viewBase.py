from django.views.generic import UpdateView
from django.utils import timezone

from .models import ExtAccessData

class StationUpdateViewBase(UpdateView):
    def __init__(self, model, fields,
        template_name='station_edit.html',
        context_object_name='data'):
        self.model = model
        self.fields = fields
        self.template_name = template_name
        self.context_object_name = context_object_name

    def add_ext_access_data(self, station, desc):
        try:
            access = ExtAccessData()
            access.extAccessData_fdsnStation = station
            access.updated_by = self.request.user
            access.updated_at = timezone.now()
            access.description = desc
            access.save()
        except:
            raise
