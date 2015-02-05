/*
 Navicat Premium Data Transfer

 Source Server Type    : PostgreSQL
 Source Server Version : 90305

 Target Server Type    : PostgreSQL
 Target Server Version : 90305
 File Encoding         : utf-8

 Date: 02/05/2015 15:06:21 PM
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
	"is_deleted" bool DEFAULT false
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
--  Primary key structure for table activedirectory
-- ----------------------------
ALTER TABLE "custom"."activedirectory" ADD PRIMARY KEY ("username") NOT DEFERRABLE INITIALLY IMMEDIATE;

