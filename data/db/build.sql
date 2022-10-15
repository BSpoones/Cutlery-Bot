/*
Database configuration for Cutlery Bot
Developed by BSpoones  Nov 21 - 
Solely for use in the Cutlery Bot discord bot
*/


-- Guild, Member, and role tables

CREATE TABLE IF NOT EXISTS guilds (
    guild_id DECIMAL(21,0) PRIMARY KEY,
    owner_id DECIMAL(21,0),
    name     VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS channels (
    guild_id            DECIMAL(21,0),
    channel_id          DECIMAL(21,0) PRIMARY KEY,
    type                VARCHAR(20) NOT NULL,
    name                VARCHAR(100) NOT NULL,
    topic               VARCHAR(1024), -- Channel description
    rate_limit_per_user INT(5), -- 21600 seconds is the longest rate_limit
    bitrate             INT(6), -- 96,000 bits per second, making it 6 digits just in case this goes above 100kb in the future
    user_limit          INT(3), -- Max is 99 users.
    video_quality       VARCHAR(5), -- 5 chars FULL | AUTO
    parent_id           DECIMAL(21,0), -- Category ID
    position            INT(4) NOT NULL,
    permissions         TEXT,
    FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS roles (
    guild_id    DECIMAL(21,0) NOT NULL,
    role_id     DECIMAL(21,0) PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    colour      VARCHAR(6),
    hoisted     BOOL NOT NULL,
    position    INT(4) NOT NULL,
    permissions TEXT,
    blacklisted BOOL DEFAULT 0, -- If True, this role should not be re-added when a user joins the server
    FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS users (
    user_id  DECIMAL(21,0) PRIMARY KEY,
    tag      VARCHAR(37) NOT NULL -- Tag = "{Username}#{Descriminator}", 32 chars for username, 4 chars for descriminator and a #
);

CREATE TABLE IF NOT EXISTS guild_members (
    guild_id  DECIMAL(21,0) NOT NULL,
    user_id   DECIMAL(21,0) NOT NULL,
    joined_at DATETIME NOT NULL,
    nickname  VARCHAR(32),
    FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    PRIMARY KEY (guild_id, user_id)
);

CREATE TABLE IF NOT EXISTS member_roles (
    user_id DECIMAL(21,0) NOT NULL,
    role_id DECIMAL(21,0) NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles (role_id) ON DELETE CASCADE ON UPDATE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- Logging module tables --

-- Stores valid log actions
CREATE TABLE IF NOT EXISTS log_action (
    action_id BIGINT(20) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    action_name VARCHAR(36) NOT NULL UNIQUE
);

-- Stores channel instances
CREATE TABLE IF NOT EXISTS log_channel (
    log_channel_id BIGINT(20) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    guild_id DECIMAL(21,0) NOT NULL,
    channel_id DECIMAL(21,0) NOT NULL,
    FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (channel_id) REFERENCES channels (channel_id) ON DELETE CASCADE ON UPDATE CASCADE

);

-- Stores ignored channels
CREATE TABLE IF NOT EXISTS log_channel_ignore (
    log_channel_id BIGINT(20) UNSIGNED NOT NULL,
    channel_id DECIMAL(21,0) NOT NULL,
    FOREIGN KEY (log_channel_id) REFERENCES log_channel (log_channel_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (channel_id) REFERENCES channels (channel_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Stores the actions which should be logged within each channel
CREATE TABLE IF NOT EXISTS channel_log_action (
  log_channel_id BIGINT(20) UNSIGNED NOT NULL,
  action_id BIGINT(20) UNSIGNED NOT NULL,
  FOREIGN KEY (log_channel_id) REFERENCES log_channel (log_channel_id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (action_id) REFERENCES log_action (action_id) ON DELETE CASCADE ON UPDATE CASCADE,
  PRIMARY KEY (log_channel_id, action_id)
);

CREATE TABLE IF NOT EXISTS message_logs (
    guild_id DECIMAL(21,0) NOT NULL,
    channel_id DECIMAL(21,0) NOT NULL,
    message_id DECIMAL(21,0),
    user_id DECIMAL(21,0) NOT NULL,
    message_content TEXT(4000), -- Nitro message limit
    message_reference DECIMAL(21,0), -- Just a message id
    pinned BOOL NOT NULL,
    tts BOOL NOT NULL,
    attachments_json TEXT, -- a list of attachment links
    -- Components TEXT, NOTE: To be added later
    embeds_json TEXT,
    reactions_json TEXT,
    created_at DATETIME NOT NULL,
    deleted_at DATETIME,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (channel_id) REFERENCES channels (channel_id) ON DELETE CASCADE ON UPDATE CASCADE,
    PRIMARY KEY (message_id)
);

CREATE TABLE IF NOT EXISTS command_logs(
    command_log_id BIGINT(20) UNSIGNED  AUTO_INCREMENT PRIMARY KEY,
    user_id DECIMAL(21,0),
    guild_id DECIMAL(21,0),
    channel_id DECIMAL(21,0),
    command text,
    args text DEFAULT NULL,
    time_sent timestamp DEFAULT CURRENT_TIMESTAMP
);
-- Filter module tables --

-- Converts charset to allow emoji
CREATE TABLE IF NOT EXISTS filter_instances(
    instance_id BIGINT(20) UNSIGNED  AUTO_INCREMENT PRIMARY KEY,
    guild_id DECIMAL(21,0) NOT NULL UNIQUE,
    user_id DECIMAL(21,0) NOT NULL, -- User that created the instance
    role_id DECIMAL(21,0) NOT NULL,
    channel_id DECIMAL(21,0) NOT NULL,
    FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (channel_id) REFERENCES channels (channel_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles (role_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS filter_user_ignore (
    instance_id BIGINT(20) UNSIGNED ,
    user_id DECIMAL(21,0),
    FOREIGN KEY (instance_id) REFERENCES filter_instances (instance_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS filter_role_ignore (
    instance_id BIGINT(20) UNSIGNED ,
    role_id DECIMAL(21,0),
    FOREIGN KEY (instance_id) REFERENCES filter_instances (instance_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS filter_channel_ignore (
    instance_id BIGINT(20) UNSIGNED ,
    channel_id DECIMAL(21,0),
    FOREIGN KEY (instance_id) REFERENCES filter_instances (instance_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (channel_id) REFERENCES channels (channel_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS filters(
    filter_id BIGINT(20) UNSIGNED  AUTO_INCREMENT PRIMARY KEY,
    instance_id BIGINT(20) UNSIGNED NOT NULL,
    name VARCHAR(255) NOT NULL,
    regex TEXT NOT NULL,
    delete_message BOOL NOT NULL,
    warn_user BOOL NOT NULL,
    warn_message TEXT NOT NULL,
    alert_message BOOL NOT NULL,
    FOREIGN KEY (instance_id) REFERENCES filter_instances (instance_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- AutoPurge module -- 

CREATE TABLE IF NOT EXISTS auto_purge (
  auto_purge_id BIGINT(20) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  guild_id DECIMAL(21,0) NOT NULL,
  channel_id DECIMAL(21,0) NOT NULL,
  cutoff INT(6) UNSIGNED NOT NULL, -- Stored in seconds (e.g. 10d1h = 867,600 seconds), max limit is 1209600s (14d)
  ignore_pinned BOOL NOT NULL,
  status_link DECIMAL(21,0) NOT NULL, -- Message ID of the newest status message
  enabled BOOL NOT NULL,
  FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (channel_id) REFERENCES channels (channel_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Admin module --
CREATE TABLE IF NOT EXISTS archives (
    guild_id DECIMAL(21,0) NOT NULL,
    channel_id DECIMAL(21,0) NOT NULL,
    last_archive DATETIME NOT NULL,
    PRIMARY KEY (guild_id, channel_id),
    FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (channel_id) REFERENCES channels (channel_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Lessons module --

CREATE TABLE IF NOT EXISTS lesson_groups (
    lesson_group_id BIGINT(24) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id DECIMAL(21,0),
    group_name VARCHAR(50),
    group_code VARCHAR(50),
    guild_id DECIMAL(21,0),
    role_id DECIMAL(21,0),
    ping_role_id DECIMAL(21,0),
    colour VARCHAR(6),-- 6 chars of hex
    category_id DECIMAL(21,0),
    channel_id DECIMAL(21,0),
    start_date DATETIME, -- Start date of week 1 if group is doing weekly lessons. This is the starting Monday
    nl_day_id DECIMAL(21,0),
    nl_time_id DECIMAL(21,0),
    image_link TEXT,
    alert_times TEXT, -- Seperated by a space
    school TEXT, -- Used for school specific features hard coded in (UoL only)
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles (role_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (ping_role_id) REFERENCES roles (role_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (channel_id) REFERENCES channels (channel_id) ON DELETE CASCADE ON UPDATE CASCADE -- Data persistance on only the announcement channel
);

CREATE TABLE IF NOT EXISTS teachers (
    teacher_id BIGINT(24) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    lesson_group_id BIGINT(24) UNSIGNED,
    name VARCHAR(50),
    colour VARCHAR(6),
    link TEXT, -- If the teacher has an online class link, it'll be used here
    online BOOL, -- If the lesson is online
    FOREIGN KEY (lesson_group_id) REFERENCES lesson_groups (lesson_group_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS subjects (
    subject_id BIGINT(24) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    lesson_group_id BIGINT(24) UNSIGNED,
    name VARCHAR(100),
    colour VARCHAR(6),
    FOREIGN KEY (lesson_group_id) REFERENCES lesson_groups (lesson_group_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS lessons (
    lesson_id BIGINT(24) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    lesson_group_id BIGINT(24) UNSIGNED,
    subject_id BIGINT(24) UNSIGNED,
    teacher_id BIGINT(24) UNSIGNED,
    day_of_week INT(1),
    week_numbers TEXT, /* Used for multi week timetables. With the format x-y (,z). For example Weeks 1-4,7 = Weeks 1,2,3,4,7 */
    start_time VARCHAR(4), -- Using varchar for HHMM
    end_time VARCHAR(4),
    room TEXT,
    lesson_type TEXT, -- Lesson / Lecture / Workshop etc
    FOREIGN KEY (lesson_group_id) REFERENCES lesson_groups (lesson_group_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects (subject_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (teacher_id) REFERENCES teachers (teacher_id) ON DELETE CASCADE ON UPDATE CASCADE

);

CREATE TABLE IF NOT EXISTS students (
    student_id BIGINT(24) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    lesson_group_id BIGINT(24) UNSIGNED,
    user_id DECIMAL(21,0),
    name VARCHAR (100),
    ping BOOL,
    moderator BOOL,
    FOREIGN KEY (lesson_group_id) REFERENCES lesson_groups (lesson_group_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS holidays (
    holiday_id BIGINT(24) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    lesson_group_id BIGINT(24) UNSIGNED,
    start_date datetime,
    end_date datetime,
    FOREIGN KEY (lesson_group_id) REFERENCES lesson_groups (lesson_group_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS assignments (
    assignment_id BIGINT(24) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id DECIMAL(21,0),
    lesson_group_id BIGINT(24) UNSIGNED,
    teacher_id BIGINT(24) UNSIGNED,
    due_at datetime,
    assignment text,
    time_sent timestamp DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (lesson_group_id) REFERENCES lesson_groups (lesson_group_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (teacher_id) REFERENCES teachers (teacher_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Reminder module--
CREATE TABLE IF NOT EXISTS reminders  (
    reminder_code VARCHAR(4) PRIMARY KEY, -- 4 chars of base36 gives 1.6 million possible reminders at once
    owner_id DECIMAL(21,0), -- Whoever created the reminder
    target_type VARCHAR(4), -- role | user | text (If you want to set a target or not)
    target_id DECIMAL(21,0), -- User or Role ID of who is being reminded
    guild_id DECIMAL(21,0),
    channel_id DECIMAL(21,0),
    reminder_type VARCHAR(1), -- Either R, S, or P (Repeating or single or per), 1 chars
    remind_per_frequency BIGINT(24), -- Total seconds to wait for remind per, Null if other type
    remind_per_start DATETIME,
    date_type VARCHAR(8), -- YYYYMMDD is the longest input with 8 chars
    date VARCHAR(9), -- Wednesday is longest input with 9 chars (Null if remind per)
    time VARCHAR(6), -- HHMMSS is longest input with 6 chars (Null if reminmd per)
    todo text,
    private BOOL,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP,
    last_reminder DATETIME DEFAULT NULL,
    FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (channel_id) REFERENCES channels (channel_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (owner_id) REFERENCES users (user_id) ON DELETE CASCADE ON UPDATE CASCADE
    -- Can't add a FK for target since target could be User | Role | "everyone"
)