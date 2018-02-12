# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
from enum import Enum

from django.db import models, transaction
from django.utils import timezone
from django.contrib.auth.models import User
from django.utils.html import mark_safe

from markdown import markdown

STRING_LENGTH_SHORT = 256
STRING_LENGTH_MEDIUM = 1024
STRING_LENGTH_LONG = 16384

class ExtDataBase(models.Model):
    entity_removed = models.BooleanField(default=False)

class ExtBasicData(ExtDataBase):
    description = models.TextField(
        max_length=STRING_LENGTH_LONG, default='', blank=True)
    start = models.DateField(blank=True, null=True)
    end = models.DateField(blank=True, null=True)

    def __str__(self):
        return 'Basic data for station {0}'.format(self.station.code)

    def get_description_as_markdown(self):
        return mark_safe(markdown(self.description, safe_mode='escape'))


class ExtOwnerData(ExtDataBase):
    name_first = models.CharField(
        max_length=STRING_LENGTH_SHORT, blank=True, default='n/a')
    name_last = models.CharField(
        max_length=STRING_LENGTH_SHORT, blank=True, default='n/a')
    department = models.CharField(
        max_length=STRING_LENGTH_SHORT, blank=True, default='n/a')
    agency = models.CharField(
        max_length=STRING_LENGTH_SHORT, blank=True, default='n/a')
    street = models.CharField(
        max_length=STRING_LENGTH_SHORT, blank=True, default='n/a')
    country = models.CharField(
        max_length=STRING_LENGTH_SHORT, blank=True, default='n/a')
    phone = models.CharField(
        max_length=STRING_LENGTH_SHORT, blank=True, default='n/a')
    email = models.CharField(
        max_length=STRING_LENGTH_SHORT, blank=True, default='n/a')

    def __str__(self):
        return 'Owner data for station {0}'.format(self.station.code)

class ExtMorphologyData(ExtDataBase):
    GEOLOGICAL_UNIT_CHOICES = (
        ('unknown', 'Unknown'),
        ('alluvial_deposits', 'Alluvial deposits'),
        ('ancient_alluvialterraces', 'Ancient alluvial terraces'),
        ('argillite', 'Argillite'),
        ('breccias', 'Breccias'),
        ('clay', 'Clay'),
        ('conglomerate', 'Conglomerate'),
        ('debris', 'Debris'),
        ('diabase', 'Diabase'),
        ('dolomite', 'Dolomite'),
        ('fillade', 'Fillade'),
        ('fluvial_deposits', 'Fluvial deposits'),
        ('gneiss', 'Gneiss'),
        ('granite', 'Granite'),
        ('jasper', 'Jasper'),
        ('lacustrine_deposits', 'Lacustrine deposits'),
        ('limestone', 'Limestone'),
        ('marls', 'Marls'),
        ('metamorphic_rock', 'Metamorphic rock'),
        ('micaschist', 'Micaschist'),
        ('morainic_deposits', 'Morainic deposits'),
        ('ophiolite', 'Ophiolite'),
        ('rhyolitic_ignimbrite', 'Rhyolitic ignimbrite'),
        ('sand_deposits', 'Sand deposits'),
        ('sandstone', 'Sandstone'),
        ('schist', 'Schist'),
        ('torbidite', 'Torbidite'),
        ('volcanic_deposits', 'Volcanic deposits'),
        ('volcanic_rocks', 'Volcanic rocks'),
    )

    MORPHOLOGY_CLASS_CHOICES = (
        ('unknown', 'Unknown'),
        ('t1', 'T1'),
        ('t2', 'T2'),
        ('t3', 'T3'),
        ('t4', 'T4'),
    )

    GROUND_TYPE_EC8_CHOICES = (
        ('unknown', 'Unknown'),
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C'),
        ('d', 'D'),
        ('e', 'E'),
        ('s1', 'S1'),
        ('s2', 'S2'),
    )

    description = models.TextField(
        max_length=STRING_LENGTH_LONG, default='', blank=True)
    geological_unit = models.CharField(
        max_length=STRING_LENGTH_SHORT,
        choices=GEOLOGICAL_UNIT_CHOICES,
        default='', blank=True)
    morphology_class = models.CharField(
        max_length=STRING_LENGTH_SHORT,
        choices=MORPHOLOGY_CLASS_CHOICES,
        default='', blank=True)
    ground_type_ec8 = models.CharField(
        max_length=STRING_LENGTH_SHORT,
        choices=GROUND_TYPE_EC8_CHOICES,
        default='', blank=True)
    groundwater_depth = models.IntegerField(default=0)
    vs_30 = models.IntegerField(default=0)
    f0 = models.IntegerField(default=0)
    amp_f0 = models.IntegerField(default=0)
    basin_flag =  models.BooleanField(default=False)
    bedrock_depth = models.IntegerField(default=0)

    def __str__(self):
        return 'Morphology data for station {0}'.format(self.station.code)

    def get_description_as_markdown(self):
        return mark_safe(markdown(self.description, safe_mode='escape'))


class ExtHousingData(ExtDataBase):
    HOUSING_CLASS_CHOICES = (
        ('borehole', 'Borehole'),
        ('bridge', 'Bridge'),
        ('building', 'Building'),
        ('cave', 'Cave'),
        ('dam', 'Dam'),
        ('free_field', 'Free field'),
        ('other_structure', 'Other structure'),
        ('tunnel', 'Tunnel'),
        ('underground_shelter', 'Underground shelter'),
        ('urban_free_field', 'Urban free field'),
    )

    description = models.TextField(
        max_length=STRING_LENGTH_LONG, default='', blank=True)
    housing_class = models.CharField(
        max_length=STRING_LENGTH_SHORT,
        choices=HOUSING_CLASS_CHOICES,
        default='', blank=True)
    in_building = models.BooleanField(default=True)
    numer_of_storeys = models.IntegerField(default=0)
    distance_to_building = models.IntegerField(default=0)

    def __str__(self):
        return 'Housing data for station {0}'.format(self.station.code)

    def get_description_as_markdown(self):
        return mark_safe(markdown(self.description, safe_mode='escape'))

class ExtBoreholeData(ExtDataBase):
    depth = models.IntegerField(default=0)

    def __str__(self):
        return 'Borehole data for station {0}'.format(self.station.code)

class ExtBoreholeLayerData(ExtDataBase):
    extBoreholeLayerData_extBoreholeData = models.ForeignKey(
        ExtBoreholeData, related_name='borehole_layers',
        on_delete=models.CASCADE, default=None)
    description = models.CharField(
        max_length=STRING_LENGTH_SHORT, default='', blank=True)
    depth_top = models.IntegerField(default=0)
    depth_bottom = models.IntegerField(default=0)

    def __str__(self):
        return self.extBoreholeLayerData_extBoreholeData.station.code

class FdsnNetwork(models.Model):
    code = models.CharField(
        max_length=STRING_LENGTH_SHORT, unique=True)
    description = models.CharField(
        max_length=STRING_LENGTH_SHORT, default='', blank=True)
    start_date = models.CharField(
        max_length=STRING_LENGTH_SHORT, default='', blank=True)
    restricted_status = models.CharField(
        max_length=STRING_LENGTH_SHORT, default='', blank=True)

    def __str__(self):
        return 'Network {0}'.format(self.code)


class FdsnStation(models.Model):
    fdsnStation_fdsnNetwork = models.ForeignKey(
        FdsnNetwork, related_name='fdsn_stations',
        on_delete=models.PROTECT, default=None)
    code = models.CharField(
        max_length=STRING_LENGTH_SHORT, unique=True)
    site_name = models.CharField(
        max_length=STRING_LENGTH_SHORT, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True)
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True)
    elevation = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True)
    restricted_status = models.CharField(
        max_length=STRING_LENGTH_SHORT, blank=True)
    start_date = models.CharField(
        max_length=STRING_LENGTH_SHORT, blank=True)
    creation_date = models.CharField(
        max_length=STRING_LENGTH_SHORT, blank=True)
    # Ext data
    ext_basic_data = models.OneToOneField(ExtBasicData,
        related_name='station', on_delete=models.PROTECT)
    ext_owner_data = models.OneToOneField(ExtOwnerData,
        related_name='station', on_delete=models.PROTECT)
    ext_morphology_data = models.OneToOneField(ExtMorphologyData,
        related_name='station', on_delete=models.PROTECT)
    ext_housing_data = models.OneToOneField(ExtHousingData,
        related_name='station', on_delete=models.PROTECT)
    ext_borehole_data = models.OneToOneField(ExtBoreholeData,
        related_name='station', on_delete=models.PROTECT)

    def __str__(self):
        return 'Station {0}'.format(self.code)


class ExtAccessData(ExtDataBase):
    extAccessData_fdsnStation = models.ForeignKey(FdsnStation,
        related_name='access_data', on_delete=models.PROTECT)
    updated_by = models.ForeignKey(
        User, null=True, related_name='+', on_delete=models.SET_NULL)
    updated_at = models.DateTimeField(null=True)
    description = models.CharField(
        max_length=STRING_LENGTH_SHORT, default='Change', blank=True)

    def __str__(self):
        return '{0} has been updated at {1} by {2}: {3}'.format(
            self.extAccessData_fdsnStation__code,
            self.updated_at,
            self.updated_by,
            self.description)