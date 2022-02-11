# Cutlery Bot
Cutlery Bot (CB) is the fourth iteration of a multipurpose Discord bot devloped in Python3.10 with [hikari-py](https://github.com/hikari-py/hikari) and [tanjun](https://github.com/FasterSpeeding/Tanjun).

--------

Planned features:
 - Reminder
    - Delivery of single or repeating reminders for a user
    - Ability to create, view and delete reminders
    - Storage of reminder details in a MySQL database
    - Text - datetime parsing (regex-based patterns) to convert a string `1y1m1d` to a datetime object
    - Creation of CronTrigger APscheduler jobs from a database entry
 - Timetable
    - Role based lesson warnings with a custom alert time feature
    - Calculation and display of a user's daily timetable / schedule
    - Calculation and display of a user's weekly timetable / schedule using a PILLOW image
    - Calculation of a user's next lesson
    - Calculation of a user's current lesson
    - Command based input of Groups, Teachers, Lessons, and Students
    - Command based removal of Groups, Teachers, Lessons, and Students
    - Secure ID based system to search through groups
 - Assignments
    - Role based assignment / homework reminders with seperate custom alerts
    - Ability to add or remove reminders through commands
    - Ability to view all current assignments for a group
    - Assignments will show on a user's daily | weekly schedule
 - GIF
    - Ability to read and create slash commands from an iamge input in a database

- Commands:

| Command | Args | Description |
|---------|------|-------------|
| Purge | | |
| Type | | |
| Define | | |
| Urbandefine | | |
| Big | | |
| Ping | | |
| Version | | |
| Botinfo | | |
| Uptime | | |
| Userinfo | | |
| Serverinfo | | |
| Command leaderboard | | |
| Command logs | | |
| Remind every | | |
| Remind in | | |
| Remind on | | |
| Show reminders | | |
| Delete reminder | | |
| Sudoku | | |
| QR code | | |
| Storytime | | |
| Help | | |
| Close bot | | |
| Restart bot | | |
| Setactivity | | |
| Schedule | | |
| Next lesson | | |
| Current lesson | | |
| Weekly Schedule| | |

- `[VALUE]` or `[OPT | OPT2 | OPT3]` indicates an OPTIONAL argument.
- `(VALUE)` or `(OPT | OPT2 | OPT3)` indicates a REQUIRED argument.
- `{ARG|DEFAULT}` indicates an OPTIONAL argument with default value.
- `ALL CAPS` indicates exact input value.
- `Camel Case` indicates unknown value title.

--------

Completed Features: