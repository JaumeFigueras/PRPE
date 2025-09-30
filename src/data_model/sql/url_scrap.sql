-- url_scrap.sql

CREATE TYPE url_type_enum AS ENUM ('ADIF_WEB', 'ADIF_JS_INFO');
CREATE TABLE url_scrap (
	url_id SERIAL NOT NULL,
	url VARCHAR NOT NULL,
	url_type url_type_enum NOT NULL,
	stop_id VARCHAR,
	PRIMARY KEY (url_id),
	UNIQUE (url),
	FOREIGN KEY(stop_id) REFERENCES stop (stop_id)
)
WITH (
  OIDS = FALSE
);
ALTER TABLE public.url_scrap
  OWNER TO prpe_user
;
GRANT ALL on public.url_scrap to prpe_remoteuser;
