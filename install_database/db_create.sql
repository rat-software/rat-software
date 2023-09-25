--
-- PostgreSQL database dump
--

-- Dumped from database version 11.14 (Debian 11.14-0+deb10u1)
-- Dumped by pg_dump version 14.1

-- Started on 2022-10-20 12:20:04 CEST

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

--
-- TOC entry 241 (class 1259 OID 133571)
-- Name: answer; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.answer (
    id integer NOT NULL,
    value text,
    participant integer,
    result integer,
    question integer,
    study integer,
    status integer,
    created_at timestamp(6) without time zone
);


--
-- TOC entry 240 (class 1259 OID 133569)
-- Name: answer_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.answer_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3383 (class 0 OID 0)
-- Dependencies: 240
-- Name: answer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.answer_id_seq OWNED BY public.answer.id;


--
-- TOC entry 271 (class 1259 OID 239534)
-- Name: classificationindicator; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.classificationindicator (
    id integer NOT NULL,
    indicator text,
    value text,
    class text,
    result integer,
    created_at timestamp without time zone
);


--
-- TOC entry 270 (class 1259 OID 239532)
-- Name: classificationindicator_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.classificationindicator_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3384 (class 0 OID 0)
-- Dependencies: 270
-- Name: classificationindicator_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.classificationindicator_id_seq OWNED BY public.classificationindicator.id;


--
-- TOC entry 269 (class 1259 OID 239522)
-- Name: classificationresult; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.classificationresult (
    id integer NOT NULL,
    class text,
    value text,
    result integer,
    created_at timestamp without time zone
);


--
-- TOC entry 268 (class 1259 OID 239520)
-- Name: classificationresult_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.classificationresult_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3385 (class 0 OID 0)
-- Dependencies: 268
-- Name: classificationresult_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.classificationresult_id_seq OWNED BY public.classificationresult.id;


--
-- TOC entry 243 (class 1259 OID 133600)
-- Name: content; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.content (
    id integer NOT NULL,
    result integer,
    value text
);


--
-- TOC entry 242 (class 1259 OID 133598)
-- Name: content_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.content_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3386 (class 0 OID 0)
-- Dependencies: 242
-- Name: content_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.content_id_seq OWNED BY public.content.id;


--
-- TOC entry 261 (class 1259 OID 199757)
-- Name: country; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.country (
    id integer NOT NULL,
    name text,
    code text,
    searchengine integer,
    language integer
);


--
-- TOC entry 260 (class 1259 OID 199755)
-- Name: country_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.country_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3387 (class 0 OID 0)
-- Dependencies: 260
-- Name: country_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.country_id_seq OWNED BY public.country.id;


--
-- TOC entry 264 (class 1259 OID 199790)
-- Name: country_monitoring; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.country_monitoring (
    country integer,
    monitoring integer
);


--
-- TOC entry 266 (class 1259 OID 199830)
-- Name: dummy_table; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dummy_table (
    id integer NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    name text,
    description text
);


--
-- TOC entry 265 (class 1259 OID 199828)
-- Name: dummy_table_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dummy_table_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3388 (class 0 OID 0)
-- Dependencies: 265
-- Name: dummy_table_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dummy_table_id_seq OWNED BY public.dummy_table.id;


--
-- TOC entry 214 (class 1259 OID 133286)
-- Name: evaluation; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.evaluation (
    id integer NOT NULL,
    source integer,
    comment text,
    status integer
);


--
-- TOC entry 213 (class 1259 OID 133284)
-- Name: evaluation_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.evaluation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3389 (class 0 OID 0)
-- Dependencies: 213
-- Name: evaluation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.evaluation_id_seq OWNED BY public.evaluation.id;


--
-- TOC entry 220 (class 1259 OID 133331)
-- Name: experiment; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.experiment (
    id integer NOT NULL,
    study integer
);


--
-- TOC entry 219 (class 1259 OID 133329)
-- Name: experiment_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.experiment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3390 (class 0 OID 0)
-- Dependencies: 219
-- Name: experiment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.experiment_id_seq OWNED BY public.experiment.id;


--
-- TOC entry 197 (class 1259 OID 133182)
-- Name: group; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."group" (
    id integer NOT NULL,
    name text,
    description text
);


--
-- TOC entry 196 (class 1259 OID 133180)
-- Name: group_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.group_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3391 (class 0 OID 0)
-- Dependencies: 196
-- Name: group_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.group_id_seq OWNED BY public."group".id;


--
-- TOC entry 225 (class 1259 OID 133384)
-- Name: incentive; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.incentive (
    id integer NOT NULL,
    study integer,
    participant integer
);


--
-- TOC entry 224 (class 1259 OID 133382)
-- Name: incentive_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.incentive_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3392 (class 0 OID 0)
-- Dependencies: 224
-- Name: incentive_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.incentive_id_seq OWNED BY public.incentive.id;


--
-- TOC entry 199 (class 1259 OID 133193)
-- Name: language; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.language (
    id integer NOT NULL,
    name text,
    code text,
    translate boolean DEFAULT false
);


--
-- TOC entry 198 (class 1259 OID 133191)
-- Name: language_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.language_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3393 (class 0 OID 0)
-- Dependencies: 198
-- Name: language_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.language_id_seq OWNED BY public.language.id;


--
-- TOC entry 221 (class 1259 OID 133343)
-- Name: language_study; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.language_study (
    language integer NOT NULL,
    study integer NOT NULL
);


--
-- TOC entry 201 (class 1259 OID 133204)
-- Name: logger; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.logger (
    id integer NOT NULL,
    clicked boolean,
    "limit" text
);


--
-- TOC entry 200 (class 1259 OID 133202)
-- Name: logger_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.logger_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3394 (class 0 OID 0)
-- Dependencies: 200
-- Name: logger_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.logger_id_seq OWNED BY public.logger.id;


--
-- TOC entry 228 (class 1259 OID 133419)
-- Name: logger_query; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.logger_query (
    logger integer NOT NULL,
    query integer NOT NULL
);


--
-- TOC entry 244 (class 1259 OID 133615)
-- Name: logger_result; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.logger_result (
    logger integer NOT NULL,
    result integer NOT NULL
);


--
-- TOC entry 235 (class 1259 OID 133507)
-- Name: logger_scraper; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.logger_scraper (
    logger integer NOT NULL,
    scraper integer NOT NULL
);


--
-- TOC entry 210 (class 1259 OID 133257)
-- Name: logger_searchengine; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.logger_searchengine (
    logger integer NOT NULL,
    searchengine integer NOT NULL
);


--
-- TOC entry 249 (class 1259 OID 133680)
-- Name: logger_serp; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.logger_serp (
    logger integer NOT NULL,
    serp integer NOT NULL
);


--
-- TOC entry 263 (class 1259 OID 199780)
-- Name: monitoring; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.monitoring (
    id integer NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    name text,
    description text,
    interval_mode integer,
    interval_frequency integer,
    result_count integer,
    resulttype integer
);


--
-- TOC entry 262 (class 1259 OID 199778)
-- Name: monitoring_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.monitoring_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3395 (class 0 OID 0)
-- Dependencies: 262
-- Name: monitoring_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.monitoring_id_seq OWNED BY public.monitoring.id;


--
-- TOC entry 232 (class 1259 OID 133466)
-- Name: option; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.option (
    id integer NOT NULL,
    value text,
    label text,
    "position" integer,
    question integer
);


--
-- TOC entry 231 (class 1259 OID 133464)
-- Name: option_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.option_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3396 (class 0 OID 0)
-- Dependencies: 231
-- Name: option_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.option_id_seq OWNED BY public.option.id;


--
-- TOC entry 223 (class 1259 OID 133361)
-- Name: participant; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.participant (
    id integer NOT NULL,
    "group" integer,
    name text,
    created_at timestamp(6) without time zone,
    updated_at timestamp(6) without time zone,
    password integer
);


--
-- TOC entry 222 (class 1259 OID 133359)
-- Name: participant_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.participant_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3397 (class 0 OID 0)
-- Dependencies: 222
-- Name: participant_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.participant_id_seq OWNED BY public.participant.id;


--
-- TOC entry 257 (class 1259 OID 199652)
-- Name: participant_study; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.participant_study (
    participant integer NOT NULL,
    study integer NOT NULL
);


--
-- TOC entry 227 (class 1259 OID 133404)
-- Name: query; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.query (
    id integer NOT NULL,
    query text,
    created_at timestamp without time zone,
    study integer,
    old_id integer,
    description text,
    "limit" integer,
    monitoring integer
);


--
-- TOC entry 226 (class 1259 OID 133402)
-- Name: query_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.query_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3398 (class 0 OID 0)
-- Dependencies: 226
-- Name: query_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.query_id_seq OWNED BY public.query.id;


--
-- TOC entry 230 (class 1259 OID 133437)
-- Name: question; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.question (
    id integer NOT NULL,
    study integer,
    title text,
    description text,
    question_type integer,
    question_template integer,
    "position" integer,
    "interval" integer
);


--
-- TOC entry 229 (class 1259 OID 133435)
-- Name: question_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.question_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3399 (class 0 OID 0)
-- Dependencies: 229
-- Name: question_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.question_id_seq OWNED BY public.question.id;


--
-- TOC entry 245 (class 1259 OID 133631)
-- Name: question_result; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.question_result (
    question integer NOT NULL,
    result integer NOT NULL
);


--
-- TOC entry 203 (class 1259 OID 133215)
-- Name: questiontemplate; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.questiontemplate (
    id integer NOT NULL,
    name text,
    description text
);


--
-- TOC entry 202 (class 1259 OID 133213)
-- Name: questiontemplate_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.questiontemplate_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3400 (class 0 OID 0)
-- Dependencies: 202
-- Name: questiontemplate_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.questiontemplate_id_seq OWNED BY public.questiontemplate.id;


--
-- TOC entry 205 (class 1259 OID 133226)
-- Name: questiontype; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.questiontype (
    id integer NOT NULL,
    name text,
    display text
);


--
-- TOC entry 204 (class 1259 OID 133224)
-- Name: questiontype_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.questiontype_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3401 (class 0 OID 0)
-- Dependencies: 204
-- Name: questiontype_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.questiontype_id_seq OWNED BY public.questiontype.id;


--
-- TOC entry 237 (class 1259 OID 133525)
-- Name: reporting; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.reporting (
    id integer NOT NULL,
    scraper integer,
    created_at timestamp without time zone,
    result_count integer,
    missing_count integer,
    duplicate_count integer,
    exit_condition text,
    duration integer,
    old_id integer
);


--
-- TOC entry 236 (class 1259 OID 133523)
-- Name: reporting_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.reporting_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3402 (class 0 OID 0)
-- Dependencies: 236
-- Name: reporting_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.reporting_id_seq OWNED BY public.reporting.id;


--
-- TOC entry 239 (class 1259 OID 133542)
-- Name: result; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.result (
    id integer NOT NULL,
    title text,
    description text,
    url text,
    "position" integer,
    created_at timestamp without time zone,
    main text,
    ip text,
    origin text,
    imported boolean,
    study integer,
    scraper integer,
    source integer,
    old_id integer,
    resulttype integer,
    monitoring integer,
    serp integer,
    query integer,
    final_url text
);


--
-- TOC entry 238 (class 1259 OID 133540)
-- Name: result_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.result_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3403 (class 0 OID 0)
-- Dependencies: 238
-- Name: result_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.result_id_seq OWNED BY public.result.id;


--
-- TOC entry 259 (class 1259 OID 199680)
-- Name: resulttype; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.resulttype (
    id integer NOT NULL,
    name text,
    display text
);


--
-- TOC entry 258 (class 1259 OID 199678)
-- Name: resulttype_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.resulttype_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3404 (class 0 OID 0)
-- Dependencies: 258
-- Name: resulttype_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.resulttype_id_seq OWNED BY public.resulttype.id;


--
-- TOC entry 207 (class 1259 OID 133237)
-- Name: role; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.role (
    id integer NOT NULL,
    name text,
    description text,
    permissions text,
    update_datetime timestamp(6) without time zone
);


--
-- TOC entry 206 (class 1259 OID 133235)
-- Name: role_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.role_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3405 (class 0 OID 0)
-- Dependencies: 206
-- Name: role_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.role_id_seq OWNED BY public.role.id;


--
-- TOC entry 234 (class 1259 OID 133483)
-- Name: scraper; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scraper (
    id integer NOT NULL,
    progress integer,
    "limit" integer,
    counter integer,
    error_code integer,
    created_at timestamp without time zone,
    query integer,
    searchengine integer,
    study integer,
    old_id integer,
    type integer
);


--
-- TOC entry 233 (class 1259 OID 133481)
-- Name: scraper_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.scraper_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3406 (class 0 OID 0)
-- Dependencies: 233
-- Name: scraper_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.scraper_id_seq OWNED BY public.scraper.id;


--
-- TOC entry 209 (class 1259 OID 133248)
-- Name: searchengine; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.searchengine (
    id integer NOT NULL,
    name text,
    config text,
    old_id integer
);


--
-- TOC entry 208 (class 1259 OID 133246)
-- Name: searchengine_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.searchengine_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3407 (class 0 OID 0)
-- Dependencies: 208
-- Name: searchengine_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.searchengine_id_seq OWNED BY public.searchengine.id;


--
-- TOC entry 246 (class 1259 OID 133647)
-- Name: searchengine_study; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.searchengine_study (
    searchengine integer NOT NULL,
    study integer NOT NULL
);


--
-- TOC entry 248 (class 1259 OID 133665)
-- Name: serp; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.serp (
    id integer NOT NULL,
    scraper integer,
    page integer,
    code bytea,
    img bytea,
    progress integer,
    created_at timestamp without time zone,
    old_id integer,
    monitoring integer,
    query integer
);


--
-- TOC entry 247 (class 1259 OID 133663)
-- Name: serp_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.serp_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3408 (class 0 OID 0)
-- Dependencies: 247
-- Name: serp_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.serp_id_seq OWNED BY public.serp.id;


--
-- TOC entry 212 (class 1259 OID 133275)
-- Name: source; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.source (
    id integer NOT NULL,
    code bytea,
    bin bytea,
    url text,
    progress integer,
    content_type text,
    error_code text,
    status_code integer,
    final_url text,
    created_at timestamp without time zone,
    result integer,
    job_server text
);


--
-- TOC entry 211 (class 1259 OID 133273)
-- Name: source_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.source_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3409 (class 0 OID 0)
-- Dependencies: 211
-- Name: source_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.source_id_seq OWNED BY public.source.id;


--
-- TOC entry 251 (class 1259 OID 133714)
-- Name: statistic; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.statistic (
    id integer NOT NULL,
    study integer,
    name text,
    value text
);


--
-- TOC entry 250 (class 1259 OID 133712)
-- Name: statistic_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.statistic_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3410 (class 0 OID 0)
-- Dependencies: 250
-- Name: statistic_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.statistic_id_seq OWNED BY public.statistic.id;


--
-- TOC entry 218 (class 1259 OID 133314)
-- Name: study; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.study (
    id integer NOT NULL,
    name text,
    description text,
    imported boolean,
    studytype integer,
    old_id integer,
    created_at timestamp(6) without time zone,
    updated_at timestamp(6) without time zone,
    resulttype integer,
    result_count integer,
    status integer
);


--
-- TOC entry 217 (class 1259 OID 133312)
-- Name: study_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.study_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3411 (class 0 OID 0)
-- Dependencies: 217
-- Name: study_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.study_id_seq OWNED BY public.study.id;


--
-- TOC entry 256 (class 1259 OID 133760)
-- Name: study_user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.study_user (
    study integer NOT NULL,
    "user" integer NOT NULL
);


--
-- TOC entry 216 (class 1259 OID 133303)
-- Name: studytype; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.studytype (
    id integer NOT NULL,
    name text,
    old_id integer
);


--
-- TOC entry 215 (class 1259 OID 133301)
-- Name: studytype_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.studytype_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3412 (class 0 OID 0)
-- Dependencies: 215
-- Name: studytype_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.studytype_id_seq OWNED BY public.studytype.id;


--
-- TOC entry 253 (class 1259 OID 133731)
-- Name: task; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.task (
    id integer NOT NULL,
    logger integer
);


--
-- TOC entry 252 (class 1259 OID 133729)
-- Name: task_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.task_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3413 (class 0 OID 0)
-- Dependencies: 252
-- Name: task_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.task_id_seq OWNED BY public.task.id;


--
-- TOC entry 255 (class 1259 OID 133745)
-- Name: user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."user" (
    id integer NOT NULL,
    email text,
    password text,
    last_login_at timestamp without time zone,
    current_login_at timestamp without time zone,
    current_login_ip text,
    login_count integer,
    active boolean,
    confirmed_at timestamp without time zone,
    last_login_ip text,
    fs_uniquifier text,
    tf_primary_method text,
    tf_totp_secret text,
    tf_phone_number text,
    create_datetime timestamp(6) without time zone,
    update_datetime timestamp(6) without time zone,
    username text,
    us_totp_secrets text,
    fs_webauthn_user_handle text,
    mf_recovery_codes text,
    us_phone_number text
);


--
-- TOC entry 254 (class 1259 OID 133743)
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3414 (class 0 OID 0)
-- Dependencies: 254
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_id_seq OWNED BY public."user".id;


--
-- TOC entry 267 (class 1259 OID 234173)
-- Name: user_role; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_role (
    "user" integer,
    role integer
);


--
-- TOC entry 3058 (class 2604 OID 133574)
-- Name: answer id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.answer ALTER COLUMN id SET DEFAULT nextval('public.answer_id_seq'::regclass);


--
-- TOC entry 3071 (class 2604 OID 239537)
-- Name: classificationindicator id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classificationindicator ALTER COLUMN id SET DEFAULT nextval('public.classificationindicator_id_seq'::regclass);


--
-- TOC entry 3070 (class 2604 OID 239525)
-- Name: classificationresult id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classificationresult ALTER COLUMN id SET DEFAULT nextval('public.classificationresult_id_seq'::regclass);


--
-- TOC entry 3059 (class 2604 OID 133603)
-- Name: content id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.content ALTER COLUMN id SET DEFAULT nextval('public.content_id_seq'::regclass);


--
-- TOC entry 3065 (class 2604 OID 199760)
-- Name: country id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.country ALTER COLUMN id SET DEFAULT nextval('public.country_id_seq'::regclass);


--
-- TOC entry 3068 (class 2604 OID 199833)
-- Name: dummy_table id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dummy_table ALTER COLUMN id SET DEFAULT nextval('public.dummy_table_id_seq'::regclass);


--
-- TOC entry 3046 (class 2604 OID 133289)
-- Name: evaluation id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluation ALTER COLUMN id SET DEFAULT nextval('public.evaluation_id_seq'::regclass);


--
-- TOC entry 3049 (class 2604 OID 133334)
-- Name: experiment id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.experiment ALTER COLUMN id SET DEFAULT nextval('public.experiment_id_seq'::regclass);


--
-- TOC entry 3037 (class 2604 OID 133185)
-- Name: group id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."group" ALTER COLUMN id SET DEFAULT nextval('public.group_id_seq'::regclass);


--
-- TOC entry 3051 (class 2604 OID 133387)
-- Name: incentive id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.incentive ALTER COLUMN id SET DEFAULT nextval('public.incentive_id_seq'::regclass);


--
-- TOC entry 3038 (class 2604 OID 133196)
-- Name: language id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.language ALTER COLUMN id SET DEFAULT nextval('public.language_id_seq'::regclass);


--
-- TOC entry 3040 (class 2604 OID 133207)
-- Name: logger id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger ALTER COLUMN id SET DEFAULT nextval('public.logger_id_seq'::regclass);


--
-- TOC entry 3066 (class 2604 OID 199783)
-- Name: monitoring id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.monitoring ALTER COLUMN id SET DEFAULT nextval('public.monitoring_id_seq'::regclass);


--
-- TOC entry 3054 (class 2604 OID 133469)
-- Name: option id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.option ALTER COLUMN id SET DEFAULT nextval('public.option_id_seq'::regclass);


--
-- TOC entry 3050 (class 2604 OID 133364)
-- Name: participant id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.participant ALTER COLUMN id SET DEFAULT nextval('public.participant_id_seq'::regclass);


--
-- TOC entry 3052 (class 2604 OID 133407)
-- Name: query id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.query ALTER COLUMN id SET DEFAULT nextval('public.query_id_seq'::regclass);


--
-- TOC entry 3053 (class 2604 OID 133440)
-- Name: question id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question ALTER COLUMN id SET DEFAULT nextval('public.question_id_seq'::regclass);


--
-- TOC entry 3041 (class 2604 OID 133218)
-- Name: questiontemplate id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questiontemplate ALTER COLUMN id SET DEFAULT nextval('public.questiontemplate_id_seq'::regclass);


--
-- TOC entry 3042 (class 2604 OID 133229)
-- Name: questiontype id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questiontype ALTER COLUMN id SET DEFAULT nextval('public.questiontype_id_seq'::regclass);


--
-- TOC entry 3056 (class 2604 OID 133528)
-- Name: reporting id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reporting ALTER COLUMN id SET DEFAULT nextval('public.reporting_id_seq'::regclass);


--
-- TOC entry 3057 (class 2604 OID 133545)
-- Name: result id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.result ALTER COLUMN id SET DEFAULT nextval('public.result_id_seq'::regclass);


--
-- TOC entry 3064 (class 2604 OID 199683)
-- Name: resulttype id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resulttype ALTER COLUMN id SET DEFAULT nextval('public.resulttype_id_seq'::regclass);


--
-- TOC entry 3043 (class 2604 OID 133240)
-- Name: role id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role ALTER COLUMN id SET DEFAULT nextval('public.role_id_seq'::regclass);


--
-- TOC entry 3055 (class 2604 OID 133486)
-- Name: scraper id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scraper ALTER COLUMN id SET DEFAULT nextval('public.scraper_id_seq'::regclass);


--
-- TOC entry 3044 (class 2604 OID 133251)
-- Name: searchengine id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.searchengine ALTER COLUMN id SET DEFAULT nextval('public.searchengine_id_seq'::regclass);


--
-- TOC entry 3060 (class 2604 OID 133668)
-- Name: serp id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.serp ALTER COLUMN id SET DEFAULT nextval('public.serp_id_seq'::regclass);


--
-- TOC entry 3045 (class 2604 OID 133278)
-- Name: source id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.source ALTER COLUMN id SET DEFAULT nextval('public.source_id_seq'::regclass);


--
-- TOC entry 3061 (class 2604 OID 133717)
-- Name: statistic id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.statistic ALTER COLUMN id SET DEFAULT nextval('public.statistic_id_seq'::regclass);


--
-- TOC entry 3048 (class 2604 OID 133317)
-- Name: study id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study ALTER COLUMN id SET DEFAULT nextval('public.study_id_seq'::regclass);


--
-- TOC entry 3047 (class 2604 OID 133306)
-- Name: studytype id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.studytype ALTER COLUMN id SET DEFAULT nextval('public.studytype_id_seq'::regclass);


--
-- TOC entry 3062 (class 2604 OID 133734)
-- Name: task id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task ALTER COLUMN id SET DEFAULT nextval('public.task_id_seq'::regclass);


--
-- TOC entry 3063 (class 2604 OID 133748)
-- Name: user id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user" ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);


--
-- TOC entry 3145 (class 2606 OID 133579)
-- Name: answer answer_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.answer
    ADD CONSTRAINT answer_pkey PRIMARY KEY (id);


--
-- TOC entry 3195 (class 2606 OID 239542)
-- Name: classificationindicator classificationindicator_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classificationindicator
    ADD CONSTRAINT classificationindicator_pkey PRIMARY KEY (id);


--
-- TOC entry 3192 (class 2606 OID 239530)
-- Name: classificationresult classificationresult_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classificationresult
    ADD CONSTRAINT classificationresult_pkey PRIMARY KEY (id);


--
-- TOC entry 3151 (class 2606 OID 133608)
-- Name: content content_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.content
    ADD CONSTRAINT content_pkey PRIMARY KEY (id);


--
-- TOC entry 3185 (class 2606 OID 199766)
-- Name: country country_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.country
    ADD CONSTRAINT country_pkey PRIMARY KEY (id);


--
-- TOC entry 3189 (class 2606 OID 199839)
-- Name: dummy_table dummy_table_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dummy_table
    ADD CONSTRAINT dummy_table_pkey PRIMARY KEY (id);


--
-- TOC entry 3092 (class 2606 OID 133294)
-- Name: evaluation evaluation_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluation
    ADD CONSTRAINT evaluation_pkey PRIMARY KEY (id);


--
-- TOC entry 3100 (class 2606 OID 133336)
-- Name: experiment experiment_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.experiment
    ADD CONSTRAINT experiment_pkey PRIMARY KEY (id);


--
-- TOC entry 3073 (class 2606 OID 133190)
-- Name: group group_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."group"
    ADD CONSTRAINT group_pkey PRIMARY KEY (id);


--
-- TOC entry 3111 (class 2606 OID 133389)
-- Name: incentive incentive_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.incentive
    ADD CONSTRAINT incentive_pkey PRIMARY KEY (id);


--
-- TOC entry 3075 (class 2606 OID 133201)
-- Name: language language_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.language
    ADD CONSTRAINT language_pkey PRIMARY KEY (id);


--
-- TOC entry 3104 (class 2606 OID 133347)
-- Name: language_study language_study_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.language_study
    ADD CONSTRAINT language_study_pkey PRIMARY KEY (language, study);


--
-- TOC entry 3077 (class 2606 OID 133212)
-- Name: logger logger_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger
    ADD CONSTRAINT logger_pkey PRIMARY KEY (id);


--
-- TOC entry 3117 (class 2606 OID 133423)
-- Name: logger_query logger_query_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_query
    ADD CONSTRAINT logger_query_pkey PRIMARY KEY (logger, query);


--
-- TOC entry 3155 (class 2606 OID 133619)
-- Name: logger_result logger_result_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_result
    ADD CONSTRAINT logger_result_pkey PRIMARY KEY (logger, result);


--
-- TOC entry 3133 (class 2606 OID 133511)
-- Name: logger_scraper logger_scraper_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_scraper
    ADD CONSTRAINT logger_scraper_pkey PRIMARY KEY (logger, scraper);


--
-- TOC entry 3088 (class 2606 OID 133261)
-- Name: logger_searchengine logger_searchengine_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_searchengine
    ADD CONSTRAINT logger_searchengine_pkey PRIMARY KEY (logger, searchengine);


--
-- TOC entry 3167 (class 2606 OID 133684)
-- Name: logger_serp logger_serp_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_serp
    ADD CONSTRAINT logger_serp_pkey PRIMARY KEY (logger, serp);


--
-- TOC entry 3187 (class 2606 OID 199789)
-- Name: monitoring monitoring_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.monitoring
    ADD CONSTRAINT monitoring_pkey PRIMARY KEY (id);


--
-- TOC entry 3125 (class 2606 OID 133474)
-- Name: option option_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.option
    ADD CONSTRAINT option_pkey PRIMARY KEY (id);


--
-- TOC entry 3107 (class 2606 OID 133369)
-- Name: participant participant_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.participant
    ADD CONSTRAINT participant_pkey PRIMARY KEY (id);


--
-- TOC entry 3181 (class 2606 OID 199656)
-- Name: participant_study participant_study_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.participant_study
    ADD CONSTRAINT participant_study_pkey PRIMARY KEY (participant, study);


--
-- TOC entry 3114 (class 2606 OID 133412)
-- Name: query query_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.query
    ADD CONSTRAINT query_pkey PRIMARY KEY (id);


--
-- TOC entry 3122 (class 2606 OID 133445)
-- Name: question question_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question
    ADD CONSTRAINT question_pkey PRIMARY KEY (id);


--
-- TOC entry 3158 (class 2606 OID 133635)
-- Name: question_result question_result_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_result
    ADD CONSTRAINT question_result_pkey PRIMARY KEY (question, result);


--
-- TOC entry 3079 (class 2606 OID 133223)
-- Name: questiontemplate questiontemplate_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questiontemplate
    ADD CONSTRAINT questiontemplate_pkey PRIMARY KEY (id);


--
-- TOC entry 3081 (class 2606 OID 133234)
-- Name: questiontype questiontype_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questiontype
    ADD CONSTRAINT questiontype_pkey PRIMARY KEY (id);


--
-- TOC entry 3136 (class 2606 OID 133533)
-- Name: reporting reporting_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reporting
    ADD CONSTRAINT reporting_pkey PRIMARY KEY (id);


--
-- TOC entry 3143 (class 2606 OID 133550)
-- Name: result result_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.result
    ADD CONSTRAINT result_pkey PRIMARY KEY (id);


--
-- TOC entry 3183 (class 2606 OID 199688)
-- Name: resulttype resulttype_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resulttype
    ADD CONSTRAINT resulttype_pkey PRIMARY KEY (id);


--
-- TOC entry 3083 (class 2606 OID 133245)
-- Name: role role_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role
    ADD CONSTRAINT role_pkey PRIMARY KEY (id);


--
-- TOC entry 3130 (class 2606 OID 133488)
-- Name: scraper scraper_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scraper
    ADD CONSTRAINT scraper_pkey PRIMARY KEY (id);


--
-- TOC entry 3085 (class 2606 OID 133256)
-- Name: searchengine searchengine_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.searchengine
    ADD CONSTRAINT searchengine_pkey PRIMARY KEY (id);


--
-- TOC entry 3161 (class 2606 OID 133651)
-- Name: searchengine_study searchengine_study_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.searchengine_study
    ADD CONSTRAINT searchengine_study_pkey PRIMARY KEY (searchengine, study);


--
-- TOC entry 3164 (class 2606 OID 133673)
-- Name: serp serp_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.serp
    ADD CONSTRAINT serp_pkey PRIMARY KEY (id);


--
-- TOC entry 3090 (class 2606 OID 133283)
-- Name: source source_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.source
    ADD CONSTRAINT source_pkey PRIMARY KEY (id);


--
-- TOC entry 3170 (class 2606 OID 133722)
-- Name: statistic statistic_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.statistic
    ADD CONSTRAINT statistic_pkey PRIMARY KEY (id);


--
-- TOC entry 3098 (class 2606 OID 133322)
-- Name: study study_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study
    ADD CONSTRAINT study_pkey PRIMARY KEY (id);


--
-- TOC entry 3178 (class 2606 OID 133764)
-- Name: study_user study_user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_user
    ADD CONSTRAINT study_user_pkey PRIMARY KEY (study, "user");


--
-- TOC entry 3095 (class 2606 OID 133311)
-- Name: studytype studytype_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.studytype
    ADD CONSTRAINT studytype_pkey PRIMARY KEY (id);


--
-- TOC entry 3173 (class 2606 OID 133736)
-- Name: task task_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task
    ADD CONSTRAINT task_pkey PRIMARY KEY (id);


--
-- TOC entry 3175 (class 2606 OID 133753)
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- TOC entry 3193 (class 1259 OID 239543)
-- Name: classificationindicator_indicator_class_result_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX classificationindicator_indicator_class_result_idx ON public.classificationindicator USING btree (indicator, class, result);


--
-- TOC entry 3190 (class 1259 OID 239544)
-- Name: classificationresult_class_value_result_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX classificationresult_class_value_result_idx ON public.classificationresult USING btree (class, value, result);


--
-- TOC entry 3137 (class 1259 OID 232963)
-- Name: fki_fk_result__serp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX fki_fk_result__serp ON public.result USING btree (serp);


--
-- TOC entry 3138 (class 1259 OID 232957)
-- Name: fki_r; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX fki_r ON public.result USING btree (serp);


--
-- TOC entry 3146 (class 1259 OID 133580)
-- Name: idx_answer__participant; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_answer__participant ON public.answer USING btree (participant);


--
-- TOC entry 3147 (class 1259 OID 133581)
-- Name: idx_answer__question; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_answer__question ON public.answer USING btree (question);


--
-- TOC entry 3148 (class 1259 OID 133582)
-- Name: idx_answer__result; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_answer__result ON public.answer USING btree (result);


--
-- TOC entry 3149 (class 1259 OID 199651)
-- Name: idx_answer__study; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_answer__study ON public.answer USING btree (study);


--
-- TOC entry 3152 (class 1259 OID 133609)
-- Name: idx_content__result; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_content__result ON public.content USING btree (result);


--
-- TOC entry 3093 (class 1259 OID 133295)
-- Name: idx_evaluation__source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_evaluation__source ON public.evaluation USING btree (source);


--
-- TOC entry 3101 (class 1259 OID 133337)
-- Name: idx_experiment__study; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_experiment__study ON public.experiment USING btree (study);


--
-- TOC entry 3108 (class 1259 OID 133390)
-- Name: idx_incentive__participant; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_incentive__participant ON public.incentive USING btree (participant);


--
-- TOC entry 3109 (class 1259 OID 133391)
-- Name: idx_incentive__study; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_incentive__study ON public.incentive USING btree (study);


--
-- TOC entry 3102 (class 1259 OID 133348)
-- Name: idx_language_study; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_language_study ON public.language_study USING btree (study);


--
-- TOC entry 3115 (class 1259 OID 133424)
-- Name: idx_logger_query; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_logger_query ON public.logger_query USING btree (query);


--
-- TOC entry 3153 (class 1259 OID 133620)
-- Name: idx_logger_result; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_logger_result ON public.logger_result USING btree (result);


--
-- TOC entry 3131 (class 1259 OID 133512)
-- Name: idx_logger_scraper; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_logger_scraper ON public.logger_scraper USING btree (scraper);


--
-- TOC entry 3086 (class 1259 OID 133262)
-- Name: idx_logger_searchengine; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_logger_searchengine ON public.logger_searchengine USING btree (searchengine);


--
-- TOC entry 3165 (class 1259 OID 133685)
-- Name: idx_logger_serp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_logger_serp ON public.logger_serp USING btree (serp);


--
-- TOC entry 3123 (class 1259 OID 133475)
-- Name: idx_option__question; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_option__question ON public.option USING btree (question);


--
-- TOC entry 3105 (class 1259 OID 133370)
-- Name: idx_participant__group; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_participant__group ON public.participant USING btree ("group");


--
-- TOC entry 3179 (class 1259 OID 199657)
-- Name: idx_participant_study; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_participant_study ON public.participant_study USING btree (study);


--
-- TOC entry 3112 (class 1259 OID 133413)
-- Name: idx_query__study; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_query__study ON public.query USING btree (study);


--
-- TOC entry 3118 (class 1259 OID 133446)
-- Name: idx_question__question_template; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_question__question_template ON public.question USING btree (question_template);


--
-- TOC entry 3119 (class 1259 OID 133447)
-- Name: idx_question__question_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_question__question_type ON public.question USING btree (question_type);


--
-- TOC entry 3120 (class 1259 OID 133448)
-- Name: idx_question__study; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_question__study ON public.question USING btree (study);


--
-- TOC entry 3156 (class 1259 OID 133636)
-- Name: idx_question_result; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_question_result ON public.question_result USING btree (result);


--
-- TOC entry 3134 (class 1259 OID 133534)
-- Name: idx_reporting__scraper; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reporting__scraper ON public.reporting USING btree (scraper);


--
-- TOC entry 3139 (class 1259 OID 133551)
-- Name: idx_result__scraper; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_result__scraper ON public.result USING btree (scraper);


--
-- TOC entry 3140 (class 1259 OID 133552)
-- Name: idx_result__source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_result__source ON public.result USING btree (source);


--
-- TOC entry 3141 (class 1259 OID 133553)
-- Name: idx_result__study; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_result__study ON public.result USING btree (study);


--
-- TOC entry 3126 (class 1259 OID 133489)
-- Name: idx_scraper__query; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scraper__query ON public.scraper USING btree (query);


--
-- TOC entry 3127 (class 1259 OID 133490)
-- Name: idx_scraper__search_engine; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scraper__search_engine ON public.scraper USING btree (searchengine);


--
-- TOC entry 3128 (class 1259 OID 133491)
-- Name: idx_scraper__study; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scraper__study ON public.scraper USING btree (study);


--
-- TOC entry 3159 (class 1259 OID 133652)
-- Name: idx_searchengine_study; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_searchengine_study ON public.searchengine_study USING btree (study);


--
-- TOC entry 3162 (class 1259 OID 133674)
-- Name: idx_serp__scraper; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_serp__scraper ON public.serp USING btree (scraper);


--
-- TOC entry 3168 (class 1259 OID 133723)
-- Name: idx_statistic__study; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_statistic__study ON public.statistic USING btree (study);


--
-- TOC entry 3096 (class 1259 OID 133323)
-- Name: idx_study__study_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_study__study_type ON public.study USING btree (studytype);


--
-- TOC entry 3176 (class 1259 OID 133765)
-- Name: idx_study_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_study_user ON public.study_user USING btree ("user");


--
-- TOC entry 3171 (class 1259 OID 133737)
-- Name: idx_task__logger; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_task__logger ON public.task USING btree (logger);


--
-- TOC entry 3256 (class 2606 OID 281983)
-- Name: classificationresult classificationresult_relation_1; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classificationresult
    ADD CONSTRAINT classificationresult_relation_1 FOREIGN KEY (result) REFERENCES public.result(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- TOC entry 3227 (class 2606 OID 133583)
-- Name: answer fk_answer__participant; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.answer
    ADD CONSTRAINT fk_answer__participant FOREIGN KEY (participant) REFERENCES public.participant(id) ON DELETE SET NULL;


--
-- TOC entry 3228 (class 2606 OID 133588)
-- Name: answer fk_answer__question; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.answer
    ADD CONSTRAINT fk_answer__question FOREIGN KEY (question) REFERENCES public.question(id) ON DELETE SET NULL;


--
-- TOC entry 3229 (class 2606 OID 133593)
-- Name: answer fk_answer__result; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.answer
    ADD CONSTRAINT fk_answer__result FOREIGN KEY (result) REFERENCES public.result(id) ON DELETE SET NULL;


--
-- TOC entry 3230 (class 2606 OID 199658)
-- Name: answer fk_answer__study; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.answer
    ADD CONSTRAINT fk_answer__study FOREIGN KEY (study) REFERENCES public.study(id);


--
-- TOC entry 3231 (class 2606 OID 133610)
-- Name: content fk_content__result; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.content
    ADD CONSTRAINT fk_content__result FOREIGN KEY (result) REFERENCES public.result(id) ON DELETE SET NULL;


--
-- TOC entry 3249 (class 2606 OID 199768)
-- Name: country fk_country__language; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.country
    ADD CONSTRAINT fk_country__language FOREIGN KEY (language) REFERENCES public.language(id);


--
-- TOC entry 3250 (class 2606 OID 199773)
-- Name: country fk_country__searchengine; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.country
    ADD CONSTRAINT fk_country__searchengine FOREIGN KEY (searchengine) REFERENCES public.searchengine(id);


--
-- TOC entry 3252 (class 2606 OID 199793)
-- Name: country_monitoring fk_country_monitoring__country; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.country_monitoring
    ADD CONSTRAINT fk_country_monitoring__country FOREIGN KEY (country) REFERENCES public.country(id);


--
-- TOC entry 3253 (class 2606 OID 199798)
-- Name: country_monitoring fk_country_monitoring__monitoring; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.country_monitoring
    ADD CONSTRAINT fk_country_monitoring__monitoring FOREIGN KEY (monitoring) REFERENCES public.monitoring(id);


--
-- TOC entry 3198 (class 2606 OID 133296)
-- Name: evaluation fk_evaluation__source; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluation
    ADD CONSTRAINT fk_evaluation__source FOREIGN KEY (source) REFERENCES public.source(id) ON DELETE SET NULL;


--
-- TOC entry 3201 (class 2606 OID 133338)
-- Name: experiment fk_experiment__study; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.experiment
    ADD CONSTRAINT fk_experiment__study FOREIGN KEY (study) REFERENCES public.study(id) ON DELETE SET NULL;


--
-- TOC entry 3205 (class 2606 OID 133392)
-- Name: incentive fk_incentive__participant; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.incentive
    ADD CONSTRAINT fk_incentive__participant FOREIGN KEY (participant) REFERENCES public.participant(id) ON DELETE SET NULL;


--
-- TOC entry 3206 (class 2606 OID 133397)
-- Name: incentive fk_incentive__study; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.incentive
    ADD CONSTRAINT fk_incentive__study FOREIGN KEY (study) REFERENCES public.study(id) ON DELETE SET NULL;


--
-- TOC entry 3202 (class 2606 OID 133349)
-- Name: language_study fk_language_study__language; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.language_study
    ADD CONSTRAINT fk_language_study__language FOREIGN KEY (language) REFERENCES public.language(id);


--
-- TOC entry 3203 (class 2606 OID 133354)
-- Name: language_study fk_language_study__study; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.language_study
    ADD CONSTRAINT fk_language_study__study FOREIGN KEY (study) REFERENCES public.study(id);


--
-- TOC entry 3209 (class 2606 OID 133425)
-- Name: logger_query fk_logger_query__logger; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_query
    ADD CONSTRAINT fk_logger_query__logger FOREIGN KEY (logger) REFERENCES public.logger(id);


--
-- TOC entry 3210 (class 2606 OID 133430)
-- Name: logger_query fk_logger_query__query; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_query
    ADD CONSTRAINT fk_logger_query__query FOREIGN KEY (query) REFERENCES public.query(id);


--
-- TOC entry 3232 (class 2606 OID 133621)
-- Name: logger_result fk_logger_result__logger; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_result
    ADD CONSTRAINT fk_logger_result__logger FOREIGN KEY (logger) REFERENCES public.logger(id);


--
-- TOC entry 3233 (class 2606 OID 133626)
-- Name: logger_result fk_logger_result__result; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_result
    ADD CONSTRAINT fk_logger_result__result FOREIGN KEY (result) REFERENCES public.result(id);


--
-- TOC entry 3218 (class 2606 OID 133513)
-- Name: logger_scraper fk_logger_scraper__logger; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_scraper
    ADD CONSTRAINT fk_logger_scraper__logger FOREIGN KEY (logger) REFERENCES public.logger(id);


--
-- TOC entry 3219 (class 2606 OID 133518)
-- Name: logger_scraper fk_logger_scraper__scraper; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_scraper
    ADD CONSTRAINT fk_logger_scraper__scraper FOREIGN KEY (scraper) REFERENCES public.scraper(id);


--
-- TOC entry 3196 (class 2606 OID 133263)
-- Name: logger_searchengine fk_logger_searchengine__logger; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_searchengine
    ADD CONSTRAINT fk_logger_searchengine__logger FOREIGN KEY (logger) REFERENCES public.logger(id);


--
-- TOC entry 3197 (class 2606 OID 133268)
-- Name: logger_searchengine fk_logger_searchengine__searchengine; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_searchengine
    ADD CONSTRAINT fk_logger_searchengine__searchengine FOREIGN KEY (searchengine) REFERENCES public.searchengine(id);


--
-- TOC entry 3241 (class 2606 OID 133686)
-- Name: logger_serp fk_logger_serp__logger; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_serp
    ADD CONSTRAINT fk_logger_serp__logger FOREIGN KEY (logger) REFERENCES public.logger(id);


--
-- TOC entry 3242 (class 2606 OID 133691)
-- Name: logger_serp fk_logger_serp__serp; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_serp
    ADD CONSTRAINT fk_logger_serp__serp FOREIGN KEY (serp) REFERENCES public.serp(id);


--
-- TOC entry 3251 (class 2606 OID 199813)
-- Name: monitoring fk_monitoring__resulttype; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.monitoring
    ADD CONSTRAINT fk_monitoring__resulttype FOREIGN KEY (resulttype) REFERENCES public.resulttype(id) ON DELETE SET NULL;


--
-- TOC entry 3214 (class 2606 OID 133476)
-- Name: option fk_option__question; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.option
    ADD CONSTRAINT fk_option__question FOREIGN KEY (question) REFERENCES public.question(id) ON DELETE SET NULL;


--
-- TOC entry 3204 (class 2606 OID 133372)
-- Name: participant fk_participant__group; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.participant
    ADD CONSTRAINT fk_participant__group FOREIGN KEY ("group") REFERENCES public."group"(id) ON DELETE SET NULL;


--
-- TOC entry 3247 (class 2606 OID 199663)
-- Name: participant_study fk_participant_study__participant; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.participant_study
    ADD CONSTRAINT fk_participant_study__participant FOREIGN KEY (participant) REFERENCES public.participant(id);


--
-- TOC entry 3248 (class 2606 OID 199668)
-- Name: participant_study fk_participant_study__study; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.participant_study
    ADD CONSTRAINT fk_participant_study__study FOREIGN KEY (study) REFERENCES public.study(id);


--
-- TOC entry 3208 (class 2606 OID 199803)
-- Name: query fk_query__monitoring; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.query
    ADD CONSTRAINT fk_query__monitoring FOREIGN KEY (monitoring) REFERENCES public.monitoring(id) ON DELETE SET NULL;


--
-- TOC entry 3207 (class 2606 OID 133414)
-- Name: query fk_query__study; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.query
    ADD CONSTRAINT fk_query__study FOREIGN KEY (study) REFERENCES public.study(id) ON DELETE SET NULL;


--
-- TOC entry 3211 (class 2606 OID 133449)
-- Name: question fk_question__question_template; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question
    ADD CONSTRAINT fk_question__question_template FOREIGN KEY (question_template) REFERENCES public.questiontemplate(id) ON DELETE SET NULL;


--
-- TOC entry 3212 (class 2606 OID 133454)
-- Name: question fk_question__question_type; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question
    ADD CONSTRAINT fk_question__question_type FOREIGN KEY (question_type) REFERENCES public.questiontype(id) ON DELETE SET NULL;


--
-- TOC entry 3213 (class 2606 OID 133459)
-- Name: question fk_question__study; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question
    ADD CONSTRAINT fk_question__study FOREIGN KEY (study) REFERENCES public.study(id) ON DELETE SET NULL;


--
-- TOC entry 3234 (class 2606 OID 133637)
-- Name: question_result fk_question_result__question; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_result
    ADD CONSTRAINT fk_question_result__question FOREIGN KEY (question) REFERENCES public.question(id);


--
-- TOC entry 3235 (class 2606 OID 133642)
-- Name: question_result fk_question_result__result; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_result
    ADD CONSTRAINT fk_question_result__result FOREIGN KEY (result) REFERENCES public.result(id);


--
-- TOC entry 3220 (class 2606 OID 133535)
-- Name: reporting fk_reporting__scraper; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reporting
    ADD CONSTRAINT fk_reporting__scraper FOREIGN KEY (scraper) REFERENCES public.scraper(id) ON DELETE SET NULL;


--
-- TOC entry 3223 (class 2606 OID 199818)
-- Name: result fk_result__monitoring; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.result
    ADD CONSTRAINT fk_result__monitoring FOREIGN KEY (monitoring) REFERENCES public.monitoring(id);


--
-- TOC entry 3224 (class 2606 OID 199890)
-- Name: result fk_result__query; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.result
    ADD CONSTRAINT fk_result__query FOREIGN KEY (query) REFERENCES public.query(id) ON DELETE SET NULL;


--
-- TOC entry 3225 (class 2606 OID 232958)
-- Name: result fk_result__serp; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.result
    ADD CONSTRAINT fk_result__serp FOREIGN KEY (serp) REFERENCES public.serp(id) ON DELETE SET NULL;


--
-- TOC entry 3221 (class 2606 OID 133564)
-- Name: result fk_result__study; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.result
    ADD CONSTRAINT fk_result__study FOREIGN KEY (study) REFERENCES public.study(id) ON DELETE SET NULL;


--
-- TOC entry 3222 (class 2606 OID 199689)
-- Name: result fk_result_resulttype; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.result
    ADD CONSTRAINT fk_result_resulttype FOREIGN KEY (resulttype) REFERENCES public.resulttype(id);


--
-- TOC entry 3226 (class 2606 OID 233723)
-- Name: result fk_result_scraper; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.result
    ADD CONSTRAINT fk_result_scraper FOREIGN KEY (scraper) REFERENCES public.scraper(id) ON DELETE SET NULL;


--
-- TOC entry 3215 (class 2606 OID 133492)
-- Name: scraper fk_scraper__query; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scraper
    ADD CONSTRAINT fk_scraper__query FOREIGN KEY (query) REFERENCES public.query(id) ON DELETE SET NULL;


--
-- TOC entry 3216 (class 2606 OID 133497)
-- Name: scraper fk_scraper__search_engine; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scraper
    ADD CONSTRAINT fk_scraper__search_engine FOREIGN KEY (searchengine) REFERENCES public.searchengine(id) ON DELETE SET NULL;


--
-- TOC entry 3217 (class 2606 OID 133502)
-- Name: scraper fk_scraper__study; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scraper
    ADD CONSTRAINT fk_scraper__study FOREIGN KEY (study) REFERENCES public.study(id) ON DELETE SET NULL;


--
-- TOC entry 3236 (class 2606 OID 133653)
-- Name: searchengine_study fk_searchengine_study__searchengine; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.searchengine_study
    ADD CONSTRAINT fk_searchengine_study__searchengine FOREIGN KEY (searchengine) REFERENCES public.searchengine(id);


--
-- TOC entry 3237 (class 2606 OID 133658)
-- Name: searchengine_study fk_searchengine_study__study; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.searchengine_study
    ADD CONSTRAINT fk_searchengine_study__study FOREIGN KEY (study) REFERENCES public.study(id);


--
-- TOC entry 3239 (class 2606 OID 199823)
-- Name: serp fk_serp__monitoring; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.serp
    ADD CONSTRAINT fk_serp__monitoring FOREIGN KEY (monitoring) REFERENCES public.monitoring(id) ON DELETE SET NULL;


--
-- TOC entry 3240 (class 2606 OID 199870)
-- Name: serp fk_serp__query; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.serp
    ADD CONSTRAINT fk_serp__query FOREIGN KEY (query) REFERENCES public.query(id) ON DELETE SET NULL;


--
-- TOC entry 3238 (class 2606 OID 133675)
-- Name: serp fk_serp__scraper; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.serp
    ADD CONSTRAINT fk_serp__scraper FOREIGN KEY (scraper) REFERENCES public.scraper(id) ON DELETE SET NULL;


--
-- TOC entry 3243 (class 2606 OID 133724)
-- Name: statistic fk_statistic__study; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.statistic
    ADD CONSTRAINT fk_statistic__study FOREIGN KEY (study) REFERENCES public.study(id) ON DELETE SET NULL;


--
-- TOC entry 3200 (class 2606 OID 234146)
-- Name: study fk_study__result_type; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study
    ADD CONSTRAINT fk_study__result_type FOREIGN KEY (resulttype) REFERENCES public.resulttype(id) ON DELETE SET NULL;


--
-- TOC entry 3199 (class 2606 OID 133324)
-- Name: study fk_study__study_type; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study
    ADD CONSTRAINT fk_study__study_type FOREIGN KEY (studytype) REFERENCES public.studytype(id) ON DELETE SET NULL;


--
-- TOC entry 3245 (class 2606 OID 133766)
-- Name: study_user fk_study_user__study; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_user
    ADD CONSTRAINT fk_study_user__study FOREIGN KEY (study) REFERENCES public.study(id);


--
-- TOC entry 3246 (class 2606 OID 133771)
-- Name: study_user fk_study_user__user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_user
    ADD CONSTRAINT fk_study_user__user FOREIGN KEY ("user") REFERENCES public."user"(id);


--
-- TOC entry 3244 (class 2606 OID 133738)
-- Name: task fk_task__logger; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task
    ADD CONSTRAINT fk_task__logger FOREIGN KEY (logger) REFERENCES public.logger(id) ON DELETE SET NULL;


--
-- TOC entry 3254 (class 2606 OID 234176)
-- Name: user_role user_role_relation_1; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_role
    ADD CONSTRAINT user_role_relation_1 FOREIGN KEY ("user") REFERENCES public."user"(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- TOC entry 3255 (class 2606 OID 234181)
-- Name: user_role user_role_relation_2; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_role
    ADD CONSTRAINT user_role_relation_2 FOREIGN KEY (role) REFERENCES public.role(id) ON UPDATE CASCADE ON DELETE CASCADE;


-- Completed on 2022-10-20 12:20:17 CEST

--
-- PostgreSQL database dump complete
--

