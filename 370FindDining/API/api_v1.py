import requests
import json
import math
import time
from threading import Thread
from FindDining.Algorithm.DBManager import *
from API.WSManager import *

def get_distance(lat1, lng1, lat2, lng2):
    """
    Calculate the distance in kilometers between two points of latitude and longitude

    :param lat1: Latitude of point 1
    :param lng1: Longitude of point 1
    :param lat2: Latitude of point 2
    :param lng2: Longitude of point 2
    :return: The distance between point 1 and 2 in kilometers
    """
    lat1 = float(lat1)
    lng1 = float(lng1)
    lat2 = float(lat2)
    lng2 = float(lng2)
    p = math.pi/180

    a = 0.5 - math.cos((lat2 - lat1) * p) / 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * (1 - math.cos((lng2 - lng1) * p)) / 2

    return (12742 * math.asin(math.sqrt(a))).__round__(3)


def clean_string_of(s: str, to_replace, to_replace_with):
    """
    just str.replace() but with error catching for None and non-strings

    :param s: The string to modify
    :param to_replace: The character you wish to replace with to_replace_with
    :param to_replace_with: The character you wish to fill the gap with. Can be ""
    :return: None
    """
    if s is None or type(s) != str:
        return s
    else:
        return s.replace(to_replace, to_replace_with)


def try_get(dic, key, clean: list = None):
    """
    Try to access a key of a dictionary. If it doesn't exist, return None. If it does, return it (possibly cleaned)

    :param dic: The dictionary to access
    :param key: The key that will be attempted to be accessed
    :param ?clean: A list of pairs of characters for use in the clean_string_of function
    :return: The value at the key (?clean) or None
    """
    try:
        to_return = dic[key]

        if clean is None:
            return to_return
        else:
            for pair in clean:
                to_return = clean_string_of(to_return, pair[0], pair[1])
            return to_return
    except:
        return None

 # Comment out when not using

class API:
    """
    The main class for Handling API tasks
    Handles Places, Details, and Web Scrapping logic and adds the results to the database
    """
    def __init__(self, location: str = "", max_distance_in_meters: str = ""):
        self._payload = {}
        self._headers = {}
        self._location = location
        self.pagetoken = ""
        self._max_distance_in_meters = max_distance_in_meters
        self._dbManager = DBManager()
        self._wsManager = WSManager()

    def set_location(self, location: str):
        self._location = location

    def get_location(self):
        return self._location

    def has_location(self):
        return bool(self._location)

    def set_max_distance_in_meters(self, distance: str):
        self._max_distance_in_meters = distance

    def get_max_distance_in_meters(self):
        return self._max_distance_in_meters

    def has_max_distance_in_meters(self):
        return bool(self._max_distance_in_meters)

    def get_pagetoken(self):
        return self.pagetoken

    def set_pagetoken(self, pagetoken):
        self.pagetoken = pagetoken

    def query(self, query: str):
        """
        Make a query using requests

        :param query: The url to query
        :return: The response, along with the headers and payload just in case
        """
        response = requests.request("GET", query, headers=self._headers, data=self._payload)
        return {
            'response': response,
            'headers': self._headers,
            'payload': self._payload
        }

    def parse_string_location(self, location: str):
        """
        Given a location in string format returns a tuple format instead

        :param location: location in string format ("lat%2Clon")
        :return: The location in tuple format (lat, lon)
        """
        lat, lon = location.split("%2C")
        lat = float(lat)
        lon = float(lon)
        return lat, lon

    def stringify_tuple_location(self, location: tuple):
        """
        Given a location in tuple format returns a string format instead

        :param location: location in tuple format (lat, lon)
        :return: The location in string format ("lat%2Clon")
        """
        return f'{location[0]}%2C{location[1]}'

    def four_corners(self, diagonal_distance_in_meters: float):
        """
        Uses the currently set location and a passed diagonal distance to create 4 points at that distance away

        :param diagonal_distance_in_meters: the diagonal distance to a point
        :return: 4 pairs of coordinates in (lat,lon) form
        """
        loc = self.parse_string_location(self.get_location())

        side = 0.707215 * float(diagonal_distance_in_meters)/1000  # hardcoded trig
        num_degrees_latitude = (side / 111)  # hardcoded latitude logic

        # longitude is very variable. Determine km in one degree of longitude locally
        test_for_longitude = (loc[0], loc[1]+1)
        one_degree_longitude_here_is = get_distance(loc[0], loc[1],
                                                    test_for_longitude[0], test_for_longitude[1])
        num_degrees_longitude = (side / one_degree_longitude_here_is)

        # these names could be messed up, but it really doesn't matter
        top_left = (loc[0]+num_degrees_latitude, loc[1]-num_degrees_longitude)
        top_right = (loc[0]+num_degrees_latitude, loc[1]+num_degrees_longitude)
        bottom_left = (loc[0]-num_degrees_latitude, loc[1]-num_degrees_longitude)
        bottom_right = (loc[0]-num_degrees_latitude, loc[1]+num_degrees_longitude)

        return top_left, top_right, bottom_left, bottom_right

    def make_initial_queries(self, uid):
        """
        Makes all the queries necessary for a given user. Adds them to database

        :param uid: Some userID
        :return: The related restaurants for testing purposes. The places are also added to the database
        """
        # not sure if api needs this rounded so will anyway
        radius = math.floor(float(self._max_distance_in_meters) / 2)

        # Find out where you are checking
        points_to_check = self.four_corners(radius)

        point_list = []
        for point in points_to_check:
            point_list.append(point)
        return self._threaded_query_all_restaurants_in(point_list, radius, uid)

    def sql_check_these_IDs(self, place_stuff: list):
        """
        given a list of tuples, determine if place_id (place_stuff[0]) is in the database
            if it is, update the open column (place_stuff[1]) in the database.

        REMEMBER: OPEN CAN BE NONE

        :param place_stuff: list of tuples of (place_id, place_open)
        :return: list of place_ids not in the database, to be web scrapped!
        """
        nonExist = []

        for key in place_stuff:
            name = self._dbManager.select_one("SELECT name FROM places WHERE place_id=?", (str(key[0]),))
            if name is not None:
                if key[1] is None:
                    self._dbManager.insert("UPDATE places SET open=? WHERE place_id=?",
                                           (False, str(key[0])))
                else:
                    self._dbManager.insert("UPDATE places SET open=? WHERE place_id=?", (str(key[1]['open_now']), str(key[0])))
            else:
                nonExist.append(key[0])

        return nonExist

    def add_to_rel_places(self, uid, places):
        """
            Adds the list of relevant places for a given user to the database in the format
            of a csv list of place_ids

            :param uid: user id for places to be added to
            :param places: list of the place ids to be added
            :return: None, but users will be updated
        """
        placesStr = ','.join([i for i in places])

        self._dbManager.insert("UPDATE users SET rel_places=?, cur_rel_places=?, prev_rel_places=? WHERE user_id=?", (placesStr, placesStr, placesStr, uid))

    def sql_add_places_to_database(self, all_place):
        """
        Adds the list of relevant places for a given user to the database in the format
        of a csv list of place_ids

        :param uid: user id for places to be added to
        :param places: list of the place ids to be added
        :return: None, but users will be updated
                """

        for key in all_place.keys():

            name = self._dbManager.select_one("SELECT name FROM places WHERE place_id=?", (key,))
            if name is not None:
                continue
            # Adding if place doesn't exist

            print('Inserting:', key, 'into db')
            data = (key, all_place[key]['name'], all_place[key]['rating'], all_place[key]['num_ratings'], all_place[key]['price'])
            data = data + (str(all_place[key]['geolocation']), all_place[key]['address'], str(all_place[key]['type']), str(all_place[key]['tags']), str(all_place[key]['photo_ref']))
            data = data + (all_place[key]['phone'], all_place[key]['url'], all_place[key]['website'], 'True')

            self._dbManager.insert("INSERT INTO places VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data)


    def scrape_these_places(self, places: list):
        """
        :param places: formatted as a list of tuples where
                places[0] = place_id
                places[1] = corresponding url
        :return: a dictionary formatted {placeID_1:[about_detail_1, about_detail_2, ...], placeID_2:[...], ...}
        """
        if len(places) == 0:
            return {}

        print('Web scraping running... ', end='')

        start = time.time()

        self._wsManager.startDriver()
        placeData = self._wsManager.scrapeWeb(places)
        self._wsManager.killDriver()

        end = time.time()

        print('Done!')
        print('Time to scrape:', str(end - start))
        return placeData

    def _get_place_details(self, place_id, pool):
        """
        Given a place_id, puts details to that place in a pool

        :param place_id: the unique place id you need to check
        :param pool: the pool to add to
        :return: None
        """
        query = "https://maps.googleapis.com/maps/api/place/details/json?place_id={}&fields=name%2Crating%2Cformatted_phone_number%2Cwebsite%2Curl%2Cbusiness_status%2Ctype%2Cprice_level&key=".format(place_id)
        queryResponse = self.query(query)
        jsonResponse = json.loads(queryResponse['response'].text)
        details = {}

        for x in range(len(jsonResponse["result"])):  # json to dictionary
            if jsonResponse["result"]["business_status"] == 'OPERATIONAL':
                details[jsonResponse["result"]['name']] = {
                    "types": try_get(jsonResponse["result"], "types"),
                    "url": try_get(jsonResponse["result"], "url"),
                    "website": try_get(jsonResponse["result"], "website"),
                    "phone": try_get(jsonResponse["result"], "formatted_phone_number")
                }
        pool.append({place_id: details})

    def _threaded_query_all_restaurants_in(self, locations:list, radius: int, uid: str):
        """
        Queries a given location for restaurants in a given area, adds them to pool, but threaded

        :param locations: List, the locations to be queried
        :param radius: int, the radius in which to check restaurants
        :param uid: str, the user id for whom the query is being ran
        :return: Dict, data returned from query
        """
        place = []
        details = []

        place_threads = [
            Thread(target=lambda: self._query_restaurants_in(locations[0], radius, place)),
            Thread(target=lambda: self._query_restaurants_in(locations[1], radius, place)),
            Thread(target=lambda: self._query_restaurants_in(locations[2], radius, place)),
            Thread(target=lambda: self._query_restaurants_in(locations[3], radius, place))
        ]

        for p in place_threads:
            p.start()

        # Wait for all threads to die to continue
        print("Place api running...", end=' ')
        wait = True
        while wait:
            local = False
            for thread in place_threads:
                if thread.is_alive():
                    local = True
            if local:
                wait = True
            else:
                wait = False
        print("Done!")

        # wipe duplicates using a dictionary
        place_dictionary = {}
        for p in place:
            if p:
                key = list(p.keys())[0]
                place_dictionary[key] = p[key]

        # extra filters
        to_remove_keys = []
        for p_key in place_dictionary.keys():

            # no ratings? gtfo
            if place_dictionary[p_key]['rating'] is None:
                to_remove_keys.append(p_key)

            # convenience store? gtfo
            elif 'convenience_store' in place_dictionary[p_key]['type']:
                to_remove_keys.append(p_key)

            # grocery store? gtfo
            elif 'grocery_or_supermarket' in place_dictionary[p_key]['type']:
                to_remove_keys.append(p_key)

            # bowling alley? c'mon
            elif 'bowling_alley' in place_dictionary[p_key]['type']:
                to_remove_keys.append(p_key)

            # you know better
            elif 'beauty_salon' in place_dictionary[p_key]['type']:
                to_remove_keys.append(p_key)

            # NO HOTELS
            elif 'lodging' in place_dictionary[p_key]['type']:
                to_remove_keys.append(p_key)

            # :/
            elif 'clothing_store' in place_dictionary[p_key]['type']:
                to_remove_keys.append(p_key)

        for remove in to_remove_keys:
            place_dictionary.pop(remove)

        all_keys = list(place_dictionary.keys())
        keys_and_is_open = []
        for key in all_keys:
            keys_and_is_open.append((key, place_dictionary[key]['open']))

        to_check = self.sql_check_these_IDs(keys_and_is_open)

        valid_place_dictionary = {}
        for key in to_check:
            valid_place_dictionary[key] = place_dictionary[key]

        print("Details api running...", end=' ')
        details_threads = []
        for p_key in valid_place_dictionary.keys():
            details_threads.append(
                Thread(target=self._get_place_details(p_key, details))
            )

        for d in details_threads:
            d.start()

        # Wait for all threads to die to continue
        wait = True
        while wait:
            local = False
            for thread in details_threads:
                if thread.is_alive():
                    local = True
            if local:
                wait = True
            else:
                wait = False
        print('Done!')

        details_dictionary = {}
        for d in details:
            if d:
                key = list(d.keys())[0]
                details_dictionary[key] = d[key]

        all = {}
        for p_key in valid_place_dictionary.keys():
            all[p_key] = valid_place_dictionary[p_key]
            for another_key in details_dictionary[p_key].keys():
                valid_place_dictionary[p_key]['url'] = details_dictionary[p_key][another_key]['url']
                valid_place_dictionary[p_key]['website'] = details_dictionary[p_key][another_key]['website']
                valid_place_dictionary[p_key]['phone'] = details_dictionary[p_key][another_key]['phone']

        to_scrape = []
        for all_key in all.keys():
            to_scrape.append((all_key, all[all_key]['url']))
        scraped_details = self.scrape_these_places(to_scrape)

        for scrape_key in scraped_details.keys():
            temp = all[scrape_key]["type"]
            temp.insert(0, scraped_details[scrape_key]['type'])
            all[scrape_key]['type'] = temp
            all[scrape_key]['tags'] = scraped_details[scrape_key]['tags']

        self.sql_add_places_to_database(all)
        self.add_to_rel_places(uid, all_keys)

        return all


    def _query_restaurants_in(self, location: tuple, radius: int, pool):
        """
        Queries a given location for restaurants in a given area, adds them to pool
        :param location: location as a tuple
        :param radius: radius as an int
        :param pool: a list to add to
        :return: nothing
        """

        ILLEGAL_CHARACTERS = [("’", "'"), ('🍕', '')]  # (illegal, replace_with)

        returnQuery = {}
        goAgain = True
        page_token = ""
        for y in range(3):
            if goAgain:
                if not page_token:
                    query = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?" \
                            f"location={self.stringify_tuple_location(location)}" \
                            f"&radius={radius}" \
                            f"&type=restaurant" \
                            f"&key={apiKey}"
                else:
                    time.sleep(2)
                    query = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?" \
                            f"location={self.stringify_tuple_location(location)}" \
                            f"&radius={radius}" \
                            f"&pagetoken={page_token}" \
                            f"&type=restaurant" \
                            f"&key={apiKey}"
                queryResponse = self.query(query)
                # print(query, queryResponse['response'].text)
                jsonResponse = json.loads(queryResponse['response'].text)
                # print(f"Error Test in API says response was:\n{jsonResponse}")
                if "next_page_token" in jsonResponse:
                    page_token = jsonResponse["next_page_token"]
                else:
                    goAgain = False  # Stops the loop from running again if there is no next page to prevent unnecessary api calls
                for x in range(len(jsonResponse["results"])):
                    is_operational = try_get(jsonResponse["results"][x], 'business_status')
                    if is_operational is not None and jsonResponse["results"][x]['business_status'] == 'OPERATIONAL':

                        # Extra loop logic for the slightly more complex photo stuff
                        photo_stuff = try_get(jsonResponse["results"][x], 'photos')
                        if photo_stuff is not None:
                            photo = list(photo_stuff)[0]
                        else:
                            photo = None

                        returnQuery[jsonResponse["results"][x]['place_id']] = {
                            'name': try_get(jsonResponse["results"][x], 'name', ILLEGAL_CHARACTERS),
                            'open': try_get(jsonResponse["results"][x], 'opening_hours'),
                            'rating': try_get(jsonResponse["results"][x], 'rating'),
                            'num_ratings': try_get(jsonResponse["results"][x], 'user_ratings_total'),
                            'price': try_get(jsonResponse["results"][x], 'price_level'),
                            'geolocation': try_get(jsonResponse["results"][x]['geometry'], 'location'),
                            'address': try_get(jsonResponse["results"][x], 'vicinity', ILLEGAL_CHARACTERS),
                            'type': try_get(jsonResponse["results"][x], 'types'),
                            'photo_ref': photo
                        }

                    pool.append(returnQuery)
                    returnQuery = {}


if __name__ == "__main__":
    api = API()
    api.set_location("52.33750590000%2C-106.5788479")
    # api.set_location("52.1317268%2C-106.6427326")
    api.set_max_distance_in_meters("5000")
    z = api.make_initial_queries('1be3718d-f5dd-4f2d-ab1d-bf51d310673a')
