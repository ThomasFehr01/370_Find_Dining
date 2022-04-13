"""FindDining URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf.urls import handler404
from . import views


handler404 = 'FindDining.views.handler404'

urlpatterns = [
    # WEBPAGE GETS
    path('', views.index, name='index'),
    path('question', views.questions, name='qs'),
    path('result', views.results, name='results'),
    path('qqq', views.qqq, name='qqq'),
    path('d_question', views.get_question, name="dynamic_question"),
    path('best_result', views.get_highest_rated_restaurant, name='best_restaurant'),
    path('random_result', views.get_random_restaurant, name='random_restaurant'),
    path('get_test', views.get_test, name='test'),
    path('calculate', views.calculate, name="calc"),


    # GETS
    path('location', views.location, name='loc'),
    path('current_restaurants', views.get_number_current_restaurants, name='get_number_current_restaurants'),
    path('total_restaurants', views.get_number_total_restaurants, name='get_number_total_restaurants'),

    # POSTS
    path('post_answer', views.post_answer, name='answer'),
    path('undo_last', views.post_undo_last_answer, name='undo'),
    path('reset', views.post_undo_all_answers, name='reset'),
    path('start_api', views.post_start_api, name='start_api'),
    path('pop_best', views.post_pop_best_restaurant, name='pop_best')


]
