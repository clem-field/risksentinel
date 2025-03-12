-- Associated Findings
--     SQL6-D0-003900
USE master
GO

/* PART 1 OF 2 - Get all permission assignments to logins and roles */

SELECT
    P1.type_desc           AS grantee_type,
    P1.name                AS grantee,
    SP.state_desc,
    SP.permission_name,
	SP.class_desc          AS securable_class,
	CASE SP.class_desc
        WHEN 'SERVER' THEN SERVERPROPERTY('ServerName')
		WHEN 'SERVER_PRINCIPAL' THEN (SELECT name FROM sys.server_principals WHERE principal_id = SP.major_id)
		WHEN 'ENDPOINT' THEN (SELECT name FROM sys.endpoints WHERE endpoint_id = SP.major_id)
		WHEN 'AVAILABILITY GROUP' THEN (SELECT ag.name FROM sys.availability_groups ag JOIN sys.availability_replicas ar ON ar.group_id = ag.group_id WHERE ar.replica_metadata_id = SP.major_id)
    END                    AS securable,
    P2.type_desc           AS grantor_type,
    P2.name                AS grantor
FROM
    sys.server_permissions SP
    INNER JOIN sys.server_principals P1
        ON P1.principal_id = SP.grantee_principal_id
    INNER JOIN sys.server_principals P2
        ON P2.principal_id = SP.grantor_principal_id
GO

/* End Get all permission assignments to logins and roles */


/* PART 2 OF 2 - Get all server role memberships */

SELECT
    R.name    AS server_role,
    M.name    AS role_member
FROM
    sys.server_role_members X
    INNER JOIN sys.server_principals R ON R.principal_id = X.role_principal_id
    INNER JOIN sys.server_principals M ON M.principal_id = X.member_principal_id
GO

/* EndGet all server role memberships */

