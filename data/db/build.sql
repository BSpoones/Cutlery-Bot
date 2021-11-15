CREATE TABLE IF NOT EXISTS Lessons (
    LessonID BIGINT(24) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    GroupID INT(32),
    TeacherID INT(32),
    DayOfWeek tinyint(6),
    StartTime TIME,
    EndTime TIME,
    Room VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS Teachers (
    TeacherID BIGINT(24) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    GroupID INT(32),
    TeacherName VARCHAR(50),
    TeacherSubject VARCHAR(100),
    TeacherColour VARCHAR(7),
    TeacherLink VARCHAR(256),
    LessonOnline BOOL
);

CREATE TABLE IF NOT EXISTS LessonGroups (
    GroupID BIGINT(24) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    GroupOwnerID VARCHAR(18),
    GuildID VARCHAR(18),
    GroupCode VARCHAR(50),
    GroupName VARCHAR(50),
    RoleID VARCHAR(18),
    RoleColour VARCHAR(7),
    CaregoryID VARCHAR(18),
    LessonAnnouncementID VARCHAR(18),
    NLDayID VARCHAR(18),
    NLTimeID VARCHAR(18),
    ImageLink VARCHAR(256),
    AlertTimes VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS Students (
    StudentID BIGINT(24) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    GroupID int,
    UserID VARCHAR(18),
    Fullname text
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

CREATE TABLE IF NOT EXISTS DateReminders (
    ReminderID BIGINT(24) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    CreatorUserID VARCHAR(18),
    TargetID VARCHAR(18),
    OutputGuildID VARCHAR(18),
    OutputChannelID VARCHAR(18),
    ReminderDatetime datetime,
    Content text,
    TimeSent timestamp DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS RepeatingReminders (
    ReminderID  BIGINT(24) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    CreatorUserID VARCHAR(18),
    TargetID VARCHAR(18),
    OutputGuildID VARCHAR(18),
    OutputChannelID VARCHAR(18),
    RepeatType char,
    ReminderDay char,
    Content text,
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
);

CREATE TABLE IF NOT EXISTS MessageLogs(
    MessageLogID BIGINT(24) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    UserID VARCHAR(18),
    GuildID VARCHAR(18),
    ChannelID VARCHAR(18),
    MessageID VARCHAR(18),
    Command text,
    TimeSent timestamp DEFAULT CURRENT_TIMESTAMP
)