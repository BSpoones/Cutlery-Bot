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
| Purge | (limit) | Purges X messages in chat|
| Type | (message) [private] | Gets the bot to type a message in chat |
| Define | (word) | Gets the dictionary definition of a word |
| Urbandefine | (word) | Uses the urban dictionary API to get the urban definition of a word or phrase |
| Big | (emoji) | Enlarges any unicode or custom discord emoji |
| Ping | | Shows the current heartbeat ping of the bot |
| Version | | Shows the version information of the bot |
| Botinfo | | Shows the current status of the bot |
| Uptime | | Shows how long the bot has been on for |
| Userinfo | [@user] | Shows information about a user |
| Serverinfo | | Shows information about a server|
| Command leaderboard | [page] [amount] [serveronly] | Shows a pagenated view of the most popular commands |
| Command logs | [page] [amount] [serveronly] | Shows a pagenated view of all command logs |
| Remind every | (@target) (date) (time) (todo) [private] | Sets a reoccouring reminder |
| Remind in | (@target) (when) (todo) [private] | Sets a reminder for a time in the future `1y1m1d` format|
| Remind on | (@target) (date) (time) (todo) [private] | Sets a reminder for a specific time in the future |
| Show reminders | [page] [amount] [serveronly] | Shows all reminders that you have created or are the target for |
| Delete reminder | (id) | Deletes a reminder |
| Sudoku | [difficulty] | Creates a sudoku grid |
| QR code | (link) | Creates a QR code from a chosen input |
| Storytime | | Uses natural language processing to create a randomly generated story |
| Help | [module | command] | Shows information about a chosen command or module |
| Close bot | | Closes the bot |
| Restart bot | | Restarts the bot |
| Setactivity | (activity type) (activity) | Sets the activity for the bot |
| Schedule | [day] [group] | Shows your schedule for a given day |
| Next lesson | [group] | Shows the next lesson for you or a given group|
| Current lesson | [group] | Shows the current lesson for you or a given group |
| Weekly Schedule| [group]| Shows assignment, lesson and reminder information for your week |

- `[VALUE]` or `[OPT | OPT2 | OPT3]` indicates an OPTIONAL argument.
- `(VALUE)` or `(OPT | OPT2 | OPT3)` indicates a REQUIRED argument.
- `{ARG|DEFAULT}` indicates an OPTIONAL argument with default value.
- `ALL CAPS` indicates exact input value.
- `Camel Case` indicates unknown value title.

--------

Completed Features: