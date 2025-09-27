# Task 0: Project Setup
Objective: Set up the django messaging app locally

Instructions:

Make a copy of the messaging_app directory done in the project Building Robust APIs,

Rename the copied directory to Django-Middleware-0x03


# Task 1: Logging User Requests(Basic Middleware)
Objective: Create a middleware that logs each user’s requests to a file, including the timestamp, user and the request path.

Instructions: - create a file middleware.py and Create the middleware class RequestLoggingMiddleware with two methods, __init__and __call__.

In the __call__ implement a logger that log’s the following information f"{datetime.now()} - User: {user} - Path: {request.path}“

Configure the Middleware section in the settings.py with your newly created middleware

Run the server to test it out. python manage.py runserver

# Task 2 : Restrict Chat Access by time
Objective: implement a middleware that restricts access to the messaging up during certain hours of the day

Instructions:

Create a middleware class RestrictAccessByTimeMiddleware with two methods, __init__and__call__. that check the current server time and deny access by returning an error 403 Forbidden

if a user accesses the chat outside 9PM and 6PM.
Update the settings.py with the middleware.

# Task 3:  Detect and Block offensive Language
Objective: Implement middleware that limits the number of chat messages a user can send within a certain time window, based on their IP address.

Instructions:

Create the middleware class OffensiveLanguageMiddleware with two methods, __init__and__call__. that tracks number of chat messages sent by each ip address and implement a time based limit i.e 5 messages per minutes such that if a user exceeds the limit, it blocks further messaging and returns and error
use the __call__method to count the number of POST requests (messages) from each IP address.
Implement a time window (e.g., 1 minute) during which a user can only send a limited number of messages.
Ensure the middleware is added to theMIDDLEWARE setting in the settings.py

# Task 4:  Enforce chat user Role Permissions
Objective: define a middleware that checks the user’s role i.e admin, before allowing access to specific actions

Instructions:

Create the middleware class RolepermissionMiddleware with two methods, __init__ and __call__. that checks the user’s role from the request
If the user is not admin or moderator, it should return error 403
Ensure the middleware is added to the MIDDLEWARE setting in the settings.py