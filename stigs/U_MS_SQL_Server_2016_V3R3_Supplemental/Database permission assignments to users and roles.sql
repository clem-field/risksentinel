-- Associated Findings
--     SQL6-D0-000300

/* PART 1 OF 3 - Get the database owner */

SELECT ISNULL(SUSER_SNAME(owner_sid),'*** Unknown Database Owner ***') AS database_owner FROM sys.databases
WHERE database_id = DB_ID() AND database_id <> 2
GO

/* End Get the database owner */


/* PART 2 OF 3 - Get all permission assignments to users and roles */

SELECT 
	CASE
		WHEN P1.type_desc IS NULL THEN '*** Unknown Grantee Type : ' + CONVERT(VARCHAR,DP.grantee_principal_id) + ' ***'
		ELSE P1.type_desc
	END AS grantee_type,
	CASE
		WHEN P1.name IS NULL THEN '*** Unknown Grantee : ' + CONVERT(VARCHAR,DP.grantee_principal_id) + ' ***'
		ELSE P1.name
	END AS grantee,
	DP.state_desc,
	DP.permission_name,
	CASE
		WHEN DP.class_desc = 'OBJECT_OR_COLUMN' AND DP.minor_id = 0 THEN COALESCE(AO.type_desc,'OBJECT')
		WHEN DP.class_desc = 'OBJECT_OR_COLUMN' AND DP.minor_id > 0 THEN 'COLUMN'
		ELSE DP.class_desc
	END AS securable_class,
	CASE 
		WHEN DP.class_desc = 'DATABASE' THEN ''
		WHEN DP.class_desc = 'OBJECT_OR_COLUMN' AND SCHEMA_NAME(AO.schema_id) IS NULL THEN ''
		WHEN DP.class_desc = 'OBJECT_OR_COLUMN' THEN SCHEMA_NAME(AO.schema_id)
		WHEN DP.class_desc = 'SCHEMA' THEN (SELECT sdp.name FROM sys.schemas s JOIN sys.database_principals sdp ON s.principal_id = sdp.principal_id WHERE s.schema_id = DP.major_id)
		WHEN DP.class_desc = 'DATABASE_PRINCIPAL' THEN ''
		WHEN DP.class_desc = 'ASSEMBLY' THEN (SELECT adp.name FROM sys.assemblies a JOIN sys.database_principals adp ON a.principal_id = adp.principal_id WHERE a.assembly_id = DP.major_id)
		WHEN DP.class_desc = 'TYPE' THEN (SELECT SCHEMA_NAME(schema_id) FROM sys.types WHERE user_type_id = DP.major_id)
		WHEN DP.class_desc = 'XML_SCHEMA_COLLECTION' THEN (SELECT SCHEMA_NAME(schema_id) FROM sys.xml_schema_collections WHERE xml_collection_id = DP.major_id)
		WHEN DP.class_desc = 'MESSAGE_TYPE' THEN (SELECT mtdp.name FROM sys.service_message_types mt JOIN sys.database_principals mtdp ON mt.principal_id = mtdp.principal_id WHERE mt.message_type_id = DP.major_id)
		WHEN DP.class_desc = 'SERVICE_CONTRACT' THEN (SELECT scdp.name FROM sys.service_contracts sc JOIN sys.database_principals scdp ON sc.principal_id = scdp.principal_id WHERE sc.service_contract_id = DP.major_id)
		WHEN DP.class_desc = 'SERVICE' THEN (SELECT svdp.name FROM sys.services sv JOIN sys.database_principals svdp ON sv.principal_id = svdp.principal_id WHERE sv.service_id = DP.major_id)
		WHEN DP.class_desc = 'REMOTE_SERVICE_BINDING' THEN (SELECT rsbdp.name FROM sys.remote_service_bindings rsb JOIN sys.database_principals rsbdp ON rsb.principal_id = rsbdp.principal_id WHERE rsb.remote_service_binding_id = DP.major_id)
		WHEN DP.class_desc = 'ROUTE' THEN (SELECT rdp.name FROM sys.routes r JOIN sys.database_principals rdp ON r.principal_id = rdp.principal_id WHERE r.route_id = DP.major_id)
		WHEN DP.class_desc = 'FULLTEXT_CATALOG' THEN (SELECT ftdp.name FROM sys.fulltext_catalogs ft JOIN sys.database_principals ftdp ON ft.principal_id = ftdp.principal_id WHERE ft.fulltext_catalog_id = DP.major_id)
		WHEN DP.class_desc = 'SYMMETRIC_KEYS' THEN (SELECT skdp.name FROM sys.symmetric_keys sk JOIN sys.database_principals skdp ON sk.principal_id = skdp.principal_id WHERE sk.symmetric_key_id = DP.major_id)
		WHEN DP.class_desc = 'CERTIFICATE' THEN (SELECT cdp.name FROM sys.certificates c JOIN sys.database_principals cdp ON c.principal_id = cdp.principal_id WHERE c.certificate_id = DP.major_id)
		WHEN DP.class_desc = 'ASYMMETRIC_KEY' THEN (SELECT akdp.name FROM sys.asymmetric_keys ak JOIN sys.database_principals akdp ON ak.principal_id = akdp.principal_id WHERE ak.asymmetric_key_id = DP.major_id)
		WHEN DP.class_desc = 'FULLTEXT_STOPLIST' THEN (SELECT ftsdp.name FROM sys.fulltext_stoplists fts JOIN sys.database_principals ftsdp ON fts.principal_id = ftsdp.principal_id WHERE fts.stoplist_id = DP.major_id)
		WHEN DP.class_desc = 'SEARCH_PROPERTY_LIST' THEN (SELECT spdp.name FROM sys.registered_search_property_lists sp JOIN sys.database_principals spdp ON sp.principal_id = spdp.principal_id WHERE sp.property_list_id = DP.major_id)
		ELSE '*** Unknown ***'
	END AS schema_or_owner,
	CASE 
		WHEN DP.class_desc = 'DATABASE' THEN DB_NAME() 
		WHEN DP.class_desc = 'OBJECT_OR_COLUMN' AND SCHEMA_NAME(AO.schema_id) IS NULL THEN '*** Internal Hidden Object : ' + CONVERT(VARCHAR,DP.major_id) + ' ***'
		WHEN DP.class_desc = 'OBJECT_OR_COLUMN' THEN OBJECT_NAME(AO.object_id) 
		WHEN DP.class_desc = 'SCHEMA' THEN (SELECT SCHEMA_NAME(schema_id) FROM sys.schemas WHERE schema_id = DP.major_id)
		WHEN DP.class_desc = 'DATABASE_PRINCIPAL' THEN (SELECT dp1dp.name FROM sys.database_permissions dp1 JOIN sys.database_principals dp1dp ON dp1dp.principal_id = dp1.major_id WHERE dp1dp.principal_id = DP.major_id AND dp1.grantee_principal_id = DP.grantee_principal_id)
		WHEN DP.class_desc = 'ASSEMBLY' THEN (SELECT a.name FROM sys.assemblies a JOIN sys.database_principals adp ON a.principal_id = adp.principal_id WHERE a.assembly_id = DP.major_id)
		WHEN DP.class_desc = 'TYPE' THEN (SELECT name from sys.types WHERE user_type_id = DP.major_id)
		WHEN DP.class_desc = 'XML_SCHEMA_COLLECTION' THEN (SELECT name FROM sys.xml_schema_collections WHERE xml_collection_id = DP.major_id)
		WHEN DP.class_desc = 'MESSAGE_TYPE' THEN (SELECT name FROM sys.service_message_types WHERE message_type_id = DP.major_id)
		WHEN DP.class_desc = 'SERVICE_CONTRACT' THEN (SELECT name from sys.service_contracts WHERE service_contract_id = DP.major_id)
		WHEN DP.class_desc = 'SERVICE' THEN (SELECT name FROM sys.services WHERE service_id = DP.major_id)
		WHEN DP.class_desc = 'REMOTE_SERVICE_BINDING' THEN (SELECT name FROM sys.remote_service_bindings WHERE remote_service_binding_id = DP.major_id)
		WHEN DP.class_desc = 'ROUTE' THEN (SELECT name FROM sys.routes WHERE route_id = DP.major_id)
		WHEN DP.class_desc = 'FULLTEXT_CATALOG' THEN (SELECT name FROM sys.fulltext_catalogs WHERE fulltext_catalog_id = DP.major_id)
		WHEN DP.class_desc = 'SYMMETRIC_KEYS' THEN (SELECT name FROM sys.symmetric_keys WHERE symmetric_key_id = DP.major_id)
		WHEN DP.class_desc = 'CERTIFICATE' THEN (SELECT name FROM sys.certificates WHERE certificate_id = DP.major_id)
		WHEN DP.class_desc = 'ASYMMETRIC_KEY' THEN (SELECT name FROM sys.asymmetric_keys WHERE asymmetric_key_id = DP.major_id)
		WHEN DP.class_desc = 'FULLTEXT_STOPLIST' THEN (SELECT name FROM sys.fulltext_stoplists WHERE stoplist_id = DP.major_id)
		WHEN DP.class_desc = 'SEARCH_PROPERTY_LIST' THEN (SELECT name FROM sys.registered_search_property_lists WHERE property_list_id = DP.major_id)
		ELSE '*** Unknown ***'
	END COLLATE DATABASE_DEFAULT AS securable,
	CASE 
		WHEN DP.minor_id > 0 THEN AC.name
		ELSE ''
	END AS column_name,
    P2.type_desc AS grantor_type,
	P2.name AS grantor
FROM
    sys.database_permissions DP
	LEFT OUTER JOIN sys.all_objects AO
		ON  DP.major_id = AO.object_id
	LEFT OUTER JOIN sys.all_columns AC
        ON  AC.object_id = DP.major_id
        AND AC.column_id = DP.minor_id
    LEFT OUTER JOIN sys.database_principals P1
        ON  P1.principal_id = DP.grantee_principal_id
    LEFT OUTER JOIN sys.database_principals P2
        ON  P2.principal_id = DP.grantor_principal_id
WHERE 
	(DB_ID() <> 2 AND (DP.major_id >= 0 OR P1.name <> 'public'))
	OR DB_ID() = 1
ORDER BY grantee, schema_or_owner, securable
GO

/* End Get all permission assignments to users and roles */


/* PART 3 OF 3 - Get all database role memberships */

SELECT
    R.name  AS database_role,
    M.name  AS role_member
FROM
    sys.database_role_members X
    INNER JOIN sys.database_principals R ON R.principal_id = X.role_principal_id
    INNER JOIN sys.database_principals M ON M.principal_id = X.member_principal_id
WHERE DB_ID() <> 2
GO

/* End Get all database role memberships */
GO

