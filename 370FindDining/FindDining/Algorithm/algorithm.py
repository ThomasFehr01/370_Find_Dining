import ast
import random as r
from collections import Counter
from API.api_v1 import *


# Unchecked Untested distance in km calculator >:)
def get_distance(lat1, lng1, lat2, lng2):
    lat1 = float(lat1)
    lng1 = float(lng1)
    lat2 = float(lat2)
    lng2 = float(lng2)
    p = math.pi/180

    a = 0.5 - math.cos((lat2 - lat1) * p) / 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * (1 - math.cos((lng2 - lng1) * p)) / 2

    return (12742 * math.asin(math.sqrt(a))).__round__(3)


def make_photo_url(dict_of_photo_info_in_string_form):
    dic = dict_of_photo_info_in_string_form  # lol
    print(dic)
    print(dic==None)
    print(dic=='None')
    print(str==type(dic))

    if dic is None or dic == "None":
        return "None"
    dic = dict(ast.literal_eval(dic))
    print(type(dic), dic)

    if dic is None or not dic:
        return None
    return f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={dic['width']}&photo_reference={dic['photo_reference']}&key={apiKey}"


def sort_query_dictionary_by_rating(dic):
    # Time complexity on this kind of sucks, but n is always gonna be 60 max so...
    sorted = []
    for key in dic.keys():
        if not sorted:
            sorted.append([key, dic[key]])
        else:
            for l in range(len(sorted)):
                if dic[key]['rating'] is None:
                    sorted.insert(0, [key, dic[key]])
                elif sorted[l][1]['rating'] is None:
                    continue
                elif float(sorted[l][1]['rating']) > float(dic[key]['rating']):
                    sorted.insert(l, [key, dic[key]])
                    break
                elif l == len(sorted)-1:
                    sorted.append([key, dic[key]])

    return sorted


class Algo:
    def __init__(self, api=None, debug=False):
        self.debug = debug
        if api is None:
            self._api = API()
        else:
            self._api = api
        self._api_response_cache = ''
        self._dbManager = DBManager()
        self.visited_tags = {}
        self.num_questions = {}
        self.visited_types = {}

    def database_to_dictionary(self, uid):
        """

        :param uid: the users ID
        :return: dictionary in form {place_id_1:{detail_key: detail}, place_id_2: {...}...}
        """

        places = (self._dbManager.select_one("SELECT cur_rel_places FROM users WHERE user_id=?", (uid,))).split(',')
        if places is None:
            raise Exception("From database_to_dictionary: no remaining places. We probably need a page for this")


        placeData = self._dbManager.select_many("SELECT * FROM places where place_id=?", places)

        place_dictionary = {}
        if placeData is None:
            return {}
        for place in placeData:

            place_dictionary[place[0]] = {}

            place_dictionary[place[0]]['name'] = place[1]
            place_dictionary[place[0]]['rating'] = place[2]
            place_dictionary[place[0]]['num_ratings'] = place[3]
            place_dictionary[place[0]]['price'] = place[4]
            place_dictionary[place[0]]['geolocation'] = place[5]
            place_dictionary[place[0]]['address'] = place[6]
            place_dictionary[place[0]]['type'] = place[7]
            place_dictionary[place[0]]['tags'] = place[8]
            place_dictionary[place[0]]['photo_ref'] = place[9]
            place_dictionary[place[0]]['phone'] = place[10]
            place_dictionary[place[0]]['map_url'] = place[11]
            place_dictionary[place[0]]['website'] = place[12]
            place_dictionary[place[0]]['open'] = place[13]

        return place_dictionary

    def reset_cur_and_prev_places(self, uid):
        """
        Resets cur and prev places to the users rel_places

        :param uid: the users ID
        :return: An all good string to hopefully force synchronous processing
        """

        rel_places = self._dbManager.select_one("SELECT rel_places FROM users WHERE user_id=?", (uid,))
        self._dbManager.insert("UPDATE users SET cur_rel_places=?, prev_rel_places=? WHERE user_id=?",
                               (rel_places, rel_places, uid))

        return "ALL GOOD :)"

    def debug_print_all_places_for(self, uid):
        rel_places = self._dbManager.select_one("SELECT rel_places FROM users WHERE user_id=?", (uid,))
        cur_places = self._dbManager.select_one("SELECT cur_rel_places FROM users WHERE user_id=?", (uid,))
        prev_places = self._dbManager.select_one("SELECT prev_rel_places FROM users WHERE user_id=?", (uid,))
        print(f"\nAll related places: {rel_places}"
              f"\nAll currently related places: {cur_places}"
              f"\nAll previous (undo) related places: {prev_places}\n")

    def rollback_cur_places(self, uid):
        """
        rolls back cur places to whatever is stored in prev places

        :param uid: the users ID
        :return: An all good string to hopefully force synchronous processing
        """

        rel_places = self._dbManager.select_one("SELECT rel_places FROM users WHERE user_id=?", (uid,))
        prev_places = self._dbManager.select_one("SELECT prev_rel_places FROM users WHERE user_id=?", (uid,))
        self._dbManager.insert("UPDATE users SET cur_rel_places=?, prev_rel_places=? WHERE user_id=?",
                               (prev_places, rel_places, uid))

        return "ALL GOOD :)"

    def update_cur_places(self, uid, to_keep: list):
        """
        Updates the cur places for a given user

        :param uid: the users ID
        :param to_remove: new list of places to set cur_rel_places equal to
        :return: None
        """
        places = ','.join([i for i in to_keep])

        old_places = self._dbManager.select_one("SELECT cur_rel_places FROM users WHERE user_id=?", (uid,))
        self._dbManager.insert("UPDATE users SET cur_rel_places=?, prev_rel_places=? WHERE user_id=?", (places, old_places, uid))

    def run_api_query(self, uid):
        """
        :param uid: the users ID
        :return: An all good string to hopefully force synchronous processing
        """

        userLocation = self.getUserLocation(uid)
        self._api.set_location(userLocation)
        self._api.set_max_distance_in_meters('10000')
        self._api.make_initial_queries(uid)

        return "It's running, hopefully"
        # places = ','.join([i for i in to_add])
        #
        # self._dbManager.open()
        # self._dbManager.insert('UPDATE users SET rel_places=? WHERE user_id=?', (places, uid))
        # self._dbManager.close()

    def get_number_current_restaurants(self, uid):
        """
        Given a user id, return the number of linked places

        :param uid: the users ID
        :return: the number of place_ids linked to a user
        """

        places = self._dbManager.select_one("SELECT cur_rel_places FROM users WHERE user_id=?", (uid,))
        if not places:
            return "0"
        return str(len(places.split(',')))

    def get_number_total_restaurants(self, uid):
        """
        Given a user id, return the number of linked places

        :param uid: the users ID
        :return: the number of place_ids linked to a user
        """

        places = self._dbManager.select_one("SELECT rel_places FROM users WHERE user_id=?", (uid,))

        if places is None:
            return "0"
        return str(len(places.split(',')))

    def clean_None(self, string):
        if string is None:
            return "None"
        else:
            return string

    def get_random_context(self, uid):
        """
        Given a user id, generates context for a results page of a random choice

        :param uid: some user id
        :return: dictionary of context
        """

        all_places = self.database_to_dictionary(uid)
        all_keys = list(all_places.keys())
        idx = r.randint(0, len(all_keys)-1)
        restaurant = all_places[all_keys[idx]]

        return self.gen_context_given_place(restaurant, uid)

    def get_best_context(self, uid):
        """
        Given a user id, generates context for the results page of the highest rated rel_place
        :param uid: some user id
        :return: dictionary of context for a result page render
        """
        all_places = self.database_to_dictionary(uid)
        all_keys = list(all_places.keys())
        best_key = None
        best_rating = 0
        for place_key in all_keys:
            if all_places[place_key]['rating'] is not None and float(all_places[place_key]['rating']) > best_rating:
                if all_places[place_key]['num_ratings'] is not None and int(all_places[place_key]['num_ratings']) > 5:
                    best_key = place_key

        if best_key is None:
            context = {
                'image': "None",
                'name': "None",
                'distance': "None",
                'price': "None",
                'phoneNumber': "None",
                'stars': "None",
                'address': "None",
                'websiteLink': "None",
                'moreInfo': "None"
            }
            return context
        restaurant = all_places[best_key]

        return self.gen_context_given_place(restaurant, uid)

    def pop_best_place(self, uid):
        """
        Given a user id, removes the highest rated place
        :param uid: some user id
        :return: Some happy string :)
        """
        all_places = self.database_to_dictionary(uid)
        if all_places is None or not all_places:
            return {"name": "No remaining restaurants... Add a check?"}

        all_keys = list(all_places.keys())
        best_key = None
        best_rating = 0
        for place_key in all_keys:
            if all_places[place_key]['rating'] is not None and float(all_places[place_key]['rating']) > best_rating:
                if all_places[place_key]['num_ratings'] is not None and int(all_places[place_key]['num_ratings']) > 5:
                    best_key = place_key

        all_keys.remove(best_key)
        self.update_cur_places(uid, all_keys)

        return ":))"

    def gen_context_given_place(self, restaurant, uid):
        # Image
        image = self.clean_None(make_photo_url(restaurant['photo_ref']))

        # Name
        name = self.clean_None(restaurant['name'])

        # Distance
        userLocation = self.getUserLocation(uid)
        bestLoc = restaurant['geolocation']
        bestLoc = dict(ast.literal_eval(bestLoc))
        userLoc = userLocation.split("%2C")
        distance = get_distance(bestLoc['lat'], bestLoc['lng'],
                                userLoc[0], userLoc[1])

        # Price
        price = self.clean_None(restaurant['price'])

        # PhoneNumber
        phoneNumber = self.clean_None(restaurant['phone'])

        # Stars
        stars = self.clean_None(restaurant['rating'])

        # Address
        address = self.clean_None(restaurant['address'])

        # Website
        websiteLink = self.clean_None(restaurant['website'])

        print(restaurant)
        # MoreInfo
        moreInfo = self.clean_None(restaurant['map_url'])

        context = {
            'image': image,
            'name': name,
            'distance': distance,
            'price': price,
            'phoneNumber': phoneNumber,
            'stars': stars,
            'address': address,
            'websiteLink': websiteLink,
            'moreInfo': moreInfo
        }

        return context

    def print_restaurants_dictionary(self, dict):
        for key in dict.keys():
            print(f"\n{key}")
            for hyperkey in dict[key].keys():
                print(f"\t{hyperkey}: {dict[key][hyperkey]}")
            print('\n')

    def parse_string_list_to_list(self, string):
        return string.strip("][",).replace("'", "").split(', ')

    def handle_answer(self, data, uid):

        print(f"Before request:\n\t{data}\nWas handled, this was {uid}'s database\n")
        self.debug_print_all_places_for(uid)


        all_places = self.database_to_dictionary(uid)
        all_keys = list(all_places.keys())
        if data['id'] == 'qqq_distance':

            keep_these_ids = []
            userLocation = self.getUserLocation(uid)
            CLOSE = 3000  # Arbitrary, as always
            FAR = 10000  # ^^

            # error checking
            if data['answer'] not in ['Far', 'Close']:
                print('Issue: answer to qqq_distance not in a recognized format', data['answer'])

            for place_id in all_keys:

                # Ignore variable names it's copied code for distance
                bestLoc = all_places[place_id]['geolocation']
                bestLoc = dict(ast.literal_eval(bestLoc))
                userLoc = userLocation.split("%2C")
                distance = get_distance(bestLoc['lat'], bestLoc['lng'],
                                        userLoc[0], userLoc[1])



                if data['answer'] == 'Far' and 0 <= distance*1000 <= FAR:
                    keep_these_ids.append(place_id)
                elif data['answer'] == 'Close' and 0 <= distance*1000 <= CLOSE:
                    keep_these_ids.append(place_id)

            self.update_cur_places(uid, keep_these_ids)

        elif data['id'] == 'qqq_price':

            keep_these_ids = []
            CHEAP = (1, 2)  # Arbitrary
            EXPENSIVE = (3, 4)

            # error checking
            if data['answer'] not in ['Cheap', 'Expensive']:
                print('Issue: answer to qqq_distance not in a recognized format', data['answer'])

            num_none = 0
            num_1 = 0
            num_2 = 0
            num_3 = 0
            num_4 = 0
            for place_id in all_keys:
                # TODO: what does everyone else think about treating None as 3?

                if all_places[place_id]['price'] is None:
                    place_price = 3
                    num_none+=1
                else:
                    place_price = int(all_places[place_id]['price'])
                    if place_price == 1: num_1 += 1
                    elif place_price == 2: num_2 += 1
                    elif place_price == 3: num_3 += 1
                    elif place_price == 4: num_4 += 1
                    else: print("Bruh")



                if data['answer'] == 'Cheap' and CHEAP[0] <= place_price <= CHEAP[1]:
                    keep_these_ids.append(place_id)
                elif data['answer'] == 'Expensive' and EXPENSIVE[0] <= place_price <= EXPENSIVE[1]:
                    keep_these_ids.append(place_id)

            print(f"\nnum_none: {num_none}\nnum_1: {num_1}\nnum_2: {num_2}\nnum_3: {num_3}\nnum_4: {num_4}\n")
            print(keep_these_ids)
            self.update_cur_places(uid, keep_these_ids)

        elif data['id'] == 'qqq_takeout':
            keep_these_ids = []
            self.print_restaurants_dictionary(all_places)

            # error checking
            if data['answer'] not in ['Dine-in', 'Delivery']:
                print('Issue: answer to qqq_distance not in a recognized format', data['answer'])

            # TODO kind of sketchy, assumes everywhere has dine-in (not true)
            if data['answer'] == 'Dine-in':
                return

            # this logic depends on dine-in no longer being an option at this point
            for place_id in all_keys:
                place_types = self.parse_string_list_to_list(str(all_places[place_id]['type']))
                place_tags = self.parse_string_list_to_list(str(all_places[place_id]['tags']))
                print(place_types)
                print(place_tags)
                has_takeout = False
                for type in place_types:
                    if type == 'meal_delivery':
                        has_takeout = True

                for tag in place_tags:
                    if tag in ['has_delivery']:
                        has_takeout = True

                if has_takeout:
                    keep_these_ids.append(place_id)

            self.update_cur_places(uid, keep_these_ids)

        else:
            self.handle_dynamic_question(data, uid)


        print(f"\nAfter request:\n\t{data}\nWas handled, this is {uid}'s database\n")
        self.debug_print_all_places_for(uid)
        return "ALL GOOD! :)"

    def get_question(self, uid):
        """
        Gets a question to ask the front end by getting a type or tag from the database and returning a string to ask
        :param uid: The user id
        :return: A question for the front end
        """
        data = self.database_to_dictionary(uid)
        self.update_num_questions(uid)
        if uid not in self.visited_tags: # Add the three tags that are answered in the QQQ that don't need to be repeated
            self.visited_tags[uid] = list()
            self.visited_tags[uid].extend(['serves_dine_in', 'has_delivery', 'has_takeout'])

        if len(self.type_restaurant_dict(data)) > 1: # Should get the food type that the user wants then find extra tags
            question_type = {next(iter(self.type_restaurant_dict(data))): 'type'}

            while list(question_type.items())[0] in self.visited_types: # Should prevent duplicate tags from appearing
                question_type = next(iter(question_type))

            for key in question_type.keys():
                better_output = str(key).replace('_', ' ')
            return_question = 'How does {} sound?'.format(better_output)
            question = {}
            question['question'] = return_question
            question['option1'] = 'Yes'
            question['option2'] = 'No'
            question['id'] = 'type'
            question['num_questions'] = self.num_questions[uid]
            return question
        else:
            question_iter = iter(self.tag_restaurant_dict(data))
            question_tag = {next(question_iter): 'tag'}
            print("remaining tags", self.tag_restaurant_dict(data))
            print("item", list(question_tag.items())[0][0])


            if len(self.visited_tags) > 0:
                print(self.visited_tags[uid])
                while list(question_tag.items())[0][0] in list(self.visited_tags[uid]):
                    question_tag = {next(question_iter): 'tag'}
                    print('while tagg', question_tag)
            for key in question_tag.keys():
                better_output = str(key).replace('_', ' ')
            return_question = 'Do you want a restaruant that {}?'.format(better_output)
            question = {}
            question['question'] = return_question
            question['option1'] = 'Yes'
            question['option2'] = 'No'
            question['id'] = 'tag'
            question['num_questions'] = self.num_questions[uid]
            return question

    def handle_dynamic_question(self, data, uid):
        """
        Handles the dynamic question and calls the functions for type or tag depending on the answer
        :param data: The response from the Question page
        :param uid: The user ID
        """
        if data['id'] == 'type':
            question_type = next(iter(self.type_restaurant_dict(self.database_to_dictionary(uid))))
            if data['answer'] == 'Yes':
                answered_yes = True
                self.add_dynamic_type(self.database_to_dictionary(uid), question_type, uid, answered_yes)
            else:
                self.add_dynamic_type(self.database_to_dictionary(uid), question_type, uid)

        elif data['id'] == 'tag':
            question_iter = iter(self.tag_restaurant_dict(self.database_to_dictionary(uid)))
            question_tag = next(question_iter) # IF DICT LOOPS ONCE BUT CAN'T FIND
            if data['answer'] == 'Yes':
                print('here')
                print(self.database_to_dictionary(uid))
                print(question_tag)
                print(uid)
                if len(self.visited_tags) > 0:
                    while question_tag in list(self.visited_tags[uid]):
                        question_tag = next(question_iter)
                self.add_dynamic_tag(self.database_to_dictionary(uid), json.dumps(question_tag), uid)
            else:
                if len(self.visited_tags) > 0:
                    print('question tag', question_tag)
                    while question_tag in list(self.visited_tags[uid]):
                        question_tag = next(question_iter)
                print(question_tag)
                self.update_visited_tags(json.dumps(question_tag), uid)
        else:
            raise Exception("Not a tag or type")

    def type_restaurant_dict(self, data):
        """
        Makes a dictionary of the number of restaurant types in the data based on the first word of the type
        :param data: Data of the restaurants
        :return: A list of counted restaurant type
        """
        restaurant_type_list = []
        for data_keys in data.keys():
            to_list = ast.literal_eval(data[data_keys]['type'])
            restaurant_type_list.append(to_list[0].split(' ')[0]) # This will sort the list to only be the first word of the type so (Pizza restaurant and Pizza delivery become Pizza)
        num_of_types = Counter(restaurant_type_list)
        if 'Restaurant' in num_of_types:
            num_of_types.pop('Restaurant')
        if 'Fast' in num_of_types:
            num_of_types['FastFood'] = num_of_types['Fast']  # Turns fast into fastfood for better output
            num_of_types.pop('Fast')
        return num_of_types

    def add_dynamic_type(self, data, type, uid, answer=False):
        """
        Takes the data and the type wanted and updates dict of restaurants with that type
        :param data: Data of the restaurants
        :param type: restaurant type from type_restaurant_dict
        :param uid: The user id
        :param answer: The user's answer yes or no as true and false
        """
        keep_these_ids = []
        self.update_visited_types(type, uid)
        if answer: # Keeps only places with the given type
            for data_keys in data.keys():
                to_list = ast.literal_eval(data[data_keys]['type'])
                if type == to_list[0].split(' ')[0]:
                    keep_these_ids.append(data_keys)
        else: # Removes all places with the given type from dict
            for data_keys in data.keys():
                to_list = ast.literal_eval(data[data_keys]['type'])
                if type != to_list[0].split(' ')[0]:
                    keep_these_ids.append(data_keys)

        self.update_cur_places(uid, keep_these_ids)

    def tag_restaurant_dict(self, data):
        """
        Makes a dictionary of counted tags in the given data
        :param data: Data of the restaurants
        :return: A counter dictionary of the tags in a restaurant
        """
        restaurant_tag_list = []
        for data_keys in data.keys():
            to_list = ast.literal_eval(data[data_keys]['tags'])
            for tag_list in to_list:
                restaurant_tag_list.append(tag_list)
        num_of_tags = Counter(restaurant_tag_list)
        return num_of_tags

    def add_dynamic_tag(self, data, tag, uid):
        """
        Updates the dictionary with restaurants with the wanted tags
        :param data: Data of the restaurants
        :param tag: A tag from tag_restaurant_dict
        :param uid: The user id
        """
        keep_these_ids = []
        tag = tag.replace('"',"")
        for data_keys in data.keys():
            to_list = ast.literal_eval(data[data_keys]['tags'])
            if tag in to_list:
                keep_these_ids.append(data_keys)
        self.update_visited_tags(tag, uid)
        self.update_cur_places(uid, keep_these_ids)

    def update_visited_tags(self, new_tag, uid):
        """
        Updates a dict of list of tags in the class so that they don't get seen again in questions
        :param new_tag: A new tag to add to the dict
        :param uid: A user id to key the tags to, to prevent cross tag conflict
        """
        new_tag = new_tag.replace('"',"")
        self.visited_tags[uid].extend(self.parse_string_list_to_list(new_tag))
        print('testit',self.visited_tags[uid])

    def update_visited_types(self, new_type, uid):
        """
        Updates a dic of list of types in the class so that they don't get seen again in questions
        :param new_type: A type to be added to the list
        :param uid: The user id
        """
        if uid not in self.visited_types:
            self.visited_types[uid] = list()
        self.visited_types[uid].extend(self.parse_string_list_to_list(new_type))

    def update_num_questions(self, uid):
        """
        Updates the number of questions asked
        :param uid: The user id to key the number to
        """
        if uid not in self.num_questions:
            self.num_questions[uid] = 0
        self.num_questions[uid] = self.num_questions[uid] + 1

    def clear_all_tags_types(self, uid):
        """
        Clears all types, tags, and the number of questions from their dictionaries
        """
        type_keys = self.visited_types.keys()
        tags_keys = self.visited_tags.keys()
        q_keys = self.num_questions.keys()

        if uid in type_keys: self.visited_types.pop(uid)
        if uid in tags_keys: self.visited_tags.pop(uid)
        if uid in q_keys: self.num_questions.pop(uid)

    def setAPI(self, api):
        self._api = api

    def hasAPI(self):
        return self._api is not None

    def query(self, query_text: str):
        self._api_response_cache = self._api.query(query_text)

    def addUser(self, userID, location):

        self._dbManager.insert("INSERT INTO users VALUES(?, ?, ?, ?, ?)", (userID, location, None, None, None))


    def getUserLocation(self, userID):
        loc = self._dbManager.select_one("SELECT location FROM users WHERE user_id=?", (userID,))
        return loc
