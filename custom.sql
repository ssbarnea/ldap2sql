/*
 Navicat Premium Data Transfer

 Source Server         : atlas
 Source Server Type    : PostgreSQL
 Source Server Version : 90305
 Source Host           : atlas.xs.citrite.net
 Source Database       : jira
 Source Schema         : custom

 Target Server Type    : PostgreSQL
 Target Server Version : 90305
 File Encoding         : utf-8

 Date: 02/09/2015 19:20:30 PM
*/

-- ----------------------------
--  Table structure for activedirectory
-- ----------------------------
DROP TABLE IF EXISTS "custom"."activedirectory";
CREATE TABLE "custom"."activedirectory" (
	"username" varchar NOT NULL COLLATE "default",
	"mail" varchar COLLATE "default",
	"title" varchar COLLATE "default",
	"managerdn" varchar COLLATE "default",
	"country" varchar COLLATE "default",
	"locale" varchar COLLATE "default",
	"state" varchar COLLATE "default",
	"distinguishedname" varchar COLLATE "default",
	"postalcode" varchar COLLATE "default",
	"phone" varchar COLLATE "default",
	"created" date,
	"changed" date,
	"givenname" varchar COLLATE "default",
	"fax" varchar COLLATE "default",
	"department" varchar COLLATE "default",
	"company" varchar COLLATE "default",
	"streetaddress" varchar COLLATE "default",
	"objectguid" varchar COLLATE "default",
	"samaccounttype" varchar COLLATE "default",
	"mobile" varchar COLLATE "default",
	"samaccountname" varchar COLLATE "default",
	"has_gravatar" bool,
	"is_active" bool,
	"gravatar_check_date" date,
	"info" varchar COLLATE "default",
	"vp" varchar COLLATE "default",
	"region" varchar COLLATE "default",
	"office" varchar COLLATE "default",
	"manager" varchar COLLATE "default",
	"is_deleted" bool DEFAULT false,
	"name" varchar COLLATE "default",
	"useraccountcontrol" int8,
	"counter" int8 NOT NULL DEFAULT 0
)
WITH (OIDS=FALSE);
ALTER TABLE "custom"."activedirectory" OWNER TO "jira";

COMMENT ON COLUMN "custom"."activedirectory"."country" IS 'country';
COMMENT ON COLUMN "custom"."activedirectory"."locale" IS 'location / city';
COMMENT ON COLUMN "custom"."activedirectory"."state" IS 'State';
COMMENT ON COLUMN "custom"."activedirectory"."vp" IS 'take it from extensionAttribute14';
COMMENT ON COLUMN "custom"."activedirectory"."region" IS 'extensionAttribute15';
COMMENT ON COLUMN "custom"."activedirectory"."office" IS 'extensionAttribute3';

-- ----------------------------
--  Table structure for stats
-- ----------------------------
DROP TABLE IF EXISTS "custom"."stats";
CREATE TABLE "custom"."stats" (
	"date" date NOT NULL,
	"workflows" numeric,
	"customfields" numeric,
	"issues" numeric,
	"projects" numeric,
	"users" numeric,
	"users_active" numeric
)
WITH (OIDS=FALSE);
ALTER TABLE "custom"."stats" OWNER TO "jira";

-- ----------------------------
--  View structure for filters
-- ----------------------------
DROP VIEW IF EXISTS "custom"."filters";
CREATE VIEW "custom"."filters" AS  SELECT sr.id,
    sr.filtername,
    sr.authorname,
    sr.description,
    sr.username,
    sr.groupname,
    sr.projectid,
    sr.reqcontent,
    sr.fav_count,
    sr.filtername_lower,
    u.active,
    (sp.id IS NOT NULL) AS is_shared
   FROM ((searchrequest sr
     LEFT JOIN users u ON (((sr.authorname)::text = (u.user_name)::text)))
     LEFT JOIN sharepermissions sp ON (((sp.entityid = sr.id) AND ((sp.entitytype)::text = 'SearchRequest'::text))));

-- ----------------------------
--  View structure for users
-- ----------------------------
DROP VIEW IF EXISTS "custom"."users";
CREATE VIEW "custom"."users" AS  SELECT cwd_user.user_name,
    cwd_user.active,
    cwd_user.email_address
   FROM (cwd_user
     LEFT JOIN cwd_directory ON (((cwd_user.directory_id = cwd_directory.id) AND (cwd_directory.active = (1)::numeric))))
  ORDER BY cwd_directory.directory_position, cwd_user.user_name;

-- ----------------------------
--  View structure for issues
-- ----------------------------
DROP VIEW IF EXISTS "custom"."issues";
CREATE VIEW "custom"."issues" AS  SELECT (((p.pkey)::text || '-'::text) || jiraissue.issuenum) AS issuekey,
    jiraissue.assignee,
    jiraissue.reporter,
    jiraissue.creator,
    issuetype.pname AS issuetype,
    jiraissue.summary,
    jiraissue.priority,
    issuestatus.pname AS status,
    resolution.pname AS resolution,
    jiraissue.created,
    jiraissue.updated,
    jiraissue.duedate,
    jiraissue.resolutiondate
   FROM ((((jiraissue
     LEFT JOIN project p ON ((jiraissue.project = p.id)))
     LEFT JOIN resolution ON (((jiraissue.resolution)::text = (resolution.id)::text)))
     LEFT JOIN issuetype ON (((jiraissue.issuetype)::text = (issuetype.id)::text)))
     LEFT JOIN issuestatus ON (((jiraissue.issuestatus)::text = (issuestatus.id)::text)))
  WHERE (jiraissue.security IS NULL);
COMMENT ON VIEW "custom"."issues" IS 'Jira issues
-- excluded secured issues, under 0.1% of them';

-- ----------------------------
--  Primary key structure for table activedirectory
-- ----------------------------
ALTER TABLE "custom"."activedirectory" ADD PRIMARY KEY ("username") NOT DEFERRABLE INITIALLY IMMEDIATE;

-- ----------------------------
--  Primary key structure for table stats
-- ----------------------------
ALTER TABLE "custom"."stats" ADD PRIMARY KEY ("date") NOT DEFERRABLE INITIALLY IMMEDIATE;

