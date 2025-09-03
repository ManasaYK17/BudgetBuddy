from django.urls import path
from . import views

urlpatterns = [
    path('logout/', views.logout, name='logout'),
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add-expense/', views.add_expense, name='add_expense'),
    path('set-budget/', views.set_budget, name='set_budget'),
    path('add-goal/', views.add_goal, name='add_goal'),
    path('analytics/', views.analytics, name='analytics'),
]
