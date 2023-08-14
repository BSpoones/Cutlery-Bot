# Cutlery Bot

### NOTE: This bot is now discontinued, It will continue to be of service for the forseeable future

Predecessor: [Vitaly Petrov](https://github.com/BSpoones/Vitaly-Petrov)  
Successor: [Zephyr](https://github.com/BSpoones/Zephyr)

Cutlery Bot is a multi-purpose Discord Bot written in [hikari-py](https://github.com/hikari-py/hikari) and [tanjun](https://github.com/FasterSpeeding/Tanjun).

Information and tutorials about Cutlery Bot can be found [here](https://www.bspoones.com/Cutlery-Bot)

--------
# Features

#### Moderation
 - **BanAll**: BanAll is a command that can ban all users that match a given string or a regular expression. This is useful for server raids, where multiple users of the same name join such as `SpamBot#0001`, `SpamBot#0002` etc.
 - **Archive**: Archive allows you to back-up a channel or a server's messages to a database to track message edits and deletions for your entire server. It's advised to only use this on a private server, where all users consent to their messages being stored.
 - **AutoPurge**: AutoPurge allows for all messages older than a defined timeframe to be deleted. This can help to de-clutter channels or to keep channels like bot-commands clean.
 - **Logging**: Cutlery Bot is able to log almost all discord events, from user joins to channel creation to message edits. This is a powerful tool to help moderate your server
 - **Purge**: This removes x messages from a channel. This can also purge messages that max a regex filter within a given range or purge a custom range of messages depending on the message ID

#### Reminders
 - **Remind at**: Send a reminder at a specific time. E.g you could set a reminder for 22:00, this would send at the next occurence of 22:00, wether it was today or the day after
 - **Remind every**: Send a repeating reminder that matches a condition. E.g remind every Sunday at 09:00, or every year at a specific datetime
 - **Remind in**: Send a reminder in a determined amount of time. E.g 10 minutes into the future
 - **Remind per**: Send a reminder once per time frame. For example send a reminder once every 4 days

#### Timetables
 - **Timetables**: Import your school or university timetable into Cutlery Bot, sending pings before your lessons to help you learn your timetable.
 - **Schedules**: Show a daily schedule, listing all lessons/lectures for the day, as well as any reminders or assignments that are scheduled to occur on that day
 - **WeeklySchedule**: Similar to schedule, but this command creates an image of your week's schedule, showing all lessons and `[NF]` reminders.
 - **NextLesson**: Find out when and where your next lesson will occur
 - **CurrentLesson**: Find out how long there is until your current lesson/lecture finishes
 - **Holidays**: Set custom holidays, which will affect your lesson announcements and schedules

#### Utility / Fun
 - **Big**: Enlarge an emoji! This now works for both default and custom discord emojis
 - **Command Logs**: Show the most recent command uses in your server or bot-wide!
 - **Command Leaderboard**: Show the most used Cutlery Bot commands!
 - **Define**: Get the dictionary definition of a word
 - **UrbanDefine**: Get the Urban Dictionary definition of a word. (Warning: These results may be NSFW!)
 - **User Info**: Find out information about a user
 - **Server Info**: Find out information about your server


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
| archive channel | (channel) [bypass_last_archive] | Archives all messages in a channel |
| archive all | [bypass_last_archive] | Archives all messages in all text channels in a guild|
| Bot close | | Closes the bot |
| Bot restart | | Restart the bot |
| Bot info | | Displays info about the bot |
| Bot SetActivity | (type) (activity) [link] [permanent] | Sets the activity for the bot |

**AutoPurge**

The AutoPurge module is responsible for automatically purging messages sent earlier than x amount of time.

| Command | Args | Description |
|---------|------|-------------|
| autopurge setup | (cutoff) [channel] [purge_pinned] [guild_wide] | Sets up an AutoPurge instance in a given channel |
| autopurge cutoff | (cutoff) [channel] | Sets a new AutoPurge cutoff |
| autopurge enable | [channel] | Enables AutoPurge |
| autopurge disable | [channel] | Disables AutoPurge |
| autopurge status | [channel] | Shows the current AutoPurge status |

**Logging**

The Logging module is responsible for logging any and all guild events (such as user joins, user leaves etc) to a given logging instance.

| Command | Args | Description |
|---------|------|-------------|
| logging enable | (preset) [channel] | Sets up a logging instance for a given guild channel with a preset | 
| logging add | (preset) [channel] | Adds a specific discord event to a logging instance |
| logging remove | (preset) [channel] | Removes a specific discord event from a logging instance |
| logging disable | [channel] | Removes the logging instance for a given guild channel |

**Reminder**

The Reminder module is responsible for reminding users at a requested time and frequency.

| Command | Args | Description |
|---------|------|-------------|
| remind every |  (date) (time) (todo) [private] [target] | Sends a repeating reminder on a specific date and time. |
| remind in | (when) (todo) [target] [private] | Sends a reminder to a target after a given amount of time (1y1m1d = 1 year, 1 month, and 1 day into the future). |
| remind at | (date) (time) (todo) [private] [target] | Sends a reminder on a specific date and time. |
| remind per | (timeframe) (todo) [private] [target] | Sets a repeating reminder, to remind every timeframe. |
| remind delete | (id) | Deletes a reminder |
| remind list | [page] [amount] [serveronly] | Shows your own reminders |

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
    - Secure method to search through groups
