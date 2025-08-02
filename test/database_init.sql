-- database_init.sql
SET timezone='UTC';

DO
$do$
BEGIN
	IF NOT EXISTS (
		SELECT FROM pg_catalog.pg_roles  -- SELECT list can be empty for this
    	WHERE rolname = 'prpe_user') THEN
            CREATE ROLE prpe_user WITH PASSWORD '1234';
            GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO prpe_user;
   END IF;
END
$do$;

DO
$do$
BEGIN
   IF NOT EXISTS (
		SELECT FROM pg_catalog.pg_roles  -- SELECT list can be empty for this
    	WHERE rolname = 'prpe_remoteuser') THEN
            CREATE ROLE prpe_remoteuser WITH PASSWORD '1234';
            GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO prpe_remoteuser;
   END IF;
END
$do$;

-- CREATE EXTENSION hstore;

ALTER DATABASE test_db OWNER TO prpe_user;
SET SESSION AUTHORIZATION prpe_user;
