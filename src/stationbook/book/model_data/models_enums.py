GEOLOGICAL_UNIT_CHOICES = (
    ("unknown", "Unknown"),
    ("alluvial_deposits", "Alluvial deposits"),
    ("ancient_alluvialterraces", "Ancient alluvial terraces"),
    ("argillite", "Argillite"),
    ("breccias", "Breccias"),
    ("clay", "Clay"),
    ("conglomerate", "Conglomerate"),
    ("debris", "Debris"),
    ("diabase", "Diabase"),
    ("dolomite", "Dolomite"),
    ("fillade", "Fillade"),
    ("fluvial_deposits", "Fluvial deposits"),
    ("gneiss", "Gneiss"),
    ("granite", "Granite"),
    ("jasper", "Jasper"),
    ("lacustrine_deposits", "Lacustrine deposits"),
    ("limestone", "Limestone"),
    ("marls", "Marls"),
    ("metamorphic_rock", "Metamorphic rock"),
    ("micaschist", "Micaschist"),
    ("morainic_deposits", "Morainic deposits"),
    ("ophiolite", "Ophiolite"),
    ("rhyolitic_ignimbrite", "Rhyolitic ignimbrite"),
    ("sand_deposits", "Sand deposits"),
    ("sandstone", "Sandstone"),
    ("schist", "Schist"),
    ("torbidite", "Torbidite"),
    ("volcanic_deposits", "Volcanic deposits"),
    ("volcanic_rocks", "Volcanic rocks"),
)

MORPHOLOGY_CLASS_CHOICES = (
    ("unknown", "Unknown"),
    ("t1", "T1"),
    ("t2", "T2"),
    ("t3", "T3"),
    ("t4", "T4"),
)

GROUND_TYPE_EC8_CHOICES = (
    ("unknown", "Unknown"),
    ("a", "A"),
    ("b", "B"),
    ("c", "C"),
    ("d", "D"),
    ("e", "E"),
    ("s1", "S1"),
    ("s2", "S2"),
)

HOUSING_CLASS_CHOICES = (
    ("borehole", "Borehole"),
    ("bridge", "Bridge"),
    ("building", "Building"),
    ("cave", "Cave"),
    ("dam", "Dam"),
    ("free_field", "Free field"),
    ("other_structure", "Other structure"),
    ("tunnel", "Tunnel"),
    ("underground_shelter", "Underground shelter"),
    ("urban_free_field", "Urban free field"),
)

NETWORK_CLASS_CHOICES = (
    ("all", "All"),
    ("permanent", "Permanent"),
    ("temporary", "Temporary"),
)

NETWORK_ACCESS_CHOICES = (
    ("all", "All"),
    ("unrestricted", "Unrestricted"),
    ("restricted", "Restricted"),
)

STATION_STATUS_CHOICES = (
    ("all", "All"),
    ("open", "Open"),
    ("closed", "Closed"),
)

STATION_ACCESS_CHOICES = (
    ("all", "All"),
    ("unrestricted", "Unrestricted"),
    ("restricted", "Restricted"),
)

SENSOR_UNIT_CHOICES = (
    ("all", "All"),
    ("m", "M"),
    ("ms", "M/S"),
    ("mss", "M/S^2"),
    ("pa", "PA"),
    ("c", "C"),
    ("deg", "DEG"),
    ("undefined", "Undefined"),
)

SENSOR_TYPE_CHOICES = (
    ("all", "All"),
    ("vbb", "VBB"),
    ("bb", "BB"),
    ("sp", "SP"),
    ("sm", "SM"),
    ("obs", "OBS"),
    ("undefined", "Undefined"),
)

BASIN_FLAG_CHOICES = (
    ("all", "All"),
    ("yes", "Yes"),
    ("no", "No"),
    ("undefined", "Undefined"),
)
