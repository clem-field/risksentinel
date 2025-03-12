USE [master];
GO

/****************************************/
/* Set variables needed by setup script */
DECLARE	@auditName varchar(25), @auditPath varchar(260), @auditGuid uniqueidentifier, @auditFileSize varchar(4), @auditFileCount varchar(4)

-- Define the name of the audit
SET @auditName = 'STIG_AUDIT'

-- Define the directory in which audit log files reside
SET @auditPath = 'C:\Audits'

-- Define the unique identifier for the audit
SET @auditGuid = NEWID()

-- Define the maximum size for a single audit file (MB)
SET @auditFileSize = 200

-- Define the number of files that should be kept online
-- Use -1 for unlimited
SET @auditFileCount = 50

/****************************************/

/* Insert the variables into a temp table so they survive for the duration of the script */
CREATE TABLE #SetupVars
(
	Variable	varchar(50),
	Value		varchar(260)
)
INSERT	INTO #SetupVars (Variable, Value)
		VALUES	('auditName', @auditName),
				('auditPath', @auditPath),
				('auditGuid', convert(varchar(40), @auditGuid)),
				('auditFileSize', @auditFileSize),
				('auditFileCount', @auditFileCount)

/****************************************/
/* Delete the audit if is currently exists */
/****************************************/

USE [master];
GO

-- Disable the Server Audit Specification
DECLARE	@auditName varchar(25), @disableSpecification nvarchar(max)
SET		@auditName = (SELECT Value FROM #SetupVars WHERE Variable = 'auditName')
SET		@disableSpecification = '
IF EXISTS (SELECT 1 FROM sys.server_audit_specifications WHERE name = N''' + @auditName + '_SERVER_SPECIFICATION'')
ALTER SERVER AUDIT SPECIFICATION [' + @auditName + '_SERVER_SPECIFICATION] WITH (STATE = OFF);'
EXEC(@disableSpecification)
GO

-- Drop the Server Audit Specification
DECLARE	@auditName varchar(25), @dropSpecification nvarchar(max)
SET		@auditName = (SELECT Value FROM #SetupVars WHERE Variable = 'auditName')
SET		@dropSpecification = '
IF EXISTS (SELECT 1 FROM sys.server_audit_specifications WHERE name = N''' + @auditName + '_SERVER_SPECIFICATION'')
DROP SERVER AUDIT SPECIFICATION [' + @auditName + '_SERVER_SPECIFICATION];'
EXEC(@dropSpecification)
GO

-- Disable the Server Audit
DECLARE	@auditName varchar(25), @disableAudit nvarchar(max)
SET		@auditName = (SELECT Value FROM #SetupVars WHERE Variable = 'auditName')
SET		@disableAudit = '
IF EXISTS (SELECT 1 FROM sys.server_audits WHERE name = N''' + @auditName + ''')
ALTER SERVER AUDIT [' + @auditName + '] WITH (STATE = OFF);'
EXEC(@disableAudit)
GO

-- Drop the Server Audit
DECLARE	@auditName varchar(25), @dropAudit nvarchar(max)
SET		@auditName = (SELECT Value FROM #SetupVars WHERE Variable = 'auditName')
SET		@dropAudit = '
IF EXISTS (SELECT 1 FROM sys.server_audits WHERE name = N''' + @auditName + ''')
DROP SERVER AUDIT [' + @auditName + '];'
EXEC(@dropAudit)
GO

/****************************************/
/* Set up the SQL Server Audit          */
/****************************************/

USE [master];
GO

/* Create the Server Audit */
DECLARE	@auditName varchar(25), @auditPath varchar(260), @auditGuid varchar(40), @auditFileSize varchar(4), @auditFileCount varchar(5)

SELECT @auditName = Value FROM #SetupVars WHERE Variable = 'auditName'
SELECT @auditPath = Value FROM #SetupVars WHERE Variable = 'auditPath'
SELECT @auditGuid = Value FROM #SetupVars WHERE Variable = 'auditGuid'
SELECT @auditFileSize = Value FROM #SetupVars WHERE Variable = 'auditFileSize'
SELECT @auditFileCount = Value FROM #SetupVars WHERE Variable = 'auditFileCount'

DECLARE @createStatement	nvarchar(max)
SET		@createStatement = '
CREATE SERVER AUDIT [' + @auditName + ']
TO FILE
( 
	FILEPATH = ''' + @auditPath + '''
	, MAXSIZE = ' + @auditFileSize + ' MB
	, MAX_ROLLOVER_FILES = ' + CASE WHEN @auditFileCount = -1 THEN 'UNLIMITED' ELSE @auditFileCount END + '
	, RESERVE_DISK_SPACE = OFF
)
WITH
( 
	QUEUE_DELAY = 1000
	, ON_FAILURE = SHUTDOWN
	, AUDIT_GUID = ''' + @auditGuid + '''
)
'

EXEC(@createStatement)
GO

/* Turn on the Audit */
DECLARE	@auditName varchar(25), @enableAudit nvarchar(max)
SET		@auditName = (SELECT Value FROM #SetupVars WHERE Variable = 'auditName')
SET		@enableAudit = '
IF EXISTS (SELECT 1 FROM sys.server_audits WHERE name = N''' + @auditName + ''')
ALTER SERVER AUDIT [' + @auditName + '] WITH (STATE = ON);'
EXEC(@enableAudit)
GO

/* Create the server audit specifications */
DECLARE	@auditName varchar(25), @createSpecification nvarchar(max)
SET		@auditName = (SELECT Value FROM #SetupVars WHERE Variable = 'auditName')
SET		@createSpecification = '
CREATE SERVER AUDIT SPECIFICATION [' + @auditName + '_SERVER_SPECIFICATION]
FOR SERVER AUDIT [' + @auditName + ']
	ADD (APPLICATION_ROLE_CHANGE_PASSWORD_GROUP),     --    SQL6-D0-011800, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-015100
	ADD (AUDIT_CHANGE_GROUP),                         --    SQL6-D0-011800, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-015100
	ADD (BACKUP_RESTORE_GROUP),                       --    SQL6-D0-011800, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-015100
	ADD (DATABASE_CHANGE_GROUP),                      --    SQL6-D0-011800, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-015100
	ADD (DATABASE_OBJECT_ACCESS_GROUP),               --    SQL6-D0-011800
	ADD (DATABASE_OBJECT_CHANGE_GROUP),               --    SQL6-D0-011800, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-015100
	ADD (DATABASE_OBJECT_OWNERSHIP_CHANGE_GROUP),     --    SQL6-D0-013400, SQL6-D0-011800, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-014200, SQL6-D0-015100, SQL6-D0-013600
	ADD (DATABASE_OBJECT_PERMISSION_CHANGE_GROUP),    --    SQL6-D0-013400, SQL6-D0-011800, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-014200, SQL6-D0-015100, SQL6-D0-013600
	ADD (DATABASE_OPERATION_GROUP),                   --    SQL6-D0-011800, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-015100
	ADD (DATABASE_OWNERSHIP_CHANGE_GROUP),            --    SQL6-D0-013400, SQL6-D0-011800, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-014200, SQL6-D0-015100, SQL6-D0-013600
	ADD (DATABASE_PERMISSION_CHANGE_GROUP),           --    SQL6-D0-013400, SQL6-D0-011800, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-014200, SQL6-D0-015100, SQL6-D0-013600
	ADD (DATABASE_PRINCIPAL_CHANGE_GROUP),            --    SQL6-D0-011800, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-015100
	ADD (DATABASE_PRINCIPAL_IMPERSONATION_GROUP),     --    SQL6-D0-011800, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-015100
	ADD (DATABASE_ROLE_MEMBER_CHANGE_GROUP),          --    SQL6-D0-013400, SQL6-D0-011800, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-014200, SQL6-D0-015100, SQL6-D0-013600
	ADD (DBCC_GROUP),                                 --    SQL6-D0-011800, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-015100
	ADD (FAILED_LOGIN_GROUP),                         --    SQL6-D0-014800
	ADD (LOGIN_CHANGE_PASSWORD_GROUP),                --    SQL6-D0-011800, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-015100
	ADD (LOGOUT_GROUP),                               --    SQL6-D0-015000, SQL6-D0-015100

	-- The SCHEMA_OBJECT_ACCESS_GROUP is intentionally commented out. Refer to the findings listed to the right before including this event.
	-- ADD (SCHEMA_OBJECT_ACCESS_GROUP),              --    SQL6-D0-004600, SQL6-D0-012900, SQL6-D0-013200, SQL6-D0-014000, SQL6-D0-014600, SQL6-D0-015400
	ADD (SCHEMA_OBJECT_CHANGE_GROUP),                 --    SQL6-D0-011800, SQL6-D0-013800, SQL6-D0-014400, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-015100
	ADD (SCHEMA_OBJECT_OWNERSHIP_CHANGE_GROUP),       --    SQL6-D0-011800, SQL6-D0-013400, SQL6-D0-013600, SQL6-D0-014200, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-015100 
	ADD (SCHEMA_OBJECT_PERMISSION_CHANGE_GROUP),      --    SQL6-D0-011800, SQL6-D0-013400, SQL6-D0-013600, SQL6-D0-014200, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-015100 
	ADD (SERVER_OBJECT_CHANGE_GROUP),                 --    SQL6-D0-011800, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-015100
	ADD (SERVER_OBJECT_OWNERSHIP_CHANGE_GROUP),       --    SQL6-D0-011800, SQL6-D0-013400, SQL6-D0-013600, SQL6-D0-014200, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-015100
	ADD (SERVER_OBJECT_PERMISSION_CHANGE_GROUP),      --    SQL6-D0-011800, SQL6-D0-013400, SQL6-D0-013600, SQL6-D0-014200, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-015100
	ADD (SERVER_OPERATION_GROUP),                     --    SQL6-D0-011800, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-015100
	ADD (SERVER_PERMISSION_CHANGE_GROUP),             --    SQL6-D0-011800, SQL6-D0-013400, SQL6-D0-013600, SQL6-D0-014200, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-015100
	ADD (SERVER_PRINCIPAL_CHANGE_GROUP),              --    SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-015100
	ADD (SERVER_PRINCIPAL_IMPERSONATION_GROUP),       --    SQL6-D0-011800, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-015100
	ADD (SERVER_ROLE_MEMBER_CHANGE_GROUP),            --    SQL6-D0-011800, SQL6-D0-013400, SQL6-D0-013600, SQL6-D0-014200, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-015100
	ADD (SERVER_STATE_CHANGE_GROUP),                  --    SQL6-D0-011800, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-015100
	ADD (SUCCESSFUL_LOGIN_GROUP),                     --    SQL6-D0-014800, SQL6-D0-015200
	ADD (TRACE_CHANGE_GROUP),                         --    SQL6-D0-011800, SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-015100
	ADD (USER_CHANGE_PASSWORD_GROUP)                  --    SQL6-D0-014900, SQL6-D0-015000, SQL6-D0-015100
WITH (STATE = ON);'
EXEC(@createSpecification)
GO

/* Clean up */
DROP TABLE #SetupVars