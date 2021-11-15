CREATE TABLE IF NOT EXISTS Lessons (
    LessonID int PRIMARY KEY,
    GroupID int,
    TeacherID int,
    DayOfWeek tinyint(6),
    StartTime time,
    EndTime time,
    Room char
);

CREATE TABLE IF NOT EXISTS Teachers (
    TeacherID int PRIMARY KEY,
    GroupID int,
    TeacherName char,
    TeacherSubject text,
    TeacherColour char,
    TeacherLink text,
    LessonOnline tinyint(1)
);

CREATE TABLE IF NOT EXISTS Groups (
    GroupID int PRIMARY KEY,
    GroupOwnerID char(18),
    GuildID char(18),
    GroupCode char,
    GroupName text,
    RoleID char(18),
    RoleColour char,
    CaregoryID char(18),
    LessonAnnouncementID char(18),
    NLDayID char(18),
    NLTimeID char(18),
    ImageLink text,
    AlertTimes text
);

CREATE TABLE IF NOT EXISTS Students (
    StudentID int PRIMARY KEY,
    GroupID int,
    UserID char(18),
    Fullname text
);

CREATE TABLE IF NOT EXISTS Assignments(
    AssignmentID int PRIMARY KEY,
    CreatorUserID char(18),
    GroupID char(18),
    TeacherID char(18),
    DueDatetime datetime,
    AssignmentContent text,
    TimeSent timestamp DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS DateReminders (
    ReminderID int PRIMARY KEY,
    CreatorUserID char(18),
    TargetID char(18),
    OutputGuildID char(18),
    OutputChannelID char(18),
    ReminderDatetime datetime,
    Content text,
    TimeSent timestamp DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS RepeatingReminders (
    ReminderID int PRIMARY KEY,
    CreatorUserID char(18),
    TargetID char(18),
    OutputGuildID char(18),
    OutputChannelID char(18),
    RepeatType char,
    ReminderDay char,
    Content text,
    TimeSent timestamp DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS CommandLogs(
    UserID char(18),
    GuildID char(18),
    ChannelID char(18),
    Command text,
    TimeSent timestamp DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS MessageLogs(
    UserID char(18),
    GuildID char(18),
    ChannelID char(18),
    MessageID char(18),
    Command text,
    TimeSent timestamp DEFAULT CURRENT_TIMESTAMP
);