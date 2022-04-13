from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
import uuid
import json
import ast
from FindDining.Algorithm.algorithm import Algo
import time


algo = Algo(debug=True)


@csrf_exempt
def location(request):
    if request.method != "POST":
        redirect('index')

    jsonResponse = json.loads(request.POST['data'])
    loc = str(jsonResponse['latitude']) + '%2C' + str(jsonResponse['longitude'])

    userID = str(uuid.uuid4())

    algo.addUser(userID, loc)

    response = HttpResponse(200)
    response.set_cookie('userID', userID)

    return response


@csrf_exempt
def qqq(request):
    if request.method != "POST":
        return redirect('index')

    # even more insecure type casting!
    qqqResults = algo.handle_QQQ(dict(json.loads(request.POST['data'])), request.COOKIES['userID'])

    response = HttpResponse(200)
    response.set_cookie('results', qqqResults)

    return response


# NEW VIEWS

@csrf_exempt
def post_pop_best_restaurant(request):
    uid = request.COOKIES['userID']
    response = HttpResponse()
    response.write(algo.pop_best_place(uid))

    return response

def post_start_api(request):
    uid = request.COOKIES['userID']
    response = HttpResponse()
    response.write(algo.run_api_query(uid))

    return response

def get_random_restaurant(request):
    uid = request.COOKIES['userID']
    # response = HttpResponse()
    context = algo.get_random_context(uid)

    return render(request, 'RandomResultPage.html', context)


def get_highest_rated_restaurant(request):
    uid = request.COOKIES['userID']
    context = algo.get_best_context(uid)

    return render(request, 'ResultPage.html', context)


@csrf_exempt
def post_answer(request):
    # POST
    uid = request.COOKIES['userID']
    response = HttpResponse()
    response.write(algo.handle_answer(dict(json.loads(request.POST['data'])), uid))

    return response


def get_question(request):
    uid = request.COOKIES['userID']
    context = algo.get_question(uid)

    return render(request, 'QuestionPage.html', context)


def get_test(request):
    return render(request, 'test_gets.html')


@csrf_exempt
def post_undo_last_answer(request):
    uid = request.COOKIES['userID']
    response = HttpResponse()
    response.write(algo.rollback_cur_places(uid))

    return response

@csrf_exempt
def post_undo_all_answers(request):
    uid = request.COOKIES['userID']
    response = HttpResponse()
    response.write(algo.reset_cur_and_prev_places(uid))
    algo.clear_all_tags_types(uid)

    return response


def get_number_current_restaurants(request):
    uid = request.COOKIES['userID']
    response = HttpResponse()
    response.write(algo.get_number_current_restaurants(uid))

    return response


def get_number_total_restaurants(request):
    uid = request.COOKIES['userID']
    response = HttpResponse()
    response.write(algo.get_number_total_restaurants(uid))

    return response


def index(request):
    response = render(request, 'StartPage.html')

    if request.COOKIES.get('is_qqq'):
        response.delete_cookie('is_qqq')
    if request.COOKIES.get('results'):
        response.delete_cookie('results')

    return response


def long(request):
    time.sleep(10)
    return HttpResponse(200)


def questions(request):

    # In case user tries to directly go to /questions first
    if not request.COOKIES.get('userID'):
        return redirect('index')

    if not request.COOKIES.get('is_qqq'):
        # This is ran when the user begins the qqqs.
        response = render(request, 'QQQPage.html')
        response.set_cookie('is_qqq', True)

        return response

    elif request.COOKIES['is_qqq'] == 'True':
        # Here once questions is called and user has finished the qqqs. Request here should contain the answers of the
        # qqs.

        context = {
            "option1": "dynamic q1",
            "option2": "dynamic q2",
            "numRestaurants": 'Some new Number'
        }

        response = render(request, 'QuestionPage.html', context)
        response.set_cookie('is_qqq', False)

        return response

    # Here when cookie exists and is equal to false
    # answer to previous dynamic question will be in request, set of either 2 new questions or possible restaurants
    # will be sent in response
    context = {
        "option1": "second Dynamic question 1 or suggestion",
        "option2": "second Dynamic question 2 or suggestion",
        "numRestaurants": 123
    }
    return render(request, 'QuestionPage.html', context)


def calculate(request):
    return render(request, 'CalculatingPage.html')


def results(request):

    if not request.COOKIES.get('results'):
        context = {
            "image": 'https://lh3.googleusercontent.com/places/AAcXr8pataLKQi0XmHJ4oa5_Ah6SNzCSt3MVPUZ50pIwjLoUorfNP2OSQRc2acuck81vlx6WTgUA8gHap_9XfS8Kn3rTFkJFnrdvNsQ=s1600-w4032',
            "name": "My House",
            "distance": 10,
            "price": "$$$",
            "phoneNumber": "(306)-123-4567",
            "deliveryLink": "https://www.google.ca/",
            "stars": 4,
            "address": "123 FakeStreet"
        }
    else:
        context = ast.literal_eval(request.COOKIES['results'])

    return render(request, 'ResultPage.html', context)


def handler404(request, exception=None):
    response = render(request, '404.html')
    response.status_code = 404
    return response
