/*
Database configuration for Cutlery Bot
Developed by BSpoones  Nov 21 - Feb 22
Solely for use in the Cutlery Bot discord bot
*/

CREATE TABLE IF NOT EXISTS Lessons (
    LessonID BIGINT(24) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    GroupID INT(32),
    TeacherID INT(32),
    SubjectID INT(32),
    DayOfWeek tinyint(6),
    WeekNumber tinyint(2), -- 0 - 52, used to check multi week timetables
    StartTime VARCHAR(4),
    EndTime VARCHAR(4),
    Room VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS LessonGroups (
    GroupID BIGINT(24) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    GroupOwnerID VARCHAR(18),
    GroupName VARCHAR(50),
    GroupCode VARCHAR(50),
    GuildID VARCHAR(18),
    RoleID VARCHAR(18),
    PingRoleID VARCHAR(18),
    RoleColour VARCHAR(7),
    CaregoryID VARCHAR(18),
    AnnouncementID VARCHAR(18),
    NLDayID VARCHAR(18),
    NLTimeID VARCHAR(18),
    ImageLink VARCHAR(256),
    AlertTimes VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS Teachers (
    TeacherID BIGINT(24) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    GroupID BIGINT(32),
    TeacherName VARCHAR(50),
    TeacherColour VARCHAR(7),
    TeacherLink VARCHAR(256),
    LessonOnline BOOL
);

CREATE TABLE IF NOT EXISTS Subjects (
    SubjectID BIGINT(24) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    TeacherID BIGINT(24),
    SubjectName VARCHAR(100),
    SubjectColour VARCHAR(7)
);

CREATE TABLE IF NOT EXISTS Students (
    StudentID BIGINT(24) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    GroupID BIGINT(24),
    UserID VARCHAR(18),
    Fullname VARCHAR (100),
    Pings BOOL,
    Moderator BOOL
);

CREATE TABLE IF NOT EXISTS Holidays (
    HolidayID BIGINT(24) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    GroupID BIGINT(24),
    StartDate datetime,
    EndDate datetime
);

CREATE TABLE IF NOT EXISTS Assignments(
    AssignmentID BIGINT(24) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    CreatorUserID VARCHAR(18),
    GroupID VARCHAR(18),
    TeacherID VARCHAR(18),
    DueDatetime datetime,
    AssignmentContent text,
    TimeSent timestamp DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Reminders (
    ReminderID BIGINT(24) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    CreatorID VARCHAR(18),
    TargetType VARCHAR(4), -- role | user | text
    TargetID VARCHAR(18),
    GuildID VARCHAR(18),
    ChannelID VARCHAR(18),
    ReminderType VARCHAR(1), -- Either R or S (Repeating or single), 1 chars
    DateType VARCHAR(8), -- YYYYMMDD is the longest input with 8 chars
    Date VARCHAR(9), -- Wednesday is longest input with 9 chars
    Time VARCHAR(6), -- HHMMSS is longest input with 6 chars
    Todo text,
    Private BOOL,
    TimeSent timestamp DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS CommandLogs(
    CommandLogID BIGINT(24) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    UserID VARCHAR(18),
    GuildID VARCHAR(18),
    ChannelID VARCHAR(18),
    Command text,
    Args text DEFAULT NULL,
    TimeSent timestamp DEFAULT CURRENT_TIMESTAMP
)