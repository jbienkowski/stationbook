# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
from urllib.request import Request, urlopen
import gzip
from .background import BackgroundThread

from django.db import transaction
from django.shortcuts import get_object_or_404

from .base_classes import \
NO_FDSNWS_DATA, NSMAP, \
RouteWrapper, RouteDatacenterWrapper, RouteParamWrapper, \
NodeWrapper, NetworkWrapper, StationWrapper, \
StationChannels, StationChannel, StationChannelSampleRateRatio, \
StationChannelSensor, StationChannelDataLogger, StationChannelResponse, \
StationChannelResponseInstrumentSensitivity, \
StationChannelResponseInputUnits, StationChannelResponseOutputUnits

from ..logger import StationBookLogger
from ..models import \
FdsnNode, FdsnNetwork, FdsnStation, ExtBasicData, ExtOwnerData, \
ExtMorphologyData, ExtHousingData, ExtAccessData, ExtBoreholeData, \
ExtBoreholeLayerData

class FdsnHttpBase(object):
    def __init__(self):
        pass

    def fdsn_request(self, url):
        try:
            req = Request(url)
            req.add_header('Accept-Encoding', 'gzip')
            response = urlopen(req)
            
            if response.info().get('Content-Encoding') == 'gzip':
                return gzip.decompress(response.read())
            else:
                return response.read()
        except Exception:
            raise
    
    def _get_fdsn_nodes(self):
        try:
            for n in FdsnNode.objects.all():
                yield NodeWrapper(n)
        except Exception:
            raise
    
    def get_node_entity_based_on_url(self, url):
        try:
            # >>> x = 'http://geofon.gfz-potsdam.de/fdsnws/dataselect/1/query'
            # >>> x.split('/')[2]
            # 'geofon.gfz-potsdam.de'
            return FdsnNode.objects.filter(
                url_station__contains=url.split('/')[2]).first()
        except FdsnNode.DoesNotExist:
            self.log_exception(
                'Could not identify node based on url: {0}'.format(url))
            return None
        except FdsnNode.MultipleObjectsReturned:
            self.log_exception(
                'Multiple nodes returned based on url: {0}'.format(url))
            return None
        except Exception:
            raise
    
    def get_network_if_known(self, node_wrapper, network_wrapper):
        try:
            return FdsnNetwork.objects.get(
                    fdsn_node__code=node_wrapper.code, 
                    code=network_wrapper.code,
                    start_date__year=network_wrapper.parse_start_date_year())

        except FdsnNetwork.DoesNotExist:
            return None
        except Exception:
            raise
    
    def get_station_if_known(self, node_wrapper, network_wrapper, station_wrapper):
        try:
            return FdsnStation.objects.get(
                fdsn_network__fdsn_node__code=node_wrapper.code,
                fdsn_network__code=network_wrapper.code,
                fdsn_network__start_date__year=network_wrapper.parse_start_date_year(),
                code=station_wrapper.code)

        except FdsnStation.DoesNotExist:
            return None
        except Exception:
            raise
    
    def log_information(self, info='No description'):
        StationBookLogger(__name__).log_info(
            '{0}: {1}'.format(self.__class__.__name__, info))
    
    def log_warning(self, info='No description'):
        StationBookLogger(__name__).log_warning(
            '{0}: {1}'.format(self.__class__.__name__, info))
    
    def log_exception(self, info='No description'):
        StationBookLogger(__name__).log_exception(
            '{0}: {1}'.format(self.__class__.__name__, info))


class FdsnNetworkManager(FdsnHttpBase):
    def __init__(self):
        pass
    
    def _discover_node_networks(self, node_wrapper):
        try:
            response = self.fdsn_request(
                node_wrapper.build_url_station_network_level())

            if not response:
                return

            root = ET.fromstring(response)

            for network in root.findall('.//mw:Network', namespaces=NSMAP):
                net_wrapper = NetworkWrapper()

                tmp = network.get('code')
                if tmp != None:
                    net_wrapper.code = tmp

                tmp = network.get('startDate')
                if tmp != None:
                    net_wrapper.start_date = tmp
                
                tmp = network.get('restrictedStatus') or 'unknown'
                if tmp != None:
                    net_wrapper.restricted_status = tmp
                
                tmp = network.find(
                    './/mw:Description', namespaces=NSMAP).text
                if tmp != None:
                    net_wrapper.description = tmp

                yield net_wrapper
        except ParseError:
            self.log_exception()
        except Exception:
            raise

    def _save_node_network(self, node_wrapper, network_wrapper):
        try:
            net = self.get_network_if_known(node_wrapper, network_wrapper)

            if net:
                net.description = network_wrapper.description
                # net.start_date = network_wrapper.start_date
                net.restricted_status = network_wrapper.restricted_status
                net.save()
            else:
                self.log_information(
                    'Adding: node {0} Network {1} Year {2}'.format(
                        node_wrapper.code,
                        network_wrapper.code,
                        network_wrapper.parse_start_date_year()))

                net = FdsnNetwork()
                net.code = network_wrapper.code
                net.description = network_wrapper.description
                net.start_date = network_wrapper.start_date
                net.restricted_status = network_wrapper.restricted_status
                net.fdsn_node = FdsnNode.objects.get(
                    code=node_wrapper.code)
                net.save()
        except Exception:
            self.log_exception()

    def _sync_fdsn_networks(self):
        try:
            for node_wrapper in self._get_fdsn_nodes():
                for network_wrapper in self._discover_node_networks(node_wrapper):
                    self._save_node_network(node_wrapper, network_wrapper)
        except Exception:
            raise


class FdsnStationChannelsManager(FdsnHttpBase):
    def __init__(self_):
        pass
    
    def discover_station_channels(self, network_pk, station_pk):
        try:
            network = FdsnNetwork.objects.get(pk=network_pk)
            station = FdsnStation.objects.get(pk=station_pk)
            node_wrapper = NodeWrapper(network.fdsn_node)
            channels_graph = StationChannels()

            response = self.fdsn_request(
                node_wrapper.build_url_station_channel_level().format(
                    network.code.upper(), station.code.upper()))
            root = ET.fromstring(response)

            for channel in root.findall('.//mw:Channel', namespaces=NSMAP):
                cha = StationChannel()

                tmp = channel.get('code')
                if tmp != None:
                    cha.code = tmp

                tmp = channel.get('startDate')
                if tmp != None:
                    cha.start_date = tmp

                tmp = channel.get('restrictedStatus')
                if tmp != None:
                    cha.restricted_status = tmp

                tmp = channel.get('locationCode')
                if tmp != None:
                    cha.location_code = tmp

                tmp = channel.find(
                    './/mw:Latitude', namespaces=NSMAP)
                if tmp != None:
                    cha.latitude = tmp.text

                tmp = channel.find(
                    './/mw:Longitude', namespaces=NSMAP)
                if tmp != None:
                    cha.longitude = tmp.text

                tmp = channel.find(
                    './/mw:Elevation', namespaces=NSMAP)
                if tmp != None:
                    cha.elevation = tmp.text

                tmp = channel.find(
                    './/mw:Depth', namespaces=NSMAP)
                if tmp != None:
                    cha.depth = tmp.text

                tmp = channel.find(
                    './/mw:Azimuth', namespaces=NSMAP)
                if tmp != None:
                    cha.azimuth = tmp.text

                tmp = channel.find(
                    './/mw:Dip', namespaces=NSMAP)
                if tmp != None:
                    cha.dip = tmp.text

                tmp = channel.find(
                    './/mw:SampleRate', namespaces=NSMAP)
                if tmp != None:
                    cha.sample_rate = tmp.text

                tmp = channel.find(
                    './/mw:StorageFormat', namespaces=NSMAP)
                if tmp != None:
                    cha.storage_format = tmp.text

                tmp = channel.find(
                    './/mw:ClockDrift', namespaces=NSMAP)
                if tmp != None:
                    cha.clock_drift = tmp.text
                
                tmp = channel.find(
                    './/mw:Sensor', namespaces=NSMAP).find(
                        './/mw:Type', namespaces=NSMAP)
                if tmp != None:
                    cha.sensor.type = tmp.text
                    
                tmp = channel.find(
                    './/mw:Sensor', namespaces=NSMAP).find(
                        './/mw:Manufacturer', namespaces=NSMAP)
                if tmp != None:
                    cha.sensor.manufacturer = channel.find(
                    './/mw:Sensor', namespaces=NSMAP).find(
                        './/mw:Manufacturer', namespaces=NSMAP).text
                
                tmp = channel.find(
                    './/mw:Sensor', namespaces=NSMAP).find(
                        './/mw:Description', namespaces=NSMAP)
                if tmp != None:
                    cha.sensor.description = tmp.text

                tmp = channel.find(
                    './/mw:Sensor', namespaces=NSMAP).find(
                        './/mw:Model', namespaces=NSMAP)
                if tmp != None:
                    cha.sensor.model = tmp.text

                tmp = channel.find(
                    './/mw:DataLogger', namespaces=NSMAP).find(
                        './/mw:Description', namespaces=NSMAP)
                if tmp != None:
                    cha.data_logger.description = tmp.text
                
                tmp = channel.find(
                    './/mw:Response', namespaces=NSMAP).find(
                        './/mw:InstrumentSensitivity', namespaces=NSMAP).find(
                            './/mw:Value', namespaces=NSMAP)
                if tmp != None:
                    cha.response.instrument_sensitivity.value = tmp.text

                tmp = channel.find(
                    './/mw:Response', namespaces=NSMAP).find(
                        './/mw:InstrumentSensitivity', namespaces=NSMAP).find(
                            './/mw:Frequency', namespaces=NSMAP)
                if tmp != None:
                    cha.response.instrument_sensitivity.frequency = tmp.text

                tmp = channel.find(
                    './/mw:Response', namespaces=NSMAP).find(
                        './/mw:InstrumentSensitivity', namespaces=NSMAP).find(
                            './/mw:InputUnits', namespaces=NSMAP).find(
                                './/mw:Name', namespaces=NSMAP)
                if tmp != None:
                    cha.response.instrument_sensitivity.input_units.name = tmp.text

                tmp = channel.find(
                    './/mw:Response', namespaces=NSMAP).find(
                        './/mw:InstrumentSensitivity', namespaces=NSMAP).find(
                            './/mw:OutputUnits', namespaces=NSMAP).find(
                                './/mw:Name', namespaces=NSMAP)
                if tmp != None:
                    cha.response.instrument_sensitivity.output_units.name = tmp.text

                channels_graph.channels.append(cha)

            return channels_graph
        except ParseError:
            self.log_exception()
            return StationChannels()
        except Exception:
            self.log_exception()
            return StationChannels()

class FdsnRoutingManager(FdsnHttpBase):
    def __init__(self):
        self.netman = FdsnNetworkManager()
        self.routing_node_wrapper = NodeWrapper(
            FdsnNode.objects.get(code='ODC'))
    
    def build_fdsn_station_url(self, url, param_wrapper):
        return url + '?network={0}&station={1}'.format(
            param_wrapper.net.upper(),
            param_wrapper.sta.upper()
        )

    def _get_fdsn_networks(self):
        try:
            for n in FdsnNetwork.objects.values('code').distinct():
                yield n['code']
        except Exception:
            raise

    def _discover_network_routes(self, network_code):
        try:
            self.log_information('Discovering network routes: {0}'.format(
                self.routing_node_wrapper.build_url_routing_network_level(
                    network_code)))

            response = self.fdsn_request(self.routing_node_wrapper.\
                build_url_routing_network_level(network_code))
            
            if not response:
                return

            root = ET.fromstring(response)
            
            route_wrapper = RouteWrapper()
            for dc in root.findall('.//datacenter'):
                datacenter_wrapper = RouteDatacenterWrapper()
                datacenter_wrapper.url = dc.find('url').text

                for param in dc.findall('.//params'):
                    param_wrapper = RouteParamWrapper()

                    tmp = param.find('loc').text
                    if tmp != None:
                        param_wrapper.loc = tmp

                    tmp = param.find('end').text
                    if tmp != None:    
                        param_wrapper.end = tmp

                    tmp = param.find('sta').text
                    if tmp != None:
                        param_wrapper.sta = tmp
                    
                    tmp = param.find('cha').text
                    if tmp != None:
                        param_wrapper.cha = tmp

                    tmp = param.find('priority').text
                    if tmp != None:
                        param_wrapper.priority = tmp

                    tmp = param.find('start').text
                    if tmp != None:
                        param_wrapper.start = tmp

                    tmp = param.find('net').text
                    if tmp != None:
                        param_wrapper.net = tmp

                    yield datacenter_wrapper.url, param_wrapper
            
            return route_wrapper
        except Exception:
            raise

    def _discover_network_stations(self, url, param_wrapper):
        try:
            node_entity = self.get_node_entity_based_on_url(url)

            if not node_entity:
                self.log_warning('Node not configured for: {0}'.format(url))
                return
            
            node_wrapper = NodeWrapper(node_entity)
            network_wrapper = NetworkWrapper()

            response = self.fdsn_request(
                node_wrapper.build_url_station_network_station_level(
                    param_wrapper.net, param_wrapper.sta))

            if not response:
                return

            root = ET.fromstring(response)

            tmp = root.find('.//mw:Network', namespaces=NSMAP).get('startDate')
            if tmp != None:
                network_wrapper.start_date = tmp
            
            tmp = root.find('.//mw:Network', namespaces=NSMAP).get('code')
            if tmp != None:
                network_wrapper.code = tmp

            for station in root.find(
                './/mw:Network', namespaces=NSMAP).findall(
                    './/mw:Station', namespaces=NSMAP):
                stat_wrapper = StationWrapper()

                tmp = station.get('code')
                if tmp != None:
                    stat_wrapper.code = tmp

                tmp = station.find(
                    './/mw:Latitude', namespaces=NSMAP).text
                if tmp != None:
                    stat_wrapper.latitude = tmp
                
                if tmp != None:
                    stat_wrapper.longitude = station.find(
                        './/mw:Longitude', namespaces=NSMAP).text
                
                tmp = station.find(
                    './/mw:Elevation', namespaces=NSMAP).text
                if tmp != None:
                    stat_wrapper.elevation = tmp
                
                tmp = station.get('restrictedStatus') or 'unknown'
                if tmp != None:
                    stat_wrapper.restricted_status = tmp
                
                tmp = station.get('startDate')
                if tmp != None:
                    stat_wrapper.start_date = tmp
                
                tmp = station.find(
                    './/mw:CreationDate', namespaces=NSMAP).text
                if tmp != None:
                    stat_wrapper.creation_date = tmp
                
                tmp = station.find(
                    './/mw:Site', namespaces=NSMAP).find(
                        './/mw:Name', namespaces=NSMAP).text
                if tmp != None:
                    stat_wrapper.site_name = tmp

                yield node_wrapper, network_wrapper, stat_wrapper
        except ParseError:
            self.log_exception()
        except:
            raise

    def _save_network_station(self, node_wrapper, network_wrapper, \
        station_wrapper):
        try:
            stat = self.get_station_if_known(
                node_wrapper, network_wrapper, station_wrapper)

            # If station is known in the database, just update it with the
            # latest FDSN data, otherwise add it to the database
            if stat:
                stat.latitude = station_wrapper.latitude
                stat.longitude = station_wrapper.longitude
                stat.elevation = station_wrapper.elevation
                stat.restricted_status = station_wrapper.restricted_status
                stat.start_date = station_wrapper.start_date
                stat.creation_date = station_wrapper.creation_date
                stat.site_name = station_wrapper.site_name
                stat.save()
            else:
                self.log_information(
                    'Adding: node {0} Network {1} Year {2} Station {3}'.format(
                        node_wrapper.code,
                        network_wrapper.code,
                        network_wrapper.parse_start_date_year(),
                        station_wrapper.code))

                # Create station entity
                stat = FdsnStation()
                # Assign station to network
                stat.fdsn_network = FdsnNetwork.objects.get(
                    fdsn_node__code=node_wrapper.code,
                    code=network_wrapper.code,
                    start_date__year=network_wrapper.parse_start_date_year()
                    )
                # Fill data obtained from the Web Service
                stat.code = station_wrapper.code
                stat.latitude = station_wrapper.latitude
                stat.longitude = station_wrapper.longitude
                stat.elevation = station_wrapper.elevation
                stat.restricted_status = station_wrapper.restricted_status
                stat.start_date = station_wrapper.start_date
                stat.creation_date = station_wrapper.creation_date
                stat.site_name = station_wrapper.site_name
                # Create ext entities
                ext_basic = ExtBasicData()
                ext_owner = ExtOwnerData()
                ext_morphology = ExtMorphologyData()
                ext_housing = ExtHousingData()
                ext_borehole = ExtBoreholeData()
                
                # Assign ext entities to station and save it
                try:
                    with transaction.atomic():
                        ext_basic.save()
                        ext_owner.save()
                        ext_morphology.save()
                        ext_housing.save()
                        ext_borehole.save()
                        
                        stat.ext_basic_data = ext_basic
                        stat.ext_owner_data = ext_owner
                        stat.ext_morphology_data = ext_morphology
                        stat.ext_housing_data = ext_housing
                        stat.ext_borehole_data = ext_borehole
                        stat.save()
                except Exception:
                    self.log_exception()
                    raise
        except FdsnNetwork.DoesNotExist:
            self.log_exception(
                'Network is not known! Node: {0} Network: {1} Station: {2}'.format(
                    vars(node_wrapper), 
                    vars(network_wrapper),
                    vars(station_wrapper)))
            raise
        except Exception:
            self.log_exception()
            raise
    
    def _sync_fdsn_stations(self):
        try:
            for network_code in self._get_fdsn_networks():
                for url, param_wrapper in self._discover_network_routes(network_code):
                    for node_wrapper, network_wrapper, stat_wrapper in \
                        self._discover_network_stations(url, param_wrapper):
                            self._save_network_station(
                                node_wrapper,
                                network_wrapper,
                                stat_wrapper
                            )
        except Exception:
            raise

class FdsnManager(object):
    def __init__(self):
        self.fdsn_netman = FdsnNetworkManager()
        self.fdsn_routman = FdsnRoutingManager()
    
    def process_fdsn(self):
        # First, discover and sync all networks
        self.fdsn_netman._sync_fdsn_networks()
        self.fdsn_routman._sync_fdsn_stations()
    
    def process_fdsn_in_thread(self):
        worker = BackgroundThread(self.process_fdsn())
        worker.run()