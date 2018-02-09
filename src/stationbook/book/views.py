# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, \
render, render_to_response
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from django.db import DatabaseError, transaction
from django.utils import timezone

from fdsn.fdsnStation.fdsnStation import NetworkStationGraph
from .models import FdsnNetwork, FdsnStation, \
ExtBasicData, ExtOwnerData, ExtMorphologyData, ExtHousingData, ExtAccessData
from fdsn.fdsnStation.fdsnStation import NetworkStationGraph
from .viewBase import StationUpdateViewBase

# Stations list view is used as a home screen for the Station Book
class HomeListView(ListView):
    model = FdsnStation
    context_object_name = 'stations'
    template_name = 'home.html'

    def get_queryset(self):
        queryset = FdsnStation.objects.order_by('?')[:1]
        return queryset


class SearchListView(ListView):
    model = FdsnStation
    context_object_name = 'data'
    template_name = 'search.html'

    def get_queryset(self):
        queryset = FdsnNetwork.objects.all()
        return queryset

class NetworksListView(ListView):
    model = FdsnNetwork
    context_object_name = 'data'
    template_name = 'networks.html'

    def get_queryset(self):
        queryset = FdsnNetwork.objects.all().order_by('code')
        return queryset

class RecentChangesListView(ListView):
    model = ExtAccessData
    context_object_name = 'data'
    template_name = 'recent_changes.html'
    paginate_by = 10

    def get_queryset(self):
        queryset = ExtAccessData.objects.all().order_by('-updated_at')[:1000]
        return queryset

class NetworkDetailsListView(ListView):
    model = FdsnNetwork
    context_object_name = 'network'
    template_name = 'network_details.html'

    def get_queryset(self):
        try:
            queryset = FdsnNetwork.objects.\
            get(code=self.kwargs.get('network_code'))
        except FdsnNetwork.DoesNotExist:
            raise Http404("Network does not exist!")
        return queryset


class StationDetailsListView(ListView):
    model = FdsnStation
    context_object_name = 'station'
    template_name = 'station_details.html'

    def get_queryset(self):
        try:
            queryset = FdsnStation.objects.\
            get(code=self.kwargs.get('station_code'))
        except FdsnStation.DoesNotExist:
            raise Http404("Station does not exist!")
        return queryset

class StationGalleryListView(ListView):
    model = FdsnStation
    context_object_name = 'station'
    template_name = 'station_gallery.html'

    def get_queryset(self):
        try:
            queryset = FdsnStation.objects.\
            get(code=self.kwargs.get('station_code'))
        except FdsnStation.DoesNotExist:
            raise Http404("Station does not exist!")
        return queryset

@method_decorator(login_required, name='dispatch')
class ExtBasicDataUpdateView(StationUpdateViewBase):
    def __init__(self):
        StationUpdateViewBase.__init__(self, 
        model=ExtBasicData,
        fields=('description', 'start', 'end', ))

    def get_object(self):
        obj = get_object_or_404(self.model, \
        station__code=self.kwargs['station_code'])
        return obj

    def form_valid(self, form):
        data = form.save(commit=False)
        data.save()
        print(data.station)
        self.add_ext_access_data(data.station, 'Updated basic data')
        return redirect('station_details', \
        network_code=data.station.fdsnStation_fdsnNetwork.code, \
        station_code=data.station.code)


@method_decorator(login_required, name='dispatch')
class ExtOwnerDataUpdateView(StationUpdateViewBase):
    def __init__(self):
        StationUpdateViewBase.__init__(self, 
        model=ExtOwnerData,
        fields=('name', 'department', 'agency', 'street', 'country', 'phone', 'email', ))

    def get_object(self):
        obj = get_object_or_404(self.model, \
        station__code=self.kwargs['station_code'])
        return obj

    def form_valid(self, form):
        data = form.save(commit=False)
        data.save()
        self.add_ext_access_data(data.station, 'Updated owner data')
        return redirect('station_details', \
        network_code=data.station.fdsnStation_fdsnNetwork.code, \
        station_code=data.station.code)


@method_decorator(login_required, name='dispatch')
class ExtMorphologyDataUpdateView(StationUpdateViewBase):
    def __init__(self):
        StationUpdateViewBase.__init__(self, 
        model=ExtMorphologyData,
        fields=('description', ))

    def get_object(self):
        obj = get_object_or_404(self.model, \
        station__code=self.kwargs['station_code'])
        return obj

    def form_valid(self, form):
        data = form.save(commit=False)
        data.save()
        self.add_ext_access_data(data.station, 'Updated morphology data')
        return redirect('station_details', \
        network_code=data.station.fdsnStation_fdsnNetwork.code, \
        station_code=data.station.code)


@method_decorator(login_required, name='dispatch')
class ExtHousingDataUpdateView(StationUpdateViewBase):
    def __init__(self):
        StationUpdateViewBase.__init__(self, 
            model=ExtHousingData,
            fields=('description', ))

    def get_object(self):
        obj = get_object_or_404(self.model, \
        station__code=self.kwargs['station_code'])
        return obj

    def form_valid(self, form):
        data = form.save(commit=False)
        data.save()
        self.add_ext_access_data(data.station, 'Updated housing data')
        return redirect('station_details', \
        network_code=data.station.fdsnStation_fdsnNetwork.code, \
        station_code=data.station.code)


def custom_404(request):
    return render_to_response('404.html')

def custom_500(request):
    return render_to_response('500.html')

def refresh_fdsn(request):
    try:
        FdsnNetwork.objects.all().delete()
        data = NetworkStationGraph('sl')
        graph = data.get_network_station_graph()
        for network in graph.networks:
            net = FdsnNetwork()
            net.code = network.code
            net.name = network.name
            net.description = network.description
            net.start_date = network.start_date
            net.restricted_status = network.restricted_status
            # If network is not known in the database, add it, otherwise get it
            #  from the database to prevent operating on a detached entity
            if not FdsnNetwork.objects.filter(code=net.code).exists():
                net.save()
            else:
                net = FdsnNetwork.objects.get(code=net.code)
            for station in network.stations:
                # Create station entity
                stat = FdsnStation()
                # Assign station to network
                stat.fdsnStation_fdsnNetwork = net
                # Fill data obtained from the Web Service
                stat.code = station.code
                stat.latitude = station.latitude
                stat.longitude = station.longitude
                stat.elevation = station.elevation
                stat.restricted_status = station.restricted_status
                stat.start_date = station.start_date
                stat.creation_date = station.creation_date
                stat.site_name = station.site_name
                # In case station data appears 
                # twice in the same dataset, ignore it
                if not FdsnStation.objects.filter(code=stat.code).exists():
                    # Create and save new ext entities
                    ext_data = ExtBasicData()
                    ext_data.save()
                    ext_owner = ExtOwnerData()
                    ext_owner.save()
                    ext_morphology = ExtMorphologyData()
                    ext_morphology.save()
                    ext_housing = ExtHousingData()
                    ext_housing.save()
                    # Assign ext entities to station and save it
                    stat.ext_basic_data = ext_data
                    stat.ext_owner_data = ext_owner
                    stat.ext_morphology_data = ext_morphology
                    stat.ext_housing_data = ext_housing
                    stat.save()
    except:
        raise
    finally:
        return redirect('home')