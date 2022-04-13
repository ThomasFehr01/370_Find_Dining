from API.api_v1 import *
from FindDining.Algorithm.algorithm import Algo

if __name__ == '__main__':
    num_failed = 0

    def assertTrue(boolean, message):
        global num_failed
        if not boolean:
            print(message)
            num_failed += 1

    def assertFalse(boolean, message):
        global num_failed
        if boolean:
            print(message)
            num_failed += 1

    def Try(func, number):
        global num_failed
        try:
            func()
        except:
            print(f"Attempt to test received an exception on test number {number+1}, counted as a fail")
            num_failed += 1


    if __name__ == '__main__':
        api0 = API()
        algo0 = Algo()
        tests = [
            lambda: assertTrue(api0.get_location() == '',
                               f"API: Expected get_location() to return '' on initialization, got {api0.get_location()}"),

            lambda: assertTrue(api0.get_max_distance_in_meters() == '',
                               f"API: Expected get_max_distance_in_meters() to return '' on initialization, got {api0.get_max_distance_in_meters()}"),

            lambda: assertTrue(api0.get_pagetoken() == '',
                               f"API: Expected get_pagetoken() to return '' on initialization, got {api0.get_pagetoken()}"),

            lambda: api0.set_location("1"),

            lambda: assertTrue(api0.get_location() == '1',
                               f"API: Expected get_location() to return '1', got {api0.get_location()}"),

            lambda: api0.set_max_distance_in_meters("4"),

            lambda: assertTrue(api0.get_max_distance_in_meters() == '4',
                               f"API: Expected get_max_distance_in_meters() to return '4', got {api0.get_max_distance_in_meters()}"),

            lambda: api0.set_pagetoken("5"),

            lambda: assertTrue(api0.get_pagetoken() == '5',
                               f"API: Expected get_pagetoken() to return '5', got {api0.get_pagetoken()}"),

            lambda: get_distance(50, -100, 51, -100),

            lambda: assertTrue(get_distance(50, -100, 50, -100)==0.0,
                               f'Distance: Expected distance to return 0.0 here, got {get_distance(50, -100, 50, -100)}'),

            lambda: assertTrue(get_distance(50, -100, 51, -100)==111.195,
                               f'Distance: Expected distance to return 111.195, got {get_distance(50, -100, 51, -100)}'),

            lambda: clean_string_of('Leopold’s', '’', "'"),

            lambda: assertTrue(clean_string_of('Leopold’s', '’', "'")=="Leopold's",
                               f"Cleaning: Expected clean_string_of to return Leopold's, got"),

            lambda: assertFalse(clean_string_of('I hate unit testing', "hate", "love")=="I hate unit testing",
                                f"Expected to love unit testing, got hate"),

            lambda: api0.parse_string_location("1%2C0"),

            lambda: api0.stringify_tuple_location((1, 0)),

            lambda: assertTrue(api0.parse_string_location("1%2C0")==(1, 0),
                               f'API: Location parse from string expected to receive (1, 0), got {api0.parse_string_location("1%2C0")}'),

            lambda: assertTrue(api0.stringify_tuple_location((1, 0))== "1%2C0",
                               f"API: Location parse from tuple expected to receive 1%2C, got {api0.stringify_tuple_location((1, 0))}"),

            lambda: assertTrue(api0.stringify_tuple_location(api0.parse_string_location("1%2C0"))=="1.0%2C0.0",
                               f'API: Expected to get the same return as arguement on double pass of 1.0%2C0.0, got {api0.stringify_tuple_location(api0.parse_string_location("1%2C0"))}'),

            lambda: assertFalse(algo0.visited_types, f"Algorithm: assorted types should be empty on initialization"),

            lambda: assertFalse(algo0.visited_tags, f"Algorithm: assorted tags should be empty on initialization"),

            lambda: assertFalse(algo0.num_questions, f"Algorithm: Expected the number of questions should be empty on initialization"),

            lambda: algo0.clean_None(None),

            lambda: assertTrue(algo0.clean_None(None)=='None', f"Algorithm: Expected a None passed to clean none should be string"),

            lambda: algo0.parse_string_list_to_list('[one, two]'),

            lambda: assertTrue(algo0.parse_string_list_to_list('[one, two]')==['one', 'two'],
                               f"Algorithm: Expected to get list of one and two from parse, didn't"),

            lambda: assertTrue(algo0.hasAPI(), f"Algorithm: Should be initialized with an API"),

            lambda: algo0.setAPI(api0),

            lambda: assertTrue(algo0.hasAPI(), f"Algorithm: New API should be set")
            ]

        for test_num in range(len(tests)):
            Try(tests[test_num], test_num)

        print(f"Tests finished!\nPassed {len(tests)-num_failed} out of {len(tests)}")








