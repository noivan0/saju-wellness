--
-- PostgreSQL database dump
--


-- Dumped from database version 14.22 (Ubuntu 14.22-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.22 (Ubuntu 14.22-0ubuntu0.22.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: saju_readings; Type: TABLE; Schema: public; Owner: saju
--

CREATE TABLE public.saju_readings (
    id integer NOT NULL,
    session_id character varying(64) NOT NULL,
    birth_year integer,
    birth_month integer,
    birth_day integer,
    birth_hour integer,
    gender character varying(10),
    day_pillar character varying(10),
    primary_element character varying(5),
    pillars_json jsonb,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.saju_readings OWNER TO saju;

--
-- Name: saju_readings_id_seq; Type: SEQUENCE; Schema: public; Owner: saju
--

CREATE SEQUENCE public.saju_readings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.saju_readings_id_seq OWNER TO saju;

--
-- Name: saju_readings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: saju
--

ALTER SEQUENCE public.saju_readings_id_seq OWNED BY public.saju_readings.id;


--
-- Name: saju_readings id; Type: DEFAULT; Schema: public; Owner: saju
--

ALTER TABLE ONLY public.saju_readings ALTER COLUMN id SET DEFAULT nextval('public.saju_readings_id_seq'::regclass);


--
-- Name: saju_readings saju_readings_pkey; Type: CONSTRAINT; Schema: public; Owner: saju
--

ALTER TABLE ONLY public.saju_readings
    ADD CONSTRAINT saju_readings_pkey PRIMARY KEY (id);


--
-- Name: idx_saju_session; Type: INDEX; Schema: public; Owner: saju
--

CREATE INDEX idx_saju_session ON public.saju_readings USING btree (session_id);


--
-- PostgreSQL database dump complete
--

\unrestrict rhfBZYw6ItxYQoNC2bbqIIXESao9aPSq6j6KTrxaMRtQo4zCg63SRG5QOYHr06U

