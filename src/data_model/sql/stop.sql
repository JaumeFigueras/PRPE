-- stop.sql

CREATE TYPE location_type_enum AS ENUM ('STOP_OR_PLATFORM', 'STATION', 'ENTRANCE_EXIT', 'GENERIC_NODE', 'BOARDING_AREA');
CREATE TYPE wheelchair_boarding_enum AS ENUM ('NO_INFORMATION', 'SOME_YES', 'NO');
CREATE TABLE stop (
	stop_id VARCHAR NOT NULL,
	stop_code VARCHAR,
	stop_name VARCHAR,
	tts_stop_name VARCHAR,
	stop_desc VARCHAR,
	stop_lat FLOAT,
	stop_lon FLOAT,
	zone_id VARCHAR,
	stop_url VARCHAR,
	location_type location_type_enum,
	parent_stop_id VARCHAR,
	stop_timezone VARCHAR,
	wheelchair_boarding wheelchair_boarding_enum,
	level_id VARCHAR,
	platform_code VARCHAR,
	PRIMARY KEY (stop_id),
	FOREIGN KEY(parent_stop_id) REFERENCES stop (stop_id),
	FOREIGN KEY(level_id) REFERENCES level (level_id)
)
WITH (
  OIDS = FALSE
);
ALTER TABLE public.stop
  OWNER TO prpe_user
;
GRANT ALL on public.stop to prpe_remoteuser;