# Microsoft-and-Google-OAuth-2.0-with-email-read-access

### (1) Project Setup:
-> The project is based on Django, a high-level web framework written in Python. <br />
-> We use Django to create a web application that will allow users to sign in with their Google and Microsoft accounts. <br />
-> The project has a folder structure with the standard Django app setup. <br />

### (2) Authentication with Google:
-> The login_with_google view handles the initial step of the Google OAuth 2.0 authentication flow. It redirects the user to Google's authorization page.<br />
-> After granting access, the callback view handles the callback from Google. It fetches the user's Google credentials and stores the access token in the user's session for later use.<br />
-> The user's Gmail account (email) is saved in the database and associated with the Django user.<br />

### (3) Authentication with Microsoft:
-> Although the code for Microsoft authentication is not shown in the provided views, it is implied that you are using the django-microsoft-auth library to handle Microsoft OAuth 2.0 authentication. <br />
-> Similar to Google authentication, the user's Microsoft account is saved in the database and associated with the Django user. <br />

### (4) Listing Gmail Accounts:
-> The gmail_accounts view fetches all the Gmail accounts saved in the database and displays them on the gmail_accounts.html template.<br />
-> This template shows a list of Gmail accounts, and the user can click on a specific Gmail account to view its incoming emails.<br />

### (5) Fetching Incoming Emails for a Gmail Account:
-> The gmail_incoming_mails view fetches the last 100 incoming emails for the selected Gmail account and sorts them by date in descending order.<br />
-> It uses the Gmail API to interact with the Gmail mailbox and fetch the emails.<br />
-> The emails are displayed on the gmail_incoming_mails.html template.<br />

### (6) Parsing and Displaying Email Data:
-> For each incoming email, the view fetches detailed information like sender name, sender email, subject, and body from the email payload.<br />
-> The parse_date function parses the date string obtained from the email headers to a Python datetime object.<br />
-> The view renders this information in a formatted manner on the template.<br />

### (7) Templates:
-> There are several templates used in the project, such as login.html, thank_you.html, gmail_accounts.html, gmail_incoming_mails.html, microsoft_incoming_mails.html, gmail_account_not_found.html, and no_emails_found.html.<br />
-> These templates use Bootstrap CSS and JS for better UI and styling.<br />

### (8) Session and Access Tokens:
-> The project uses Django's session framework to store the user's access token for later use during API requests to Google and Microsoft.<br />
-> The access token is stored in the user's session and retrieved when needed to make API calls.<br />
<br />
Overall, the project allows users to sign in with their Google and Microsoft accounts, lists the Gmail accounts associated with the user, and fetches the last 100 incoming emails for a selected Gmail account. It also displays the emails in a formatted manner with sender details, subject, and body content. The UI is enhanced using Bootstrap for better styling and responsiveness.
