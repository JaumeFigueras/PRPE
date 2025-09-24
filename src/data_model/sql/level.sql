-- level.sql

CREATE TABLE level (
	level_id VARCHAR NOT NULL,
	level_index FLOAT NOT NULL,
	level_name VARCHAR,
	PRIMARY KEY (level_id)
)
WITH (
  OIDS = FALSE
);
ALTER TABLE public.level
  OWNER TO prpe_user
;
GRANT ALL on public.level to prpe_remoteuser;
