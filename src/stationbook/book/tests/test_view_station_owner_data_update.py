from django.urls import resolve, reverse

from .base_classes import NetworkStationTest
from ..views import ExtOwnerDataUpdateView


class StationOwnerDataUpdateTests(NetworkStationTest):
    def __init__(self, *args):
        NetworkStationTest.__init__(
            self,
            *args,
            url="station_edit_owner",
            arguments={"network_pk": "1", "station_pk": "1"}
        )

    def test_station_owner_data_update_view_status_code_authenticated(self):
        self.login_and_refresh()
        self.assertEquals(self.response.status_code, 200)

    def test_station_owner_data_update_view_status_code_anon(self):
        self.logout_and_refresh()
        self.assertEquals(self.response.status_code, 302)

    def test_station_owner_data_update_url_resolves_view(self):
        view = resolve("/networks/1/station/1/edit-owner/")
        self.assertEquals(view.func.view_class, ExtOwnerDataUpdateView)
