#!/usr/bin/env python3
"""Map US cities to HOI4 provinces and write victory points by population category."""
from __future__ import annotations

import math
import pathlib
import re
from collections import defaultdict

ROOT = pathlib.Path(".")
STATES = ROOT / "history" / "states"
UNITSTACKS = ROOT / "map" / "unitstacks.txt"
LOC = ROOT / "localisation" / "english" / "doomsday_usa_cities_l_english.yml"

# category -> VP value
CAT_VP = {1: 25, 2: 12, 3: 5, 4: 2}
# top metros get a bump within cat 1
VP_OVERRIDE = {
    "New York": 35,
    "Los Angeles": 30,
    "Chicago": 30,
    "Houston": 25,
    "Washington": 20,  # capital weight inside cat 2
}

# City: (category, state_abbr, lat, lon)
# Coordinates are approximate city centers (WGS84).
CITIES: dict[str, tuple[int, str, float, float]] = {
    # Cat 1
    "New York": (1, "NY", 40.7128, -74.0060),
    "Los Angeles": (1, "CA", 34.0522, -118.2437),
    "Chicago": (1, "IL", 41.8781, -87.6298),
    "Houston": (1, "TX", 29.7604, -95.3698),
    "Phoenix": (1, "AZ", 33.4484, -112.0740),
    "Philadelphia": (1, "PA", 39.9526, -75.1652),
    "San Antonio": (1, "TX", 29.4241, -98.4936),
    "San Diego": (1, "CA", 32.7157, -117.1611),
    "Dallas": (1, "TX", 32.7767, -96.7970),
    "Fort Worth": (1, "TX", 32.7555, -97.3308),
    "Jacksonville": (1, "FL", 30.3322, -81.6557),
    "Austin": (1, "TX", 30.2672, -97.7431),
    # Cat 2
    "San Jose": (2, "CA", 37.3382, -121.8863),
    "Charlotte": (2, "NC", 35.2271, -80.8431),
    "Columbus": (2, "OH", 39.9612, -82.9988),
    "Indianapolis": (2, "IN", 39.7684, -86.1581),
    "San Francisco": (2, "CA", 37.7749, -122.4194),
    "Seattle": (2, "WA", 47.6062, -122.3321),
    "Denver": (2, "CO", 39.7392, -104.9903),
    "Oklahoma City": (2, "OK", 35.4676, -97.5164),
    "Nashville": (2, "TN", 36.1627, -86.7816),
    "Washington": (2, "DC", 38.9072, -77.0369),
    "Las Vegas": (2, "NV", 36.1699, -115.1398),
    "El Paso": (2, "TX", 31.7619, -106.4850),
    "Boston": (2, "MA", 42.3601, -71.0589),
    "Detroit": (2, "MI", 42.3314, -83.0458),
    "Louisville": (2, "KY", 38.2527, -85.7585),
    "Portland": (2, "OR", 45.5152, -122.6784),
    "Memphis": (2, "TN", 35.1495, -90.0490),
    "Baltimore": (2, "MD", 39.2904, -76.6122),
    "Milwaukee": (2, "WI", 43.0389, -87.9065),
    "Albuquerque": (2, "NM", 35.0844, -106.6504),
    "Fresno": (2, "CA", 36.7378, -119.7871),
    "Tucson": (2, "AZ", 32.2226, -110.9747),
    "Sacramento": (2, "CA", 38.5816, -121.4944),
    "Atlanta": (2, "GA", 33.7490, -84.3880),
    "Kansas City": (2, "MO", 39.0997, -94.5786),
    "Mesa": (2, "AZ", 33.4152, -111.8315),
    "Raleigh": (2, "NC", 35.7796, -78.6382),
    # Cat 3
    "Omaha": (3, "NE", 41.2565, -95.9345),
    "Colorado Springs": (3, "CO", 38.8339, -104.8214),
    "Long Beach": (3, "CA", 33.7701, -118.1937),
    "Virginia Beach": (3, "VA", 36.8529, -75.9780),
    "Miami": (3, "FL", 25.7617, -80.1918),
    "Oakland": (3, "CA", 37.8044, -122.2712),
    "Minneapolis": (3, "MN", 44.9778, -93.2650),
    "Tulsa": (3, "OK", 36.1540, -95.9928),
    "Bakersfield": (3, "CA", 35.3733, -119.0187),
    "Wichita": (3, "KS", 37.6872, -97.3301),
    "Aurora CO": (3, "CO", 39.7294, -104.8319),
    "New Orleans": (3, "LA", 29.9511, -90.0715),
    "Arlington TX": (3, "TX", 32.7357, -97.1081),
    "Tampa": (3, "FL", 27.9506, -82.4572),
    "Honolulu": (3, "HI", 21.3069, -157.8583),
    "Anaheim": (3, "CA", 33.8366, -117.9143),
    "Santa Ana": (3, "CA", 33.7455, -117.8677),
    "Corpus Christi": (3, "TX", 27.8006, -97.3964),
    "Riverside": (3, "CA", 33.9533, -117.3962),
    "Saint Louis": (3, "MO", 38.6270, -90.1994),
    "Lexington": (3, "KY", 38.0406, -84.5037),
    "Pittsburgh": (3, "PA", 40.4406, -79.9959),
    "Stockton": (3, "CA", 37.9577, -121.2908),
    "Anchorage": (3, "AK", 61.2181, -149.9003),
    "Cincinnati": (3, "OH", 39.1031, -84.5120),
    "Saint Paul": (3, "MN", 44.9537, -93.0900),
    "Greensboro": (3, "NC", 36.0726, -79.7920),
    "Toledo": (3, "OH", 41.6528, -83.5379),
    "Newark": (3, "NJ", 40.7357, -74.1724),
    "Plano": (3, "TX", 33.0198, -96.6989),
    "Henderson": (3, "NV", 36.0395, -114.9817),
    "Lincoln": (3, "NE", 40.8136, -96.7026),
    "Orlando": (3, "FL", 28.5383, -81.3792),
    "Jersey City": (3, "NJ", 40.7178, -74.0431),
    "Chula Vista": (3, "CA", 32.6401, -117.0842),
    "Buffalo": (3, "NY", 42.8864, -78.8784),
    "Fort Wayne": (3, "IN", 41.0793, -85.1394),
    "Chandler": (3, "AZ", 33.3062, -111.8413),
    "Saint Petersburg": (3, "FL", 27.7676, -82.6403),
    "Laredo": (3, "TX", 27.5306, -99.4803),
    "Durham": (3, "NC", 35.9940, -78.8986),
    "Irvine": (3, "CA", 33.6846, -117.8265),
    "Madison": (3, "WI", 43.0731, -89.4012),
    "Norfolk": (3, "VA", 36.8508, -76.2859),
    "Lubbock": (3, "TX", 33.5779, -101.8552),
    "Gilbert": (3, "AZ", 33.3528, -111.7890),
    "Winston-Salem": (3, "NC", 36.0999, -80.2442),
    "Glendale AZ": (3, "AZ", 33.5387, -112.1860),
    "Reno": (3, "NV", 39.5296, -119.8138),
    "Hialeah": (3, "FL", 25.8576, -80.2781),
    "Garland": (3, "TX", 32.9126, -96.6389),
    "Scottsdale": (3, "AZ", 33.4942, -111.9261),
    "Irving": (3, "TX", 32.8140, -96.9489),
    "Chesapeake": (3, "VA", 36.7682, -76.2875),
    "North Las Vegas": (3, "NV", 36.1989, -115.1175),
    "Fremont": (3, "CA", 37.5485, -121.9886),
    "Baton Rouge": (3, "LA", 30.4515, -91.1871),
    "Richmond": (3, "VA", 37.5407, -77.4360),
    "Boise": (3, "ID", 43.6150, -116.2023),
    # Cat 4 (selected distinct centers; suburbs still mapped for conflict collapse)
    "Spokane": (4, "WA", 47.6588, -117.4260),
    "Des Moines": (4, "IA", 41.5868, -93.6250),
    "Tacoma": (4, "WA", 47.2529, -122.4443),
    "San Bernardino": (4, "CA", 34.1083, -117.2898),
    "Modesto": (4, "CA", 37.6391, -120.9969),
    "Fontana": (4, "CA", 34.0922, -117.4350),
    "Santa Clarita": (4, "CA", 34.3917, -118.5426),
    "Birmingham": (4, "AL", 33.5207, -86.8025),
    "Oxnard": (4, "CA", 34.1975, -119.1771),
    "Fayetteville": (4, "NC", 35.0527, -78.8784),
    "Rochester": (4, "NY", 43.1566, -77.6088),
    "Huntington Beach": (4, "CA", 33.6595, -117.9988),
    "Salt Lake City": (4, "UT", 40.7608, -111.8910),
    "Grand Rapids": (4, "MI", 42.9634, -85.6681),
    "Amarillo": (4, "TX", 35.2220, -101.8313),
    "Yonkers": (4, "NY", 40.9312, -73.8987),
    "Aurora IL": (4, "IL", 41.7606, -88.3201),
    "Montgomery": (4, "AL", 32.3792, -86.3077),
    "Akron": (4, "OH", 41.0814, -81.5190),
    "Little Rock": (4, "AR", 34.7465, -92.2896),
    "Augusta": (4, "GA", 33.4735, -82.0105),
    "Shreveport": (4, "LA", 32.5252, -93.7502),
    "Columbus GA": (4, "GA", 32.4610, -84.9877),
    "Grand Prairie": (4, "TX", 32.7459, -96.9978),
    "Tallahassee": (4, "FL", 30.4383, -84.2807),
    "Huntsville": (4, "AL", 34.7304, -86.5861),
    "Mobile": (4, "AL", 30.6954, -88.0399),
    "Tempe": (4, "AZ", 33.4255, -111.9400),
    "Knoxville": (4, "TN", 35.9606, -83.9207),
    "Worcester": (4, "MA", 42.2626, -71.8023),
    "Newport News": (4, "VA", 37.0871, -76.4730),
    "Brownsville": (4, "TX", 25.9017, -97.4975),
    "Providence": (4, "RI", 41.8240, -71.4128),
    "Santa Rosa": (4, "CA", 38.4404, -122.7141),
    "Peoria AZ": (4, "AZ", 33.5806, -112.2374),
    "Oceanside": (4, "CA", 33.1959, -117.3795),
    "Fort Lauderdale": (4, "FL", 26.1224, -80.1373),
    "Chattanooga": (4, "TN", 35.0456, -85.3097),
    "Ontario": (4, "CA", 34.0633, -117.6509),
    "Cary": (4, "NC", 35.7915, -78.7811),
    "Elk Grove": (4, "CA", 38.4088, -121.3716),
    "Salem": (4, "OR", 44.9429, -123.0351),
    "Lancaster": (4, "CA", 34.6868, -118.1542),
    "Corona": (4, "CA", 33.8753, -117.5664),
    "Eugene": (4, "OR", 44.0521, -123.0868),
    "Palmdale": (4, "CA", 34.5794, -118.1165),
    "Salinas": (4, "CA", 36.6777, -121.6555),
    "Springfield MO": (4, "MO", 37.2089, -93.2923),
    "Pasadena TX": (4, "TX", 29.6911, -95.2091),
    "Rockford": (4, "IL", 42.2711, -89.0940),
    "Pomona": (4, "CA", 34.0551, -117.7500),
    "Hayward": (4, "CA", 37.6688, -122.0808),
    "Fort Collins": (4, "CO", 40.5853, -105.0844),
    "Escondido": (4, "CA", 33.1192, -117.0864),
    "Sunnyvale": (4, "CA", 37.3688, -122.0363),
    "Alexandria": (4, "VA", 38.8048, -77.0469),
    "Lakewood": (4, "CO", 39.7047, -105.0814),
    "Hollywood FL": (4, "FL", 26.0112, -80.1495),
    "Clarksville": (4, "TN", 36.5298, -87.3595),
    "Torrance": (4, "CA", 33.8358, -118.3406),
    "Victorville": (4, "CA", 34.5362, -117.2928),
    "Bridgeport": (4, "CT", 41.1865, -73.1952),
    "Macon": (4, "GA", 32.8407, -83.6324),
    "Warren": (4, "MI", 42.5145, -83.0147),
    "Syracuse": (4, "NY", 43.0481, -76.1474),
    "Naperville": (4, "IL", 41.7508, -88.1535),
    "Midland": (4, "TX", 31.9973, -102.0779),
    "Roseville": (4, "CA", 38.7521, -121.2880),
    "Killeen": (4, "TX", 31.1171, -97.7278),
    "Surprise": (4, "AZ", 33.6292, -112.3680),
    "Denton": (4, "TX", 33.2148, -97.1331),
    "Fullerton": (4, "CA", 33.8704, -117.9242),
    "Mesquite": (4, "TX", 32.7668, -96.5992),
    "Savannah": (4, "GA", 32.0809, -81.0912),
    "McAllen": (4, "TX", 26.2034, -98.2300),
    "Paterson": (4, "NJ", 40.9168, -74.1718),
    "Waco": (4, "TX", 31.5493, -97.1467),
    "Visalia": (4, "CA", 36.3302, -119.2921),
    "Olathe": (4, "KS", 38.8814, -94.8191),
    "Thornton": (4, "CO", 39.8680, -104.9719),
    "Orange": (4, "CA", 33.7879, -117.8531),
    "Thousand Oaks": (4, "CA", 34.1706, -118.8376),
    "Hampton": (4, "VA", 37.0299, -76.3452),
    "Miramar": (4, "FL", 25.9861, -80.2322),
    "Dayton": (4, "OH", 39.7589, -84.1916),
    "Gainesville": (4, "FL", 29.6516, -82.3248),
    "West Valley City": (4, "UT", 40.6916, -112.0011),
    "Coral Springs": (4, "FL", 26.2712, -80.2706),
    "Cedar Rapids": (4, "IA", 41.9778, -91.6656),
    "Sterling Heights": (4, "MI", 42.5803, -83.0302),
    "New Haven": (4, "CT", 41.3083, -72.9279),
    "Stamford": (4, "CT", 41.0534, -73.5387),
    "Elizabeth": (4, "NJ", 40.6640, -74.2107),
    "Concord CA": (4, "CA", 37.9780, -122.0311),
    "Kent": (4, "WA", 47.3809, -122.2348),
    "Lafayette": (4, "LA", 30.2241, -92.0198),
    "Simi Valley": (4, "CA", 34.2694, -118.7815),
    "Santa Clara": (4, "CA", 37.3541, -121.9552),
    "Athens": (4, "GA", 33.9519, -83.3576),
    "Hartford": (4, "CT", 41.7658, -72.6734),
    "Vallejo": (4, "CA", 38.1041, -122.2566),
    "Berkeley": (4, "CA", 37.8715, -122.2730),
    "Round Rock": (4, "TX", 30.5083, -97.6789),
    "Ann Arbor": (4, "MI", 42.2808, -83.7430),
    "Fargo": (4, "ND", 46.8772, -96.7898),
    "Columbia MO": (4, "MO", 38.9517, -92.3341),
    "Provo": (4, "UT", 40.2338, -111.6585),
    "Lansing": (4, "MI", 42.7325, -84.5555),
    "El Monte": (4, "CA", 34.0686, -118.0276),
    "Springfield IL": (4, "IL", 39.7817, -89.6501),
    "Fairfield": (4, "CA", 38.2494, -122.0399),
    "Miami Gardens": (4, "FL", 25.9420, -80.2456),
    "Temecula": (4, "CA", 33.4936, -117.1484),
    "Costa Mesa": (4, "CA", 33.6411, -117.9187),
    "College Station": (4, "TX", 30.6280, -96.3344),
    "Elgin": (4, "IL", 42.0354, -88.2826),
    "Murrieta": (4, "CA", 33.5539, -117.2139),
    "Gresham": (4, "OR", 45.5001, -122.4302),
    "High Point": (4, "NC", 35.9557, -80.0053),
    "Antioch": (4, "CA", 38.0049, -121.8058),
    "Inglewood": (4, "CA", 33.9617, -118.3531),
    "Cambridge": (4, "MA", 42.3736, -71.1097),
    "Burbank": (4, "CA", 34.1808, -118.3090),
    "Greeley": (4, "CO", 40.4233, -104.7091),
    "San Mateo": (4, "CA", 37.5630, -122.3255),
    "El Cajon": (4, "CA", 32.7948, -116.9625),
    "Charleston SC": (4, "SC", 32.7765, -79.9311),
    "Florida City": (4, "FL", 25.4479, -80.4792),
    "West Palm Beach": (4, "FL", 26.7153, -80.0534),
    "Columbia SC": (4, "SC", 34.0007, -81.0348),
    "Port St Lucie": (4, "FL", 27.2730, -80.3582),
    "Jackson": (4, "MS", 32.2988, -90.1848),
    "Brooklyn": (4, "NY", 40.6782, -73.9442),
    "Vancouver": (4, "WA", 45.6387, -122.6615),
    "Frisco": (4, "TX", 33.1507, -96.8236),
    "Sioux Falls": (4, "SD", 43.5446, -96.7311),
    "Allentown": (4, "PA", 40.6084, -75.4902),
}

# Manual forced province overrides when geography/split states need certainty.
# (Used after nearest-neighbor; wins over projection.)
FORCED: dict[str, int] = {
    "New York": 3878,
    "Brooklyn": 3894,
    "Los Angeles": 9814,
    "Chicago": 9450,
    "Houston": 10337,
    "Phoenix": 853,
    "Philadelphia": 6845,
    "San Antonio": 12782,
    "San Diego": 1562,
    "Dallas": 3960,
    "Fort Worth": 7981,
    "Jacksonville": 10352,
    "Austin": 6798,
    "San Jose": 6861,
    "San Francisco": 9671,
    "Oakland": 4518,
    "Boston": 6732,
    "Seattle": 7315,
    "Denver": 1827,
    "Detroit": 6710,
    "Washington": 3957,
    "Baltimore": 6984,
    "Atlanta": 12384,
    "New Orleans": 7552,
    "Baton Rouge": 1453,
    "Shreveport": 12401,
    "Birmingham": 12735,
    "Jackson": 4565,
    "Minneapolis": 1866,
    "Saint Paul": 6752,
    "Honolulu": 4180,
    "Anchorage": 13091,
    "Sacramento": 9713,
    "Las Vegas": 4799,
    "Reno": 4607,
    "Salt Lake City": 4865,
    "Albuquerque": 4975,
    "Oklahoma City": 5103,
    "Tulsa": 1806,
    "Kansas City": 10717,
    "Saint Louis": 4569,
    "Milwaukee": 12357,
    "Madison": 1560,
    "Indianapolis": 1595,
    "Columbus": 6855,
    "Cincinnati": 6874,
    "Toledo": 9808,
    "Akron": 882,
    "Dayton": 9775,
    "Charlotte": 7138,
    "Raleigh": 10081,
    "Durham": 7045,
    "Greensboro": 12054,
    "Nashville": 12501,
    "Memphis": 7797,
    "Knoxville": 8014,
    "Chattanooga": 1758,
    "Louisville": 6696,
    "Lexington": 12568,
    "Portland": 3513,
    "Salem": 12211,
    "Eugene": 10305,
    "Miami": 1843,
    "Tampa": 7388,
    "Orlando": 1572,
    "Tallahassee": 12381,
    "El Paso": 1998,
    "Corpus Christi": 805,
    "Lubbock": 2055,
    "Amarillo": 3972,
    "Waco": 12341,
    "Laredo": 5061,
    "McAllen": 12369,
    "Brownsville": 6785,
    "Fresno": 6694,
    "Bakersfield": 610,
    "Stockton": 9637,
    "Tucson": 3834,
    "Norfolk": 788,
    "Virginia Beach": 873,
    "Richmond": 10412,
    "Pittsburgh": 11800,
    "Allentown": 9789,
    "Buffalo": 11654,
    "Rochester": 3702,
    "Syracuse": 9664,
    "Yonkers": 11660,
    "Newark": 6882,
    "Jersey City": 6882,
    "Boise": 9616,
    "Omaha": 12586,
    "Lincoln": 12586,
    "Wichita": 4740,
    "Spokane": 1690,
    "Tacoma": 7255,
    "Vancouver": 12214,
    "Des Moines": 1770,
    "Little Rock": 12489,
    "Mobile": 7480,
    "Montgomery": 4622,
    "Huntsville": 4756,
    "Charleston SC": 7202,
    "Columbia SC": 4491,
    "Savannah": 12498,
    "Augusta": 11975,
    "Macon": 10437,
    "Columbus GA": 12325,
    "Colorado Springs": 868,
    "Fort Collins": 10588,
    "Grand Rapids": 6769,
    "Lansing": 11656,
    "Ann Arbor": 9724,
    "Fargo": 1870,
    "Sioux Falls": 10595,
    "Aurora CO": 12642,
    "Worcester": 3715,
    "Bridgeport": 9850,
    "New Haven": 3710,
    "Hartford": 9675,
    "Stamford": 9847,
    "Providence": 3906,
    "Springfield IL": 7831,
    "Rockford": 12305,
    "Aurora IL": 9682,
    "Naperville": 6737,
    "Springfield MO": 10370,
    "Henderson": 4799,
    "North Las Vegas": 4799,
    "West Valley City": 4865,
    "Provo": 1740,
    "Pasadena TX": 10337,
    "Arlington TX": 7981,
    "Plano": 3960,
    "Garland": 3960,
    "Irving": 7981,
    "Frisco": 3960,
    "Mesa": 853,
    "Chandler": 853,
    "Gilbert": 853,
    "Glendale AZ": 853,
    "Scottsdale": 853,
    "Tempe": 853,
    "Surprise": 853,
    "Peoria AZ": 853,
    "Long Beach": 9814,
    "Anaheim": 9814,
    "Santa Ana": 9814,
    "Irvine": 9814,
    "Riverside": 823,
    "Chula Vista": 1562,
    "Fremont": 6861,
    "Sunnyvale": 6861,
    "Santa Clara": 6861,
    "Hayward": 4518,
    "Berkeley": 4518,
    "Concord CA": 4518,
    "Vallejo": 9671,
    "Santa Rosa": 9671,
    "Modesto": 9637,
    "Saint Petersburg": 7388,
    "Hialeah": 1843,
    "Fort Lauderdale": 1843,
    "Hollywood FL": 1843,
    "Miramar": 1843,
    "Coral Springs": 1843,
    "Miami Gardens": 1843,
    "West Palm Beach": 9834,
    "Port St Lucie": 1913,
    "Gainesville": 10407,
    "Florida City": 1843,
    "Chesapeake": 788,
    "Newport News": 788,
    "Hampton": 788,
    "Alexandria": 951,
    "Winston-Salem": 12054,
    "High Point": 12054,
    "Cary": 10081,
    "Fayetteville": 4168,
    "Paterson": 6882,
    "Elizabeth": 6882,
    "Cambridge": 6732,
    "Kent": 7255,
    "Gresham": 3513,
    "Lafayette": 7555,
    "Olathe": 10717,
    "Columbia MO": 10370,
    "Cedar Rapids": 1770,
    "Warren": 6710,
    "Sterling Heights": 6710,
    "Athens": 11975,
    "Midland": 4955,
    "Killeen": 1927,
    "Round Rock": 6798,
    "College Station": 4577,
    "Denton": 3960,
    "Mesquite": 3960,
    "Grand Prairie": 7981,
}

# State abbr -> possible state ids in this mod (including splits)
STATE_IDS: dict[str, list[int]] = {
    "NY": [358, 1125],
    "CA": [378, 1124],
    "IL": [395],
    "TX": [375, 1126, 1127, 1128, 1129],
    "AZ": [377],
    "PA": [360],
    "FL": [366],
    "NC": [363],
    "OH": [261],
    "IN": [396],
    "WA": [386],
    "CO": [382],
    "OK": [374],
    "TN": [368],
    "DC": [361],
    "NV": [379],
    "MA": [357],
    "MI": [393],
    "KY": [369],
    "OR": [385],
    "MD": [361],
    "WI": [394],
    "NM": [376],
    "GA": [365, 1132],
    "MO": [373],
    "NE": [384],
    "MN": [391, 1137],
    "KS": [383],
    "LA": [371, 1133, 1134, 1135],
    "HI": [629],
    "AK": [463],
    "NJ": [359],
    "VA": [362],
    "ID": [387],
    "AL": [367, 1131],
    "UT": [380],
    "AR": [372],
    "RI": [357],
    "CT": [357],
    "SC": [364],
    "MS": [370, 1130],
    "ND": [389],
    "SD": [390],
    "IA": [392],
}


def load_province_coords() -> dict[int, tuple[float, float]]:
    coords: dict[int, tuple[float, float]] = {}
    for line in UNITSTACKS.open(encoding="utf-8", errors="ignore"):
        parts = line.strip().split(";")
        if len(parts) < 5 or parts[1] != "0":
            continue
        pid = int(parts[0])
        coords[pid] = (float(parts[2]), float(parts[4]))
    return coords


def find_state_file(sid: int) -> pathlib.Path | None:
    for p in STATES.glob("*.txt"):
        try:
            t = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if re.search(rf"^\s*id\s*=\s*{sid}\b", t, re.M):
            return p
    return None


def get_provinces(text: str) -> set[int]:
    m = re.search(r"provinces\s*=\s*\{([^}]*)\}", text, re.S)
    if not m:
        return set()
    return {int(x) for x in re.findall(r"\d+", m.group(1))}


def load_state_provinces() -> dict[int, set[int]]:
    out: dict[int, set[int]] = {}
    for abbr, sids in STATE_IDS.items():
        for sid in sids:
            path = find_state_file(sid)
            if not path:
                continue
            out[sid] = get_provinces(path.read_text(encoding="utf-8"))
    # also load any US states we might need
    for sid in list(range(357, 397)) + [261, 463, 629, 686, 816] + list(range(1124, 1138)):
        if sid in out:
            continue
        path = find_state_file(sid)
        if path:
            out[sid] = get_provinces(path.read_text(encoding="utf-8"))
    return out


def fit_affine(anchors: list[tuple[float, float, float, float]]):
    """Fit x = a*lat + b*lon + c, z = d*lat + e*lon + f from anchors (lat,lon,x,z)."""
    # Normal equations for 3-param least squares, separately for x and z
    def solve(targets):
        # unknowns a,b,c
        s_ll = s_oo = s_lo = s_l = s_o = n = 0.0
        s_lt = s_ot = s_t = 0.0
        for lat, lon, t in targets:
            s_ll += lat * lat
            s_oo += lon * lon
            s_lo += lat * lon
            s_l += lat
            s_o += lon
            n += 1
            s_lt += lat * t
            s_ot += lon * t
            s_t += t
        # 3x3 system
        A = [
            [s_ll, s_lo, s_l],
            [s_lo, s_oo, s_o],
            [s_l, s_o, n],
        ]
        B = [s_lt, s_ot, s_t]
        # Gaussian elimination
        M = [A[i][:] + [B[i]] for i in range(3)]
        for i in range(3):
            piv = max(range(i, 3), key=lambda r: abs(M[r][i]))
            M[i], M[piv] = M[piv], M[i]
            div = M[i][i] or 1e-12
            for j in range(i, 4):
                M[i][j] /= div
            for r in range(3):
                if r == i:
                    continue
                fac = M[r][i]
                for j in range(i, 4):
                    M[r][j] -= fac * M[i][j]
        return M[0][3], M[1][3], M[2][3]

    ax = solve([(lat, lon, x) for lat, lon, x, z in anchors])
    az = solve([(lat, lon, z) for lat, lon, x, z in anchors])
    return ax, az


def project(lat: float, lon: float, ax, az) -> tuple[float, float]:
    a, b, c = ax
    d, e, f = az
    return a * lat + b * lon + c, d * lat + e * lon + f


def nearest_province(
    x: float,
    z: float,
    candidates: set[int],
    coords: dict[int, tuple[float, float]],
) -> int | None:
    best = None
    best_d = 1e18
    for pid in candidates:
        if pid not in coords:
            continue
        px, pz = coords[pid]
        d = (px - x) ** 2 + (pz - z) ** 2
        if d < best_d:
            best_d = d
            best = pid
    return best


def display_name(key: str) -> str:
    # Strip disambiguators we added
    for suffix in (" CO", " TX", " AZ", " IL", " FL", " CA", " GA", " MO", " SC", " NY"):
        if key.endswith(suffix) and key not in ("New York",):
            # only strip if it's our disambiguation pattern for duplicates
            base = key[: -len(suffix)]
            if base in {
                "Aurora",
                "Arlington",
                "Glendale",
                "Hollywood",
                "Pasadena",
                "Concord",
                "Peoria",
                "Columbus",
                "Columbia",
                "Springfield",
                "Charleston",
            }:
                return base
    return key


def replace_vps(text: str, entries: list[tuple[int, int, str]]) -> str:
    text2 = re.sub(r"\n?\s*victory_points\s*=\s*\{[^}]*\}", "", text)
    if not entries:
        return text2
    block = "\t\tvictory_points = {\n"
    for pid, vp, name in sorted(entries, key=lambda e: (-e[1], e[2])):
        block += f"\t\t\t{pid} {vp} # {name}\n"
    block += "\t\t}\n"
    m = re.search(r"(add_core_of\s*=\s*USA\s*\n)", text2)
    if m:
        return text2[: m.end()] + block + text2[m.end() :]
    m2 = re.search(r"(\n\tprovinces\s*=)", text2)
    if m2:
        hist = text2.rfind("}", 0, m2.start())
        return text2[:hist] + block + "\t" + text2[hist:]
    return text2


def main() -> None:
    coords = load_province_coords()
    state_provs = load_state_provinces()

    # Build anchors from forced cities that have coords
    anchors = []
    for name, pid in FORCED.items():
        if name not in CITIES or pid not in coords:
            continue
        cat, abbr, lat, lon = CITIES[name]
        x, z = coords[pid]
        anchors.append((lat, lon, x, z))
    ax, az = fit_affine(anchors)
    print(f"fitted affine from {len(anchors)} anchors")

    # Map each city -> province
    city_prov: dict[str, int] = {}
    for name, (cat, abbr, lat, lon) in CITIES.items():
        if name in FORCED:
            pid = FORCED[name]
            # verify province exists in expected states
            sids = STATE_IDS.get(abbr, [])
            owned = any(pid in state_provs.get(sid, set()) for sid in sids)
            if not owned:
                # still allow if province exists anywhere in US states
                owned = any(pid in prows for prows in state_provs.values())
            if owned and pid in coords:
                city_prov[name] = pid
                continue
            print(f"WARN forced {name}->{pid} not in state {abbr}, falling back")

        sids = STATE_IDS.get(abbr, [])
        candidates: set[int] = set()
        for sid in sids:
            candidates |= state_provs.get(sid, set())
        if not candidates:
            print(f"WARN no provinces for {name} ({abbr})")
            continue
        x, z = project(lat, lon, ax, az)
        pid = nearest_province(x, z, candidates, coords)
        if pid is None:
            print(f"WARN no coord match for {name}")
            continue
        city_prov[name] = pid

    # Per province: keep best category city
    best: dict[int, tuple[int, str, int]] = {}  # pid -> (cat, name, vp)
    collapsed = []
    for name, pid in city_prov.items():
        cat, abbr, lat, lon = CITIES[name]
        vp = VP_OVERRIDE.get(name, CAT_VP[cat])
        dname = display_name(name)
        if pid not in best:
            best[pid] = (cat, dname, vp)
        else:
            old_cat, old_name, old_vp = best[pid]
            # lower cat number = higher priority; then higher vp
            if cat < old_cat or (cat == old_cat and vp > old_vp):
                collapsed.append(f"{old_name} (cat{old_cat}) <- lost to {dname} (cat{cat}) on {pid}")
                best[pid] = (cat, dname, vp)
            else:
                collapsed.append(f"{dname} (cat{cat}) collapsed into {old_name} on {pid}")

    # Group by state file
    pid_to_state: dict[int, int] = {}
    for sid, prows in state_provs.items():
        for pid in prows:
            pid_to_state[pid] = sid

    by_state: dict[int, list[tuple[int, int, str]]] = defaultdict(list)
    for pid, (cat, name, vp) in best.items():
        sid = pid_to_state.get(pid)
        if sid is None:
            print(f"WARN province {pid} ({name}) not in any tracked state")
            continue
        by_state[sid].append((pid, vp, name))

    # Write state files
    updated = 0
    all_loc: dict[int, str] = {}
    for sid, entries in sorted(by_state.items()):
        path = find_state_file(sid)
        if not path:
            print("missing state file", sid)
            continue
        text = path.read_text(encoding="utf-8")
        new_text = replace_vps(text, entries)
        path.write_text(new_text, encoding="utf-8", newline="\n")
        updated += 1
        for pid, vp, name in entries:
            all_loc[pid] = name
        print(f"{path.name}: {len(entries)} VPs")

    # Clear VPs from US states that ended with none? leave vanilla alone if not in by_state
    # States we touched earlier but now empty of mapped cities - restore nothing special

    lines = ["l_english:\n"]
    for pid, name in sorted(all_loc.items()):
        lines.append(f' VICTORY_POINTS_{pid}:0 "{name}"\n')
    LOC.parent.mkdir(parents=True, exist_ok=True)
    LOC.write_text("".join(lines), encoding="utf-8", newline="\n")

    print(f"\nstates updated: {updated}")
    print(f"unique provinces: {len(best)}")
    print(f"cities input: {len(CITIES)}")
    print(f"collapsed: {len(collapsed)}")
    # show a few collapses for sanity
    for line in collapsed[:25]:
        print(" ", line)
    if len(collapsed) > 25:
        print(f"  ... +{len(collapsed)-25} more")

    # sanity: every cat1 city should win its province
    print("\nCat1 mappings:")
    for name, (cat, abbr, lat, lon) in CITIES.items():
        if cat != 1:
            continue
        pid = city_prov.get(name)
        winner = best.get(pid, (None, None, None))[1] if pid else None
        print(f"  {name} -> {pid} (shown as {winner})")


if __name__ == "__main__":
    main()
