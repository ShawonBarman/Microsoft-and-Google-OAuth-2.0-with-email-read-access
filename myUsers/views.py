from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from google.oauth2.credentials import Credentials
from google.auth.transport import requests as google_auth_requests
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from .models import *
import email.utils
from datetime import datetime, timedelta
import re
import base64
import msal
import requests

SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'

# Load the OAuth 2.0 client configuration from the credentials file
flow = InstalledAppFlow.from_client_secrets_file('myUsers/static/json/secret.json', scopes=SCOPES)

# Microsoft OAuth configuration
CLIENT_ID = '5df87552-f119-4d3a-ac0f-e70bcb829e7d'
CLIENT_SECRET = '878e1418-0301-4875-8ec0-b497347835ab'
AUTHORITY = 'https://login.microsoftonline.com/common'
SCOPE = ['User.Read'] 

def login_page(request):
    return render(request, 'login.html')

def login_with_google(request):
    # Redirect the user to Google's OAuth 2.0 authorization page
    flow.redirect_uri = request.build_absolute_uri('/callback')
    flow.include_granted_scopes = 'true'
    flow.prompt = 'consent'
    authorization_url, state = flow.authorization_url(access_type='offline')
    return redirect(authorization_url)

def callback(request):
    code = request.GET.get('code')
    if code:
        # Handle the OAuth 2.0 callback from Google
        flow.fetch_token(code=code)

        # Get the user's Google credentials
        credentials = flow.credentials

        # Fetch user info using the Gmail API
        service = build('gmail', 'v1', credentials=credentials)
        user_info = service.users().getProfile(userId='me').execute()

        # Save the user's Gmail account in the database
        email = user_info['emailAddress']
        user, created = User.objects.get_or_create(username=email, email=email)
        user.set_unusable_password()  # Set an unusable password to prevent login using Django authentication
        user_profile, _ = UserProfile.objects.get_or_create(user=user)
        user_profile.access_token = credentials.token
        user_profile.account_type = 'google'  # Set the account type to 'google'
        user_profile.save()

        # Save the user's access token in the session for later use
        request.session['access_token'] = credentials.token

        # Authenticate the user in Django's authentication system
        login(request, user)

        return redirect('thank_you')
    else:
        return HttpResponse("Error: No code received from Google.")

def thank_you(request):
    message="Authentication successful!"
    return render(request, 'thank_you.html', {"message": message})

def gmail_accounts(request):
    # Get all users with Google accounts from the database
    google_users = User.objects.filter(userprofile__account_type='google', email__isnull=False)

    # Get all users with Microsoft accounts from the database
    microsoft_users = User.objects.filter(userprofile__account_type='microsoft', email__isnull=False)

    # Extract the Gmail accounts from the users
    google_gmail_accounts = [user.email for user in google_users]
    microsoft_gmail_accounts = [user.email for user in microsoft_users]

    return render(request, 'gmail_accounts.html', {'google_gmail_accounts': google_gmail_accounts, 'microsoft_gmail_accounts': microsoft_gmail_accounts})

def parse_date(date_string):
    # Extract timezone offset from the date_string
    offset_match = re.search(r'[+-]\d{4}$', date_string)
    offset_str = offset_match.group() if offset_match else "+0000"

    # Parse the date string into a datetime object without timezone
    date_time_obj = email.utils.parsedate_to_datetime(date_string)

    # Manually add the timezone offset to the datetime object
    offset = timedelta(hours=int(offset_str[1:3]), minutes=int(offset_str[3:]))
    if offset_str[0] == '-':
        date_time_obj -= offset
    else:
        date_time_obj += offset

    return date_time_obj

def gmail_incoming_mails(request, gmail_account):
    try:
        # Get the user's credentials based on the selected Gmail account (replace 'email' with the actual field name where you store the Gmail account)
        user = User.objects.filter(email=gmail_account).first()
        if not user:
            # Handle the case when the Gmail account is not found in the database
            return render(request, 'gmail_account_not_found.html')

        # Get the user's access token from the user profile
        user_profile = UserProfile.objects.get(user=user)
        credentials = Credentials(token=user_profile.access_token)

        if not credentials.valid:
            # The token has expired, refresh it
            flow = InstalledAppFlow.from_client_secrets_file('myUsers/static/json/secret.json', scopes=SCOPES)
            credentials.refresh(google_auth_requests.Request())
            user_profile.access_token = credentials.token  # Update the access token in the user profile
            user_profile.save()

        # Create a Gmail API service using the authenticated credentials
        service = build('gmail', 'v1', credentials=credentials)

        # Fetch the last 100 emails using the Gmail API and sort them by date in descending order
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], q='', maxResults=100).execute()
        messages = results.get('messages', [])
        messages.reverse()  # Reverse the list to get the latest emails first

        if not messages:
            return render(request, 'no_emails_found.html')

        # Get detailed information for each message
        incoming_mails = []
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
            sender_info = next((h['value'] for h in msg['payload']['headers'] if h['name'] == 'From'), None)
            sender_name, sender_email = parse_sender_info(sender_info)
            subject = next(h['value'] for h in msg['payload']['headers'] if h['name'] == 'Subject')
            
            # Get the body data of the plain text part if available
            plain_text_part = next((part for part in msg['payload']['parts'] if part['mimeType'] == 'text/plain'), None)
            if plain_text_part:
                body_data = plain_text_part['body']['data']
                body_text = base64.urlsafe_b64decode(body_data).decode('utf-8')
            else:
                body_text = "[No body text available]"
            
            date = next(h['value'] for h in msg['payload']['headers'] if h['name'] == 'Date')  # Extract the date
            date_time_obj = parse_date(date)
            incoming_mails.append({'sender_name': sender_name, 'sender_email': sender_email, 'subject': subject, 'body': body_text, 'date': date_time_obj})
            
        incoming_mails.sort(key=lambda x: x['date'], reverse=True)

        return render(request, 'gmail_incoming_mails.html', {'incoming_mails': incoming_mails, 'gmail_account': gmail_account})
    except Exception as e:
        raise Exception(str(e))

def parse_sender_info(sender_info):
    """
    Parse the sender information to extract sender's name and email address.
    """
    # Remove surrounding spaces and '<>'
    sender_info = sender_info.strip("<> ")
    
    # Split sender information by the first occurrence of '<'
    sender_name, _, sender_email = sender_info.partition('<')
    
    return sender_name.strip(), sender_email.strip('>')

# Microsoft login view
def login_with_microsoft(request):
    # Create a PublicClientApplication instance
    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY)

    # Get the sign-in URL
    login_url = app.get_authorization_request_url(SCOPE, redirect_uri=request.build_absolute_uri('/microsoft-callback/'))

    return redirect(login_url)

# Microsoft callback view
def microsoft_callback(request):
    code = request.GET.get('code')
    if code:
        # Create a PublicClientApplication instance
        app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY)

        # Acquire a token using the authorization code
        result = app.acquire_token_by_authorization_code(code, SCOPE, redirect_uri=request.build_absolute_uri('/microsoft-callback/'), client_secret=CLIENT_SECRET)

        if 'access_token' in result:
            # Successfully authenticated with Microsoft, now authenticate the user in Django
            graph_data = get_microsoft_user_data(result['access_token'])
            email = graph_data.get('userPrincipalName')
            if not email:
                email = graph_data.get('mail')
            if email:
                user, created = User.objects.get_or_create(username=email, email=email)
                user.set_unusable_password()  # Set an unusable password to prevent login using Django authentication

                # Save the user's access token in the user profile
                user_profile, _ = UserProfile.objects.get_or_create(user=user)
                user_profile.access_token = result['access_token']
                user_profile.account_type = 'microsoft'
                user_profile.save()

                # Authenticate the user in Django's authentication system
                login(request, user)
                return redirect('thank_you')
            else:
                return HttpResponse("Error: Email not found in Microsoft user data.")
        else:
            return HttpResponse("Error: No access token received from Microsoft.")
    else:
        return HttpResponse("Error: No code received from Microsoft.")

def get_microsoft_user_data(access_token):
    # Fetch user info using the access token (Microsoft Graph API)
    import requests
    graph_endpoint = 'https://graph.microsoft.com/v1.0/me'
    headers = {'Authorization': 'Bearer ' + access_token}
    response = requests.get(graph_endpoint, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Error fetching Microsoft user data.")
    
    
def microsoft_incoming_mails(request, microsoft_account):
    try:
        # Get the user's credentials based on the selected Microsoft account
        user = User.objects.filter(email=microsoft_account).first()
        if not user:
            # Handle the case when the Microsoft account is not found in the database
            return render(request, 'microsoft_account_not_found.html')

        # Get the user's access token from the user profile
        user_profile = UserProfile.objects.get(user=user)
        access_token = user_profile.access_token

        # Fetch the last 100 emails using the Microsoft Graph API and sort them by date in descending order
        headers = {'Authorization': f'Bearer {access_token}'}
        mail_list_response = requests.get('https://graph.microsoft.com/v1.0/me/messages?$top=100', headers=headers)
        mail_list = mail_list_response.json().get('value', [])
        mail_list.sort(key=lambda x: x['sentDateTime'], reverse=True)

        if not mail_list:
            return render(request, 'no_emails_found.html')

        # Get detailed information for each email
        incoming_mails = []
        for mail in mail_list:
            sender_name, sender_email = parse_sender_info(mail['from'])
            subject = mail['subject']

            # Get the body data of the plain text part if available
            body_data = mail['body']['content']
            body_text = body_data if 'text' in body_data else "[No body text available]"

            date_time_obj = parse_date(mail['sentDateTime'])
            incoming_mails.append({'sender_name': sender_name, 'sender_email': sender_email, 'subject': subject, 'body': body_text, 'date': date_time_obj})

        return render(request, 'microsoft_incoming_mails.html', {'incoming_mails': incoming_mails, 'microsoft_account': microsoft_account})
    except Exception as e:
        raise Exception(str(e))