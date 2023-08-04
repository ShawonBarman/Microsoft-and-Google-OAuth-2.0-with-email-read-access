from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.login_page, name='login'),
    path('login/', views.login_with_google, name='login_with_google'),
    path('callback/', views.callback, name='callback'),
    path('thankyou/', views.thank_you, name='thank_you'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('gmail-accounts/', views.gmail_accounts, name='gmail_accounts'),
    path('incoming-mails/<str:gmail_account>/', views.gmail_incoming_mails, name='gmail_incoming_mails'),
    
    # Sign in with Microsoft
    path('login-with-microsoft/', views.login_with_microsoft, name='login_with_microsoft'),
    path('microsoft-callback/', views.microsoft_callback, name='microsoft_callback'),
    path('microsoft-incoming-mails/<str:microsoft_account>/', views.microsoft_incoming_mails, name='microsoft_incoming_mails'),
]
