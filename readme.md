# Cutlery Bot
Cutlery Bot (CB) is the fourth iteration of a multipurpose Discord bot devloped in Python3.10 with [hikari-py](https://github.com/hikari-py/hikari) and [tanjun](https://github.com/FasterSpeeding/Tanjun).

Other documentation and tutorials can be found [here](https://www.bspoones.com/)
--------

Planned features:

 - Assignments
    - Role based assignment / homework reminders with seperate custom alerts
    - Ability to add or remove reminders through commands
    - Ability to view all current assignments for a group
    - Assignments will show on a user's daily | weekly schedule
 - GIF
    - Ability to read and create slash commands from an iamge input in a database

An unfinished command will have the prefix `NF` in the commands table

# Current Module commands:

**Admin**

The Admin module consists of commands that directly affect the bot itself. These are only allowed to be used by bot owners

| Command | Args | Description |
|---------|------|-------------|
| Closebot| | Closes the bot (Owner only) |
| RestartBot | | | Restarts the bot (Owner only) |
| SetActivity | (type) (activity) [link] [permanent] | Sets the activity for the bot |

**Logging**

The Logging module is responsible for logging any and all guild events (such as user joins, user leaves etc) to a given logging instance.

| Command | Args | Description |
|---------|------|-------------|
| Addlogger | (preset) [channel] | Creates a logging instance for a given guild channel with a preset | 
| AddLoggingEvent |  | |
| RemoveLoggingEvent | | |
| RemoveLogger | | |

**Reminder**

The Reminder module is responsible for reminding users at a requested time and frequency.

| Command | Args | Description |
|---------|------|-------------|
| RemindEvery |  (date) (time) (todo) [private] [target] | Sends a repeating reminder on a specific date and time. |
| RemindIn | (when) (todo) [target] [private] | Sends a reminder to a target after a given amount of time (1y1m1d = 1 year, 1 month, and 1 day into the future). |
| RemindOn | (date) (time) (todo) [private] [target] | Sends a reminder on a specific date and time. |
| DeleteReminder | (id) | Deletes a reminder |
| ShowReminders| [page] [amount] [serveronly] | Shows your own reminders |

**Timetable**

The Timetable module is responsible for all parts of the bot's handling of lessons. This module gives lesson and assignment announcements as well as commands to display lesson information.

| Command | Args | Description |
|---------|------|-------------|
| Current lesson | [group] | Sh  ows the current lesson for you or a given group |
| Next lesson | [group] | Shows the next lesson for you or a given group|
| Schedule | [day] [group] | Shows your schedule for a given day |
| AddHoliday | (start) (end) [group] | Adds a holiday for a group |
| ShowHolidays | [group] | Shows all holidays for a group or user |
| DeleteHoliday | (id) | Deletes a holiday |
| `NF` Weekly Schedule| [group]| Shows assignment, lesson and reminder information for your week |

**Utility**
The Utility module is responsible for miscellaneous commands.

| Command | Args | Description |
|---------|------|-------------|
| Big | (emoji) | Enlarges any unicode or custom discord emoji |
| Botinfo | | Shows the current status of the bot |
| Command leaderboard | [page] [amount] [serveronly] | Shows a pagenated view of the most popular commands |
| Command logs | [page] [amount] [serveronly] | Shows a pagenated view of all command logs |
| Define | (word) | Gets the dictionary definition of a word |
| Ping | | Shows the current heartbeat latency of the bot |
| Purge | (limit) | Purges X messages in chat |
| Serverinfo | | Shows information about a server |
| Type | (message) [private] [channel] | Gets the bot to type a message in chat or to a specified text channel |
| Uptime | | Shows how long the bot has been on for |
| Userinfo | [@user] | Shows information about a user |
| Version | | Shows the version information of the bot |
| `NF` Help | [module / command] | Shows information about a chosen command or module |
| `NF` Sudoku | [difficulty] | Creates a sudoku grid |
| `NF` QR code | (link) | Creates a QR code from a chosen input |
| `NF` Storytime | | Uses natural language processing to create a randomly generated story |

- `[VALUE]` or `[OPT | OPT2 | OPT3]` indicates an OPTIONAL argument.
- `(VALUE)` or `(OPT | OPT2 | OPT3)` indicates a REQUIRED argument.
- `{ARG|DEFAULT}` indicates an OPTIONAL argument with default value.
- `ALL CAPS` indicates exact input value.
- `Camel Case` indicates unknown value title.

--------

Completed Features:

 - Reminder
    - Delivery of single or repeating reminders for a user
    - Ability to create, view and delete reminders
    - Storage of reminder details in a MySQL database
    - Text - datetime parsing (regex-based patterns) to convert a string `1y1m1d` to a datetime object
    - Creation of CronTrigger APscheduler jobs from a database entry
 - Timetable
    - Role based lesson warnings with a custom alert time feature
    - Calculation and display of a user's daily timetable / schedule
    - `NF` Calculation and display of a user's weekly timetable / schedule using a PILLOW image
    - Calculation of a user's next lesson
    - Calculation of a user's current lesson
    - `NF` Command based input of Groups, Teachers, Lessons, and Students
    - `NF` Command based removal of Groups, Teachers, Lessons, and Students
    - `NF` Secure method to search through groups