--
-- PostgreSQL database dump
--

-- Dumped from database version 11.20 (Debian 11.20-0+deb10u1)
-- Dumped by pg_dump version 14.2

-- Started on 2024-08-06 11:17:54

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

--
-- TOC entry 3579 (class 1262 OID 676941)
-- Name: rat-install; Type: DATABASE; Schema: -; Owner: -
--

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

--
-- TOC entry 196 (class 1259 OID 676942)
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- TOC entry 197 (class 1259 OID 676945)
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
    created_at timestamp(6) without time zone,
    source_status_code integer
);


--
-- TOC entry 198 (class 1259 OID 676951)
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
-- TOC entry 3580 (class 0 OID 0)
-- Dependencies: 198
-- Name: answer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.answer_id_seq OWNED BY public.answer.id;


--
-- TOC entry 199 (class 1259 OID 676953)
-- Name: classifier; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.classifier (
    id integer NOT NULL,
    name text NOT NULL,
    display_name character varying(255)
);


--
-- TOC entry 200 (class 1259 OID 676959)
-- Name: classifier_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.classifier_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3581 (class 0 OID 0)
-- Dependencies: 200
-- Name: classifier_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.classifier_id_seq OWNED BY public.classifier.id;


--
-- TOC entry 201 (class 1259 OID 676961)
-- Name: classifier_indicator; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.classifier_indicator (
    id integer NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    indicator text,
    value text,
    result integer NOT NULL,
    classifier integer NOT NULL,
    job_server text
);


--
-- TOC entry 202 (class 1259 OID 676968)
-- Name: classifier_indicator_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.classifier_indicator_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3582 (class 0 OID 0)
-- Dependencies: 202
-- Name: classifier_indicator_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.classifier_indicator_id_seq OWNED BY public.classifier_indicator.id;


--
-- TOC entry 203 (class 1259 OID 676970)
-- Name: classifier_result; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.classifier_result (
    id integer NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    value text,
    result integer,
    classifier integer,
    job_server text
);


--
-- TOC entry 204 (class 1259 OID 676977)
-- Name: classifier_result_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.classifier_result_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3583 (class 0 OID 0)
-- Dependencies: 204
-- Name: classifier_result_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.classifier_result_id_seq OWNED BY public.classifier_result.id;


--
-- TOC entry 205 (class 1259 OID 676979)
-- Name: classifier_study_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.classifier_study_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 206 (class 1259 OID 676981)
-- Name: classifier_study; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.classifier_study (
    id integer DEFAULT nextval('public.classifier_study_id_seq'::regclass) NOT NULL,
    classifier integer,
    study integer
);


--
-- TOC entry 207 (class 1259 OID 676985)
-- Name: content; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.content (
    id integer NOT NULL,
    result integer,
    value text
);


--
-- TOC entry 208 (class 1259 OID 676991)
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
-- TOC entry 3584 (class 0 OID 0)
-- Dependencies: 208
-- Name: content_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.content_id_seq OWNED BY public.content.id;


--
-- TOC entry 209 (class 1259 OID 676993)
-- Name: country; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.country (
    id integer NOT NULL,
    name text,
    code text,
    language integer
);


--
-- TOC entry 210 (class 1259 OID 676999)
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
-- TOC entry 3585 (class 0 OID 0)
-- Dependencies: 210
-- Name: country_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.country_id_seq OWNED BY public.country.id;


--
-- TOC entry 211 (class 1259 OID 677001)
-- Name: country_monitoring; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.country_monitoring (
    country integer,
    monitoring integer
);


--
-- TOC entry 212 (class 1259 OID 677004)
-- Name: dummy_table; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dummy_table (
    id integer NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    name text,
    description text
);


--
-- TOC entry 213 (class 1259 OID 677011)
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
-- TOC entry 3586 (class 0 OID 0)
-- Dependencies: 213
-- Name: dummy_table_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dummy_table_id_seq OWNED BY public.dummy_table.id;


--
-- TOC entry 214 (class 1259 OID 677013)
-- Name: evaluation; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.evaluation (
    id integer NOT NULL,
    source integer,
    comment text,
    status integer
);


--
-- TOC entry 215 (class 1259 OID 677019)
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
-- TOC entry 3587 (class 0 OID 0)
-- Dependencies: 215
-- Name: evaluation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.evaluation_id_seq OWNED BY public.evaluation.id;


--
-- TOC entry 216 (class 1259 OID 677021)
-- Name: experiment; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.experiment (
    id integer NOT NULL,
    study integer
);


--
-- TOC entry 217 (class 1259 OID 677024)
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
-- TOC entry 3588 (class 0 OID 0)
-- Dependencies: 217
-- Name: experiment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.experiment_id_seq OWNED BY public.experiment.id;


--
-- TOC entry 218 (class 1259 OID 677026)
-- Name: group; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."group" (
    id integer NOT NULL,
    name text,
    description text
);


--
-- TOC entry 219 (class 1259 OID 677032)
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
-- TOC entry 3589 (class 0 OID 0)
-- Dependencies: 219
-- Name: group_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.group_id_seq OWNED BY public."group".id;


--
-- TOC entry 220 (class 1259 OID 677034)
-- Name: incentive; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.incentive (
    id integer NOT NULL,
    study integer,
    participant integer
);


--
-- TOC entry 221 (class 1259 OID 677037)
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
-- TOC entry 3590 (class 0 OID 0)
-- Dependencies: 221
-- Name: incentive_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.incentive_id_seq OWNED BY public.incentive.id;


--
-- TOC entry 222 (class 1259 OID 677039)
-- Name: language; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.language (
    id integer NOT NULL,
    name text,
    code text,
    translate boolean DEFAULT false
);


--
-- TOC entry 223 (class 1259 OID 677046)
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
-- TOC entry 3591 (class 0 OID 0)
-- Dependencies: 223
-- Name: language_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.language_id_seq OWNED BY public.language.id;


--
-- TOC entry 224 (class 1259 OID 677048)
-- Name: language_study; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.language_study (
    language integer NOT NULL,
    study integer NOT NULL
);


--
-- TOC entry 225 (class 1259 OID 677051)
-- Name: logger; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.logger (
    id integer NOT NULL,
    clicked boolean,
    "limit" text
);


--
-- TOC entry 226 (class 1259 OID 677057)
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
-- TOC entry 3592 (class 0 OID 0)
-- Dependencies: 226
-- Name: logger_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.logger_id_seq OWNED BY public.logger.id;


--
-- TOC entry 227 (class 1259 OID 677059)
-- Name: logger_query; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.logger_query (
    logger integer NOT NULL,
    query integer NOT NULL
);


--
-- TOC entry 228 (class 1259 OID 677062)
-- Name: logger_result; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.logger_result (
    logger integer NOT NULL,
    result integer NOT NULL
);


--
-- TOC entry 229 (class 1259 OID 677065)
-- Name: logger_scraper; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.logger_scraper (
    logger integer NOT NULL,
    scraper integer NOT NULL
);


--
-- TOC entry 230 (class 1259 OID 677068)
-- Name: logger_searchengine; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.logger_searchengine (
    logger integer NOT NULL,
    searchengine integer NOT NULL
);


--
-- TOC entry 231 (class 1259 OID 677071)
-- Name: logger_serp; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.logger_serp (
    logger integer NOT NULL,
    serp integer NOT NULL
);


--
-- TOC entry 232 (class 1259 OID 677074)
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
-- TOC entry 233 (class 1259 OID 677081)
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
-- TOC entry 3593 (class 0 OID 0)
-- Dependencies: 233
-- Name: monitoring_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.monitoring_id_seq OWNED BY public.monitoring.id;


--
-- TOC entry 234 (class 1259 OID 677083)
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
-- TOC entry 235 (class 1259 OID 677089)
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
-- TOC entry 3594 (class 0 OID 0)
-- Dependencies: 235
-- Name: option_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.option_id_seq OWNED BY public.option.id;


--
-- TOC entry 236 (class 1259 OID 677091)
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
-- TOC entry 237 (class 1259 OID 677097)
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
-- TOC entry 3595 (class 0 OID 0)
-- Dependencies: 237
-- Name: participant_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.participant_id_seq OWNED BY public.participant.id;


--
-- TOC entry 238 (class 1259 OID 677099)
-- Name: participant_study; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.participant_study (
    participant integer NOT NULL,
    study integer NOT NULL
);


--
-- TOC entry 239 (class 1259 OID 677102)
-- Name: provider; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.provider (
    id integer NOT NULL,
    name text
);


--
-- TOC entry 240 (class 1259 OID 677108)
-- Name: provider_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.provider_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3596 (class 0 OID 0)
-- Dependencies: 240
-- Name: provider_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.provider_id_seq OWNED BY public.provider.id;


--
-- TOC entry 241 (class 1259 OID 677110)
-- Name: qs_geotarget; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.qs_geotarget (
    id integer NOT NULL,
    name text NOT NULL,
    canonical_name text NOT NULL,
    country_code text NOT NULL,
    target_type text NOT NULL,
    criterion_id integer NOT NULL
);


--
-- TOC entry 242 (class 1259 OID 677116)
-- Name: qs_geotarget_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.qs_geotarget_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3597 (class 0 OID 0)
-- Dependencies: 242
-- Name: qs_geotarget_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.qs_geotarget_id_seq OWNED BY public.qs_geotarget.id;


--
-- TOC entry 243 (class 1259 OID 677118)
-- Name: qs_keyword; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.qs_keyword (
    id integer NOT NULL,
    qs_study_id integer NOT NULL,
    qs_geotarget_criterion_id integer NOT NULL,
    qs_language_code_criterion_id integer NOT NULL,
    keyword text NOT NULL,
    created_at timestamp without time zone,
    status integer DEFAULT 0
);


--
-- TOC entry 244 (class 1259 OID 677125)
-- Name: qs_keyword_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.qs_keyword_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3598 (class 0 OID 0)
-- Dependencies: 244
-- Name: qs_keyword_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.qs_keyword_id_seq OWNED BY public.qs_keyword.id;


--
-- TOC entry 245 (class 1259 OID 677127)
-- Name: qs_keyword_idea; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.qs_keyword_idea (
    id integer NOT NULL,
    qs_study_id integer NOT NULL,
    qs_keyword_id integer NOT NULL,
    keyword_idea text NOT NULL,
    avg_monthly_searches integer NOT NULL,
    competition text NOT NULL,
    created_at timestamp without time zone
);


--
-- TOC entry 246 (class 1259 OID 677133)
-- Name: qs_keyword_ideas_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.qs_keyword_ideas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3599 (class 0 OID 0)
-- Dependencies: 246
-- Name: qs_keyword_ideas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.qs_keyword_ideas_id_seq OWNED BY public.qs_keyword_idea.id;


--
-- TOC entry 247 (class 1259 OID 677135)
-- Name: qs_language_code; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.qs_language_code (
    id integer NOT NULL,
    name text NOT NULL,
    code text NOT NULL,
    criterion_id integer NOT NULL
);


--
-- TOC entry 248 (class 1259 OID 677141)
-- Name: qs_language_code_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.qs_language_code_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3600 (class 0 OID 0)
-- Dependencies: 248
-- Name: qs_language_code_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.qs_language_code_id_seq OWNED BY public.qs_language_code.id;


--
-- TOC entry 249 (class 1259 OID 677143)
-- Name: qs_study; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.qs_study (
    id integer NOT NULL,
    name character varying NOT NULL,
    created_at timestamp without time zone,
    status integer DEFAULT 0
);


--
-- TOC entry 250 (class 1259 OID 677150)
-- Name: qs_study_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.qs_study_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3601 (class 0 OID 0)
-- Dependencies: 250
-- Name: qs_study_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.qs_study_id_seq OWNED BY public.qs_study.id;


--
-- TOC entry 251 (class 1259 OID 677152)
-- Name: query; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.query (
    id integer NOT NULL,
    query text,
    created_at timestamp without time zone,
    study integer,
    description text,
    "limit" integer,
    monitoring integer
);


--
-- TOC entry 252 (class 1259 OID 677158)
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
-- TOC entry 3602 (class 0 OID 0)
-- Dependencies: 252
-- Name: query_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.query_id_seq OWNED BY public.query.id;


--
-- TOC entry 253 (class 1259 OID 677160)
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
-- TOC entry 254 (class 1259 OID 677166)
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
-- TOC entry 3603 (class 0 OID 0)
-- Dependencies: 254
-- Name: question_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.question_id_seq OWNED BY public.question.id;


--
-- TOC entry 255 (class 1259 OID 677168)
-- Name: question_result; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.question_result (
    question integer NOT NULL,
    result integer NOT NULL
);


--
-- TOC entry 256 (class 1259 OID 677171)
-- Name: questiontemplate; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.questiontemplate (
    id integer NOT NULL,
    name text,
    description text
);


--
-- TOC entry 257 (class 1259 OID 677177)
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
-- TOC entry 3604 (class 0 OID 0)
-- Dependencies: 257
-- Name: questiontemplate_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.questiontemplate_id_seq OWNED BY public.questiontemplate.id;


--
-- TOC entry 258 (class 1259 OID 677179)
-- Name: questiontype; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.questiontype (
    id integer NOT NULL,
    name text,
    display text
);


--
-- TOC entry 259 (class 1259 OID 677185)
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
-- TOC entry 3605 (class 0 OID 0)
-- Dependencies: 259
-- Name: questiontype_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.questiontype_id_seq OWNED BY public.questiontype.id;


--
-- TOC entry 260 (class 1259 OID 677187)
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
-- TOC entry 261 (class 1259 OID 677193)
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
-- TOC entry 3606 (class 0 OID 0)
-- Dependencies: 261
-- Name: reporting_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.reporting_id_seq OWNED BY public.reporting.id;


--
-- TOC entry 262 (class 1259 OID 677195)
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
    resulttype integer,
    monitoring integer,
    serp integer,
    query integer,
    final_url text
);


--
-- TOC entry 263 (class 1259 OID 677201)
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
-- TOC entry 3607 (class 0 OID 0)
-- Dependencies: 263
-- Name: result_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.result_id_seq OWNED BY public.result.id;


--
-- TOC entry 264 (class 1259 OID 677203)
-- Name: result_source; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.result_source (
    result integer,
    source integer,
    progress integer,
    id integer NOT NULL,
    counter integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone,
    error_code text,
    job_server text
);


--
-- TOC entry 265 (class 1259 OID 677210)
-- Name: result_source_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.result_source_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3608 (class 0 OID 0)
-- Dependencies: 265
-- Name: result_source_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.result_source_id_seq OWNED BY public.result_source.id;


--
-- TOC entry 266 (class 1259 OID 677212)
-- Name: resulttype; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.resulttype (
    id integer NOT NULL,
    name text,
    display text
);


--
-- TOC entry 267 (class 1259 OID 677218)
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
-- TOC entry 3609 (class 0 OID 0)
-- Dependencies: 267
-- Name: resulttype_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.resulttype_id_seq OWNED BY public.resulttype.id;


--
-- TOC entry 268 (class 1259 OID 677220)
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
-- TOC entry 269 (class 1259 OID 677226)
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
-- TOC entry 3610 (class 0 OID 0)
-- Dependencies: 269
-- Name: role_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.role_id_seq OWNED BY public.role.id;


--
-- TOC entry 270 (class 1259 OID 677228)
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
    type integer,
    job_server text
);


--
-- TOC entry 271 (class 1259 OID 677234)
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
-- TOC entry 3611 (class 0 OID 0)
-- Dependencies: 271
-- Name: scraper_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.scraper_id_seq OWNED BY public.scraper.id;


--
-- TOC entry 272 (class 1259 OID 677236)
-- Name: searchengine; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.searchengine (
    id integer NOT NULL,
    name text,
    module text,
    test integer,
    error_code text,
    resulttype integer,
    country text,
    provider text
);


--
-- TOC entry 273 (class 1259 OID 677242)
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
-- TOC entry 3612 (class 0 OID 0)
-- Dependencies: 273
-- Name: searchengine_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.searchengine_id_seq OWNED BY public.searchengine.id;


--
-- TOC entry 274 (class 1259 OID 677244)
-- Name: searchengine_study; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.searchengine_study (
    searchengine integer NOT NULL,
    study integer NOT NULL
);


--
-- TOC entry 275 (class 1259 OID 677247)
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
-- TOC entry 276 (class 1259 OID 677253)
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
-- TOC entry 3613 (class 0 OID 0)
-- Dependencies: 276
-- Name: serp_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.serp_id_seq OWNED BY public.serp.id;


--
-- TOC entry 277 (class 1259 OID 677255)
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
    created_at timestamp without time zone,
    job_server text,
    content_dict text
);


--
-- TOC entry 278 (class 1259 OID 677261)
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
-- TOC entry 3614 (class 0 OID 0)
-- Dependencies: 278
-- Name: source_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.source_id_seq OWNED BY public.source.id;


--
-- TOC entry 279 (class 1259 OID 677263)
-- Name: statistic; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.statistic (
    id integer NOT NULL,
    study integer,
    name text,
    value text
);


--
-- TOC entry 280 (class 1259 OID 677269)
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
-- TOC entry 3615 (class 0 OID 0)
-- Dependencies: 280
-- Name: statistic_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.statistic_id_seq OWNED BY public.statistic.id;


--
-- TOC entry 281 (class 1259 OID 677271)
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
    status integer,
    task text
);


--
-- TOC entry 282 (class 1259 OID 677277)
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
-- TOC entry 3616 (class 0 OID 0)
-- Dependencies: 282
-- Name: study_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.study_id_seq OWNED BY public.study.id;


--
-- TOC entry 283 (class 1259 OID 677279)
-- Name: study_user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.study_user (
    study integer NOT NULL,
    "user" integer NOT NULL
);


--
-- TOC entry 284 (class 1259 OID 677282)
-- Name: studytype; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.studytype (
    id integer NOT NULL,
    name text
);


--
-- TOC entry 285 (class 1259 OID 677288)
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
-- TOC entry 3617 (class 0 OID 0)
-- Dependencies: 285
-- Name: studytype_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.studytype_id_seq OWNED BY public.studytype.id;


--
-- TOC entry 286 (class 1259 OID 677290)
-- Name: task; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.task (
    id integer NOT NULL,
    logger integer
);


--
-- TOC entry 287 (class 1259 OID 677293)
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
-- TOC entry 3618 (class 0 OID 0)
-- Dependencies: 287
-- Name: task_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.task_id_seq OWNED BY public.task.id;


--
-- TOC entry 288 (class 1259 OID 677295)
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
    us_phone_number text,
    affiliation text
);


--
-- TOC entry 289 (class 1259 OID 677301)
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
-- TOC entry 3619 (class 0 OID 0)
-- Dependencies: 289
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_id_seq OWNED BY public."user".id;


--
-- TOC entry 290 (class 1259 OID 677303)
-- Name: user_role; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_role (
    "user" integer,
    role integer
);


--
-- TOC entry 3104 (class 2604 OID 677306)
-- Name: answer id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.answer ALTER COLUMN id SET DEFAULT nextval('public.answer_id_seq'::regclass);


--
-- TOC entry 3105 (class 2604 OID 677307)
-- Name: classifier id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classifier ALTER COLUMN id SET DEFAULT nextval('public.classifier_id_seq'::regclass);


--
-- TOC entry 3107 (class 2604 OID 677308)
-- Name: classifier_indicator id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classifier_indicator ALTER COLUMN id SET DEFAULT nextval('public.classifier_indicator_id_seq'::regclass);


--
-- TOC entry 3109 (class 2604 OID 677309)
-- Name: classifier_result id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classifier_result ALTER COLUMN id SET DEFAULT nextval('public.classifier_result_id_seq'::regclass);


--
-- TOC entry 3111 (class 2604 OID 677310)
-- Name: content id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.content ALTER COLUMN id SET DEFAULT nextval('public.content_id_seq'::regclass);


--
-- TOC entry 3112 (class 2604 OID 677311)
-- Name: country id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.country ALTER COLUMN id SET DEFAULT nextval('public.country_id_seq'::regclass);


--
-- TOC entry 3114 (class 2604 OID 677312)
-- Name: dummy_table id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dummy_table ALTER COLUMN id SET DEFAULT nextval('public.dummy_table_id_seq'::regclass);


--
-- TOC entry 3115 (class 2604 OID 677313)
-- Name: evaluation id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluation ALTER COLUMN id SET DEFAULT nextval('public.evaluation_id_seq'::regclass);


--
-- TOC entry 3116 (class 2604 OID 677314)
-- Name: experiment id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.experiment ALTER COLUMN id SET DEFAULT nextval('public.experiment_id_seq'::regclass);


--
-- TOC entry 3117 (class 2604 OID 677315)
-- Name: group id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."group" ALTER COLUMN id SET DEFAULT nextval('public.group_id_seq'::regclass);


--
-- TOC entry 3118 (class 2604 OID 677316)
-- Name: incentive id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.incentive ALTER COLUMN id SET DEFAULT nextval('public.incentive_id_seq'::regclass);


--
-- TOC entry 3120 (class 2604 OID 677317)
-- Name: language id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.language ALTER COLUMN id SET DEFAULT nextval('public.language_id_seq'::regclass);


--
-- TOC entry 3121 (class 2604 OID 677318)
-- Name: logger id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger ALTER COLUMN id SET DEFAULT nextval('public.logger_id_seq'::regclass);


--
-- TOC entry 3123 (class 2604 OID 677319)
-- Name: monitoring id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.monitoring ALTER COLUMN id SET DEFAULT nextval('public.monitoring_id_seq'::regclass);


--
-- TOC entry 3124 (class 2604 OID 677320)
-- Name: option id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.option ALTER COLUMN id SET DEFAULT nextval('public.option_id_seq'::regclass);


--
-- TOC entry 3125 (class 2604 OID 677321)
-- Name: participant id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.participant ALTER COLUMN id SET DEFAULT nextval('public.participant_id_seq'::regclass);


--
-- TOC entry 3126 (class 2604 OID 677322)
-- Name: provider id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.provider ALTER COLUMN id SET DEFAULT nextval('public.provider_id_seq'::regclass);


--
-- TOC entry 3127 (class 2604 OID 677323)
-- Name: qs_geotarget id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.qs_geotarget ALTER COLUMN id SET DEFAULT nextval('public.qs_geotarget_id_seq'::regclass);


--
-- TOC entry 3129 (class 2604 OID 677324)
-- Name: qs_keyword id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.qs_keyword ALTER COLUMN id SET DEFAULT nextval('public.qs_keyword_id_seq'::regclass);


--
-- TOC entry 3130 (class 2604 OID 677325)
-- Name: qs_keyword_idea id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.qs_keyword_idea ALTER COLUMN id SET DEFAULT nextval('public.qs_keyword_ideas_id_seq'::regclass);


--
-- TOC entry 3131 (class 2604 OID 677326)
-- Name: qs_language_code id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.qs_language_code ALTER COLUMN id SET DEFAULT nextval('public.qs_language_code_id_seq'::regclass);


--
-- TOC entry 3133 (class 2604 OID 677327)
-- Name: qs_study id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.qs_study ALTER COLUMN id SET DEFAULT nextval('public.qs_study_id_seq'::regclass);


--
-- TOC entry 3134 (class 2604 OID 677328)
-- Name: query id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.query ALTER COLUMN id SET DEFAULT nextval('public.query_id_seq'::regclass);


--
-- TOC entry 3135 (class 2604 OID 677329)
-- Name: question id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question ALTER COLUMN id SET DEFAULT nextval('public.question_id_seq'::regclass);


--
-- TOC entry 3136 (class 2604 OID 677330)
-- Name: questiontemplate id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questiontemplate ALTER COLUMN id SET DEFAULT nextval('public.questiontemplate_id_seq'::regclass);


--
-- TOC entry 3137 (class 2604 OID 677331)
-- Name: questiontype id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questiontype ALTER COLUMN id SET DEFAULT nextval('public.questiontype_id_seq'::regclass);


--
-- TOC entry 3138 (class 2604 OID 677332)
-- Name: reporting id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reporting ALTER COLUMN id SET DEFAULT nextval('public.reporting_id_seq'::regclass);


--
-- TOC entry 3139 (class 2604 OID 677333)
-- Name: result id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.result ALTER COLUMN id SET DEFAULT nextval('public.result_id_seq'::regclass);


--
-- TOC entry 3141 (class 2604 OID 677334)
-- Name: result_source id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.result_source ALTER COLUMN id SET DEFAULT nextval('public.result_source_id_seq'::regclass);


--
-- TOC entry 3142 (class 2604 OID 677335)
-- Name: resulttype id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resulttype ALTER COLUMN id SET DEFAULT nextval('public.resulttype_id_seq'::regclass);


--
-- TOC entry 3143 (class 2604 OID 677336)
-- Name: role id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role ALTER COLUMN id SET DEFAULT nextval('public.role_id_seq'::regclass);


--
-- TOC entry 3144 (class 2604 OID 677337)
-- Name: scraper id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scraper ALTER COLUMN id SET DEFAULT nextval('public.scraper_id_seq'::regclass);


--
-- TOC entry 3145 (class 2604 OID 677338)
-- Name: searchengine id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.searchengine ALTER COLUMN id SET DEFAULT nextval('public.searchengine_id_seq'::regclass);


--
-- TOC entry 3146 (class 2604 OID 677339)
-- Name: serp id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.serp ALTER COLUMN id SET DEFAULT nextval('public.serp_id_seq'::regclass);


--
-- TOC entry 3147 (class 2604 OID 677340)
-- Name: source id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.source ALTER COLUMN id SET DEFAULT nextval('public.source_id_seq'::regclass);


--
-- TOC entry 3148 (class 2604 OID 677341)
-- Name: statistic id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.statistic ALTER COLUMN id SET DEFAULT nextval('public.statistic_id_seq'::regclass);


--
-- TOC entry 3149 (class 2604 OID 677342)
-- Name: study id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study ALTER COLUMN id SET DEFAULT nextval('public.study_id_seq'::regclass);


--
-- TOC entry 3150 (class 2604 OID 677343)
-- Name: studytype id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.studytype ALTER COLUMN id SET DEFAULT nextval('public.studytype_id_seq'::regclass);


--
-- TOC entry 3151 (class 2604 OID 677344)
-- Name: task id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task ALTER COLUMN id SET DEFAULT nextval('public.task_id_seq'::regclass);


--
-- TOC entry 3152 (class 2604 OID 677345)
-- Name: user id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user" ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);


--
-- TOC entry 3479 (class 0 OID 676942)
-- Dependencies: 196
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3480 (class 0 OID 676945)
-- Dependencies: 197
-- Data for Name: answer; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3482 (class 0 OID 676953)
-- Dependencies: 199
-- Data for Name: classifier; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.classifier (id, name, display_name) VALUES (1, 'seo_rule_based', 'SEO (rule-based)');


--
-- TOC entry 3484 (class 0 OID 676961)
-- Dependencies: 201
-- Data for Name: classifier_indicator; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3486 (class 0 OID 676970)
-- Dependencies: 203
-- Data for Name: classifier_result; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3489 (class 0 OID 676981)
-- Dependencies: 206
-- Data for Name: classifier_study; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3490 (class 0 OID 676985)
-- Dependencies: 207
-- Data for Name: content; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3492 (class 0 OID 676993)
-- Dependencies: 209
-- Data for Name: country; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.country (id, name, code, language) VALUES (1, 'Germany', 'de', NULL);
INSERT INTO public.country (id, name, code, language) VALUES (2, '	USA', 'us', NULL);
INSERT INTO public.country (id, name, code, language) VALUES (3, 'Sweden', 'se', NULL);
INSERT INTO public.country (id, name, code, language) VALUES (4, 'Ireland', 'ie', NULL);
INSERT INTO public.country (id, name, code, language) VALUES (5, 'Mexico', 'mx', NULL);
INSERT INTO public.country (id, name, code, language) VALUES (6, 'United Kingdom', 'gb', NULL);


--
-- TOC entry 3494 (class 0 OID 677001)
-- Dependencies: 211
-- Data for Name: country_monitoring; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3495 (class 0 OID 677004)
-- Dependencies: 212
-- Data for Name: dummy_table; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3497 (class 0 OID 677013)
-- Dependencies: 214
-- Data for Name: evaluation; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3499 (class 0 OID 677021)
-- Dependencies: 216
-- Data for Name: experiment; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3501 (class 0 OID 677026)
-- Dependencies: 218
-- Data for Name: group; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3503 (class 0 OID 677034)
-- Dependencies: 220
-- Data for Name: incentive; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3505 (class 0 OID 677039)
-- Dependencies: 222
-- Data for Name: language; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3507 (class 0 OID 677048)
-- Dependencies: 224
-- Data for Name: language_study; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3508 (class 0 OID 677051)
-- Dependencies: 225
-- Data for Name: logger; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3510 (class 0 OID 677059)
-- Dependencies: 227
-- Data for Name: logger_query; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3511 (class 0 OID 677062)
-- Dependencies: 228
-- Data for Name: logger_result; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3512 (class 0 OID 677065)
-- Dependencies: 229
-- Data for Name: logger_scraper; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3513 (class 0 OID 677068)
-- Dependencies: 230
-- Data for Name: logger_searchengine; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3514 (class 0 OID 677071)
-- Dependencies: 231
-- Data for Name: logger_serp; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3515 (class 0 OID 677074)
-- Dependencies: 232
-- Data for Name: monitoring; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3517 (class 0 OID 677083)
-- Dependencies: 234
-- Data for Name: option; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3519 (class 0 OID 677091)
-- Dependencies: 236
-- Data for Name: participant; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3521 (class 0 OID 677099)
-- Dependencies: 238
-- Data for Name: participant_study; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3522 (class 0 OID 677102)
-- Dependencies: 239
-- Data for Name: provider; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.provider (id, name) VALUES (1, 'Google');
INSERT INTO public.provider (id, name) VALUES (2, 'Microsoft');
INSERT INTO public.provider (id, name) VALUES (3, 'Ecosia');
INSERT INTO public.provider (id, name) VALUES (4, 'Stabi Hamburg');


--
-- TOC entry 3524 (class 0 OID 677110)
-- Dependencies: 241
-- Data for Name: qs_geotarget; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3526 (class 0 OID 677118)
-- Dependencies: 243
-- Data for Name: qs_keyword; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3528 (class 0 OID 677127)
-- Dependencies: 245
-- Data for Name: qs_keyword_idea; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3530 (class 0 OID 677135)
-- Dependencies: 247
-- Data for Name: qs_language_code; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3532 (class 0 OID 677143)
-- Dependencies: 249
-- Data for Name: qs_study; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3534 (class 0 OID 677152)
-- Dependencies: 251
-- Data for Name: query; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3536 (class 0 OID 677160)
-- Dependencies: 253
-- Data for Name: question; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3538 (class 0 OID 677168)
-- Dependencies: 255
-- Data for Name: question_result; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3539 (class 0 OID 677171)
-- Dependencies: 256
-- Data for Name: questiontemplate; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3541 (class 0 OID 677179)
-- Dependencies: 258
-- Data for Name: questiontype; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.questiontype (id, name, display) VALUES (1, 'Short Text', 'short_text');
INSERT INTO public.questiontype (id, name, display) VALUES (2, 'Long Text', 'long_text');
INSERT INTO public.questiontype (id, name, display) VALUES (3, 'Single Choice', 'true_false');
INSERT INTO public.questiontype (id, name, display) VALUES (4, 'Rating Scale', 'likert_scale');
INSERT INTO public.questiontype (id, name, display) VALUES (5, 'Multiple Choice', 'multiple_choice');
INSERT INTO public.questiontype (id, name, display) VALUES (6, 'Sliding Scale', 'scale_number');


--
-- TOC entry 3543 (class 0 OID 677187)
-- Dependencies: 260
-- Data for Name: reporting; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3545 (class 0 OID 677195)
-- Dependencies: 262
-- Data for Name: result; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3547 (class 0 OID 677203)
-- Dependencies: 264
-- Data for Name: result_source; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3549 (class 0 OID 677212)
-- Dependencies: 266
-- Data for Name: resulttype; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.resulttype (id, name, display) VALUES (1, 'Organic Results', 'organic');
INSERT INTO public.resulttype (id, name, display) VALUES (2, 'Snippets', 'snippet');
INSERT INTO public.resulttype (id, name, display) VALUES (3, 'Universal Search Results', 'universal');
INSERT INTO public.resulttype (id, name, display) VALUES (4, 'Advertisements', 'ad');
INSERT INTO public.resulttype (id, name, display) VALUES (5, 'News', 'news');


--
-- TOC entry 3551 (class 0 OID 677220)
-- Dependencies: 268
-- Data for Name: role; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3553 (class 0 OID 677228)
-- Dependencies: 270
-- Data for Name: scraper; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3555 (class 0 OID 677236)
-- Dependencies: 272
-- Data for Name: searchengine; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.searchengine (id, name, module, test, error_code, resulttype, country, provider) VALUES (1, 'Google_DE', 'google_de.py', 1, NULL, 1, '1', '1');
INSERT INTO public.searchengine (id, name, module, test, error_code, resulttype, country, provider) VALUES (2, 'Bing_DE', 'bing_de.py', 1, NULL, 1, '1', '2');
INSERT INTO public.searchengine (id, name, module, test, error_code, resulttype, country, provider) VALUES (3, 'Google_SE', 'google_se.py', 1, NULL, 1, '3', '1');
INSERT INTO public.searchengine (id, name, module, test, error_code, resulttype, country, provider) VALUES (4, 'Ecosia_DE', 'ecosia_de.py', 1, NULL, 1, '1', '3');
INSERT INTO public.searchengine (id, name, module, test, error_code, resulttype, country, provider) VALUES (5, 'Katalogplus Bücher & mehr ', 'katalogplus_de_books.py', 1, NULL, 1, '1', '4');
INSERT INTO public.searchengine (id, name, module, test, error_code, resulttype, country, provider) VALUES (6, 'Katalogplus Artikel', 'katalogplus_de_articles.py', 1, NULL, 1, '1', '4');


--
-- TOC entry 3557 (class 0 OID 677244)
-- Dependencies: 274
-- Data for Name: searchengine_study; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3558 (class 0 OID 677247)
-- Dependencies: 275
-- Data for Name: serp; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3560 (class 0 OID 677255)
-- Dependencies: 277
-- Data for Name: source; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3562 (class 0 OID 677263)
-- Dependencies: 279
-- Data for Name: statistic; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3564 (class 0 OID 677271)
-- Dependencies: 281
-- Data for Name: study; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3566 (class 0 OID 677279)
-- Dependencies: 283
-- Data for Name: study_user; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3567 (class 0 OID 677282)
-- Dependencies: 284
-- Data for Name: studytype; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.studytype (id, name) VALUES (1, 'Relevance Assessment');
INSERT INTO public.studytype (id, name) VALUES (2, 'Classification Task');
INSERT INTO public.studytype (id, name) VALUES (3, 'Interactive Information Retrieval');
INSERT INTO public.studytype (id, name) VALUES (4, 'Experiment');
INSERT INTO public.studytype (id, name) VALUES (5, 'Custom');
INSERT INTO public.studytype (id, name) VALUES (6, 'Only URLs from search results');


--
-- TOC entry 3569 (class 0 OID 677290)
-- Dependencies: 286
-- Data for Name: task; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3571 (class 0 OID 677295)
-- Dependencies: 288
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3573 (class 0 OID 677303)
-- Dependencies: 290
-- Data for Name: user_role; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3620 (class 0 OID 0)
-- Dependencies: 198
-- Name: answer_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.answer_id_seq', 1, false);


--
-- TOC entry 3621 (class 0 OID 0)
-- Dependencies: 200
-- Name: classifier_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.classifier_id_seq', 1, true);


--
-- TOC entry 3622 (class 0 OID 0)
-- Dependencies: 202
-- Name: classifier_indicator_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.classifier_indicator_id_seq', 1, false);


--
-- TOC entry 3623 (class 0 OID 0)
-- Dependencies: 204
-- Name: classifier_result_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.classifier_result_id_seq', 1, false);


--
-- TOC entry 3624 (class 0 OID 0)
-- Dependencies: 205
-- Name: classifier_study_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.classifier_study_id_seq', 1, false);


--
-- TOC entry 3625 (class 0 OID 0)
-- Dependencies: 208
-- Name: content_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.content_id_seq', 1, false);


--
-- TOC entry 3626 (class 0 OID 0)
-- Dependencies: 210
-- Name: country_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.country_id_seq', 6, true);


--
-- TOC entry 3627 (class 0 OID 0)
-- Dependencies: 213
-- Name: dummy_table_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dummy_table_id_seq', 1, false);


--
-- TOC entry 3628 (class 0 OID 0)
-- Dependencies: 215
-- Name: evaluation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.evaluation_id_seq', 1, false);


--
-- TOC entry 3629 (class 0 OID 0)
-- Dependencies: 217
-- Name: experiment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.experiment_id_seq', 1, false);


--
-- TOC entry 3630 (class 0 OID 0)
-- Dependencies: 219
-- Name: group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.group_id_seq', 1, false);


--
-- TOC entry 3631 (class 0 OID 0)
-- Dependencies: 221
-- Name: incentive_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.incentive_id_seq', 1, false);


--
-- TOC entry 3632 (class 0 OID 0)
-- Dependencies: 223
-- Name: language_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.language_id_seq', 1, false);


--
-- TOC entry 3633 (class 0 OID 0)
-- Dependencies: 226
-- Name: logger_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.logger_id_seq', 1, false);


--
-- TOC entry 3634 (class 0 OID 0)
-- Dependencies: 233
-- Name: monitoring_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.monitoring_id_seq', 1, false);


--
-- TOC entry 3635 (class 0 OID 0)
-- Dependencies: 235
-- Name: option_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.option_id_seq', 1, false);


--
-- TOC entry 3636 (class 0 OID 0)
-- Dependencies: 237
-- Name: participant_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.participant_id_seq', 1, false);


--
-- TOC entry 3637 (class 0 OID 0)
-- Dependencies: 240
-- Name: provider_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.provider_id_seq', 4, true);


--
-- TOC entry 3638 (class 0 OID 0)
-- Dependencies: 242
-- Name: qs_geotarget_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.qs_geotarget_id_seq', 1, false);


--
-- TOC entry 3639 (class 0 OID 0)
-- Dependencies: 244
-- Name: qs_keyword_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.qs_keyword_id_seq', 1, false);


--
-- TOC entry 3640 (class 0 OID 0)
-- Dependencies: 246
-- Name: qs_keyword_ideas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.qs_keyword_ideas_id_seq', 1, false);


--
-- TOC entry 3641 (class 0 OID 0)
-- Dependencies: 248
-- Name: qs_language_code_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.qs_language_code_id_seq', 1, false);


--
-- TOC entry 3642 (class 0 OID 0)
-- Dependencies: 250
-- Name: qs_study_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.qs_study_id_seq', 1, false);


--
-- TOC entry 3643 (class 0 OID 0)
-- Dependencies: 252
-- Name: query_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.query_id_seq', 1, false);


--
-- TOC entry 3644 (class 0 OID 0)
-- Dependencies: 254
-- Name: question_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.question_id_seq', 1, false);


--
-- TOC entry 3645 (class 0 OID 0)
-- Dependencies: 257
-- Name: questiontemplate_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.questiontemplate_id_seq', 1, false);


--
-- TOC entry 3646 (class 0 OID 0)
-- Dependencies: 259
-- Name: questiontype_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.questiontype_id_seq', 6, true);


--
-- TOC entry 3647 (class 0 OID 0)
-- Dependencies: 261
-- Name: reporting_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.reporting_id_seq', 1, false);


--
-- TOC entry 3648 (class 0 OID 0)
-- Dependencies: 263
-- Name: result_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.result_id_seq', 1, false);


--
-- TOC entry 3649 (class 0 OID 0)
-- Dependencies: 265
-- Name: result_source_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.result_source_id_seq', 1, false);


--
-- TOC entry 3650 (class 0 OID 0)
-- Dependencies: 267
-- Name: resulttype_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.resulttype_id_seq', 5, true);


--
-- TOC entry 3651 (class 0 OID 0)
-- Dependencies: 269
-- Name: role_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.role_id_seq', 1, false);


--
-- TOC entry 3652 (class 0 OID 0)
-- Dependencies: 271
-- Name: scraper_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.scraper_id_seq', 1, false);


--
-- TOC entry 3653 (class 0 OID 0)
-- Dependencies: 273
-- Name: searchengine_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.searchengine_id_seq', 6, true);


--
-- TOC entry 3654 (class 0 OID 0)
-- Dependencies: 276
-- Name: serp_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.serp_id_seq', 1, false);


--
-- TOC entry 3655 (class 0 OID 0)
-- Dependencies: 278
-- Name: source_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.source_id_seq', 1, false);


--
-- TOC entry 3656 (class 0 OID 0)
-- Dependencies: 280
-- Name: statistic_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.statistic_id_seq', 1, false);


--
-- TOC entry 3657 (class 0 OID 0)
-- Dependencies: 282
-- Name: study_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.study_id_seq', 1, false);


--
-- TOC entry 3658 (class 0 OID 0)
-- Dependencies: 285
-- Name: studytype_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.studytype_id_seq', 6, true);


--
-- TOC entry 3659 (class 0 OID 0)
-- Dependencies: 287
-- Name: task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.task_id_seq', 1, false);


--
-- TOC entry 3660 (class 0 OID 0)
-- Dependencies: 289
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.user_id_seq', 1, false);


--
-- TOC entry 3154 (class 2606 OID 677347)
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- TOC entry 3156 (class 2606 OID 677349)
-- Name: answer answer_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.answer
    ADD CONSTRAINT answer_pkey PRIMARY KEY (id);


--
-- TOC entry 3164 (class 2606 OID 677351)
-- Name: classifier_indicator classifier_indicator_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classifier_indicator
    ADD CONSTRAINT classifier_indicator_pkey PRIMARY KEY (id);


--
-- TOC entry 3162 (class 2606 OID 677353)
-- Name: classifier classifier_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classifier
    ADD CONSTRAINT classifier_pkey PRIMARY KEY (id);


--
-- TOC entry 3166 (class 2606 OID 677355)
-- Name: classifier_result classifier_result_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classifier_result
    ADD CONSTRAINT classifier_result_pkey PRIMARY KEY (id);


--
-- TOC entry 3168 (class 2606 OID 677357)
-- Name: classifier_study classifier_study_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classifier_study
    ADD CONSTRAINT classifier_study_pkey PRIMARY KEY (id);


--
-- TOC entry 3170 (class 2606 OID 677359)
-- Name: content content_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.content
    ADD CONSTRAINT content_pkey PRIMARY KEY (id);


--
-- TOC entry 3173 (class 2606 OID 677361)
-- Name: country country_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.country
    ADD CONSTRAINT country_pkey PRIMARY KEY (id);


--
-- TOC entry 3175 (class 2606 OID 677363)
-- Name: dummy_table dummy_table_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dummy_table
    ADD CONSTRAINT dummy_table_pkey PRIMARY KEY (id);


--
-- TOC entry 3177 (class 2606 OID 677365)
-- Name: evaluation evaluation_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluation
    ADD CONSTRAINT evaluation_pkey PRIMARY KEY (id);


--
-- TOC entry 3180 (class 2606 OID 677367)
-- Name: experiment experiment_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.experiment
    ADD CONSTRAINT experiment_pkey PRIMARY KEY (id);


--
-- TOC entry 3183 (class 2606 OID 677369)
-- Name: group group_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."group"
    ADD CONSTRAINT group_pkey PRIMARY KEY (id);


--
-- TOC entry 3187 (class 2606 OID 677371)
-- Name: incentive incentive_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.incentive
    ADD CONSTRAINT incentive_pkey PRIMARY KEY (id);


--
-- TOC entry 3189 (class 2606 OID 677373)
-- Name: language language_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.language
    ADD CONSTRAINT language_pkey PRIMARY KEY (id);


--
-- TOC entry 3192 (class 2606 OID 677375)
-- Name: language_study language_study_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.language_study
    ADD CONSTRAINT language_study_pkey PRIMARY KEY (language, study);


--
-- TOC entry 3194 (class 2606 OID 677377)
-- Name: logger logger_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger
    ADD CONSTRAINT logger_pkey PRIMARY KEY (id);


--
-- TOC entry 3197 (class 2606 OID 677379)
-- Name: logger_query logger_query_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_query
    ADD CONSTRAINT logger_query_pkey PRIMARY KEY (logger, query);


--
-- TOC entry 3200 (class 2606 OID 677381)
-- Name: logger_result logger_result_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_result
    ADD CONSTRAINT logger_result_pkey PRIMARY KEY (logger, result);


--
-- TOC entry 3203 (class 2606 OID 677383)
-- Name: logger_scraper logger_scraper_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_scraper
    ADD CONSTRAINT logger_scraper_pkey PRIMARY KEY (logger, scraper);


--
-- TOC entry 3206 (class 2606 OID 677385)
-- Name: logger_searchengine logger_searchengine_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_searchengine
    ADD CONSTRAINT logger_searchengine_pkey PRIMARY KEY (logger, searchengine);


--
-- TOC entry 3209 (class 2606 OID 677387)
-- Name: logger_serp logger_serp_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_serp
    ADD CONSTRAINT logger_serp_pkey PRIMARY KEY (logger, serp);


--
-- TOC entry 3211 (class 2606 OID 677389)
-- Name: monitoring monitoring_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.monitoring
    ADD CONSTRAINT monitoring_pkey PRIMARY KEY (id);


--
-- TOC entry 3214 (class 2606 OID 677391)
-- Name: option option_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.option
    ADD CONSTRAINT option_pkey PRIMARY KEY (id);


--
-- TOC entry 3217 (class 2606 OID 677393)
-- Name: participant participant_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.participant
    ADD CONSTRAINT participant_pkey PRIMARY KEY (id);


--
-- TOC entry 3220 (class 2606 OID 677395)
-- Name: participant_study participant_study_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.participant_study
    ADD CONSTRAINT participant_study_pkey PRIMARY KEY (participant, study);


--
-- TOC entry 3222 (class 2606 OID 677397)
-- Name: qs_geotarget qs_geotarget_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.qs_geotarget
    ADD CONSTRAINT qs_geotarget_pkey PRIMARY KEY (id);


--
-- TOC entry 3226 (class 2606 OID 677399)
-- Name: qs_keyword_idea qs_keyword_ideas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.qs_keyword_idea
    ADD CONSTRAINT qs_keyword_ideas_pkey PRIMARY KEY (id);


--
-- TOC entry 3224 (class 2606 OID 677401)
-- Name: qs_keyword qs_keyword_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.qs_keyword
    ADD CONSTRAINT qs_keyword_pkey PRIMARY KEY (id);


--
-- TOC entry 3228 (class 2606 OID 677403)
-- Name: qs_language_code qs_language_code_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.qs_language_code
    ADD CONSTRAINT qs_language_code_pkey PRIMARY KEY (id);


--
-- TOC entry 3230 (class 2606 OID 677405)
-- Name: qs_study qs_study_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.qs_study
    ADD CONSTRAINT qs_study_pkey PRIMARY KEY (id);


--
-- TOC entry 3233 (class 2606 OID 677407)
-- Name: query query_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.query
    ADD CONSTRAINT query_pkey PRIMARY KEY (id);


--
-- TOC entry 3238 (class 2606 OID 677409)
-- Name: question question_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question
    ADD CONSTRAINT question_pkey PRIMARY KEY (id);


--
-- TOC entry 3241 (class 2606 OID 677411)
-- Name: question_result question_result_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_result
    ADD CONSTRAINT question_result_pkey PRIMARY KEY (question, result);


--
-- TOC entry 3243 (class 2606 OID 677413)
-- Name: questiontemplate questiontemplate_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questiontemplate
    ADD CONSTRAINT questiontemplate_pkey PRIMARY KEY (id);


--
-- TOC entry 3245 (class 2606 OID 677415)
-- Name: questiontype questiontype_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questiontype
    ADD CONSTRAINT questiontype_pkey PRIMARY KEY (id);


--
-- TOC entry 3248 (class 2606 OID 677417)
-- Name: reporting reporting_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reporting
    ADD CONSTRAINT reporting_pkey PRIMARY KEY (id);


--
-- TOC entry 3254 (class 2606 OID 677419)
-- Name: result result_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.result
    ADD CONSTRAINT result_pkey PRIMARY KEY (id);


--
-- TOC entry 3256 (class 2606 OID 677421)
-- Name: result_source result_source_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.result_source
    ADD CONSTRAINT result_source_pkey PRIMARY KEY (id);


--
-- TOC entry 3258 (class 2606 OID 677423)
-- Name: resulttype resulttype_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resulttype
    ADD CONSTRAINT resulttype_pkey PRIMARY KEY (id);


--
-- TOC entry 3260 (class 2606 OID 677425)
-- Name: role role_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role
    ADD CONSTRAINT role_pkey PRIMARY KEY (id);


--
-- TOC entry 3265 (class 2606 OID 677427)
-- Name: scraper scraper_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scraper
    ADD CONSTRAINT scraper_pkey PRIMARY KEY (id);


--
-- TOC entry 3267 (class 2606 OID 677429)
-- Name: searchengine searchengine_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.searchengine
    ADD CONSTRAINT searchengine_pkey PRIMARY KEY (id);


--
-- TOC entry 3270 (class 2606 OID 677431)
-- Name: searchengine_study searchengine_study_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.searchengine_study
    ADD CONSTRAINT searchengine_study_pkey PRIMARY KEY (searchengine, study);


--
-- TOC entry 3273 (class 2606 OID 677433)
-- Name: serp serp_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.serp
    ADD CONSTRAINT serp_pkey PRIMARY KEY (id);


--
-- TOC entry 3275 (class 2606 OID 677435)
-- Name: source source_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.source
    ADD CONSTRAINT source_pkey PRIMARY KEY (id);


--
-- TOC entry 3278 (class 2606 OID 677437)
-- Name: statistic statistic_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.statistic
    ADD CONSTRAINT statistic_pkey PRIMARY KEY (id);


--
-- TOC entry 3281 (class 2606 OID 677439)
-- Name: study study_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study
    ADD CONSTRAINT study_pkey PRIMARY KEY (id);


--
-- TOC entry 3284 (class 2606 OID 677441)
-- Name: study_user study_user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_user
    ADD CONSTRAINT study_user_pkey PRIMARY KEY (study, "user");


--
-- TOC entry 3286 (class 2606 OID 677443)
-- Name: studytype studytype_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.studytype
    ADD CONSTRAINT studytype_pkey PRIMARY KEY (id);


--
-- TOC entry 3289 (class 2606 OID 677445)
-- Name: task task_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task
    ADD CONSTRAINT task_pkey PRIMARY KEY (id);


--
-- TOC entry 3291 (class 2606 OID 677447)
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- TOC entry 3249 (class 1259 OID 677448)
-- Name: fki_fk_result__serp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX fki_fk_result__serp ON public.result USING btree (serp);


--
-- TOC entry 3250 (class 1259 OID 677449)
-- Name: fki_r; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX fki_r ON public.result USING btree (serp);


--
-- TOC entry 3157 (class 1259 OID 677450)
-- Name: idx_answer__participant; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_answer__participant ON public.answer USING btree (participant);


--
-- TOC entry 3158 (class 1259 OID 677451)
-- Name: idx_answer__question; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_answer__question ON public.answer USING btree (question);


--
-- TOC entry 3159 (class 1259 OID 677452)
-- Name: idx_answer__result; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_answer__result ON public.answer USING btree (result);


--
-- TOC entry 3160 (class 1259 OID 677453)
-- Name: idx_answer__study; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_answer__study ON public.answer USING btree (study);


--
-- TOC entry 3171 (class 1259 OID 677454)
-- Name: idx_content__result; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_content__result ON public.content USING btree (result);


--
-- TOC entry 3178 (class 1259 OID 677455)
-- Name: idx_evaluation__source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_evaluation__source ON public.evaluation USING btree (source);


--
-- TOC entry 3181 (class 1259 OID 677456)
-- Name: idx_experiment__study; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_experiment__study ON public.experiment USING btree (study);


--
-- TOC entry 3184 (class 1259 OID 677457)
-- Name: idx_incentive__participant; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_incentive__participant ON public.incentive USING btree (participant);


--
-- TOC entry 3185 (class 1259 OID 677458)
-- Name: idx_incentive__study; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_incentive__study ON public.incentive USING btree (study);


--
-- TOC entry 3190 (class 1259 OID 677459)
-- Name: idx_language_study; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_language_study ON public.language_study USING btree (study);


--
-- TOC entry 3195 (class 1259 OID 677460)
-- Name: idx_logger_query; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_logger_query ON public.logger_query USING btree (query);


--
-- TOC entry 3198 (class 1259 OID 677461)
-- Name: idx_logger_result; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_logger_result ON public.logger_result USING btree (result);


--
-- TOC entry 3201 (class 1259 OID 677462)
-- Name: idx_logger_scraper; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_logger_scraper ON public.logger_scraper USING btree (scraper);


--
-- TOC entry 3204 (class 1259 OID 677463)
-- Name: idx_logger_searchengine; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_logger_searchengine ON public.logger_searchengine USING btree (searchengine);


--
-- TOC entry 3207 (class 1259 OID 677464)
-- Name: idx_logger_serp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_logger_serp ON public.logger_serp USING btree (serp);


--
-- TOC entry 3212 (class 1259 OID 677465)
-- Name: idx_option__question; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_option__question ON public.option USING btree (question);


--
-- TOC entry 3215 (class 1259 OID 677466)
-- Name: idx_participant__group; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_participant__group ON public.participant USING btree ("group");


--
-- TOC entry 3218 (class 1259 OID 677467)
-- Name: idx_participant_study; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_participant_study ON public.participant_study USING btree (study);


--
-- TOC entry 3231 (class 1259 OID 677468)
-- Name: idx_query__study; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_query__study ON public.query USING btree (study);


--
-- TOC entry 3234 (class 1259 OID 677469)
-- Name: idx_question__question_template; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_question__question_template ON public.question USING btree (question_template);


--
-- TOC entry 3235 (class 1259 OID 677470)
-- Name: idx_question__question_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_question__question_type ON public.question USING btree (question_type);


--
-- TOC entry 3236 (class 1259 OID 677471)
-- Name: idx_question__study; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_question__study ON public.question USING btree (study);


--
-- TOC entry 3239 (class 1259 OID 677472)
-- Name: idx_question_result; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_question_result ON public.question_result USING btree (result);


--
-- TOC entry 3246 (class 1259 OID 677473)
-- Name: idx_reporting__scraper; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reporting__scraper ON public.reporting USING btree (scraper);


--
-- TOC entry 3251 (class 1259 OID 677474)
-- Name: idx_result__scraper; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_result__scraper ON public.result USING btree (scraper);


--
-- TOC entry 3252 (class 1259 OID 677475)
-- Name: idx_result__study; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_result__study ON public.result USING btree (study);


--
-- TOC entry 3261 (class 1259 OID 677476)
-- Name: idx_scraper__query; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scraper__query ON public.scraper USING btree (query);


--
-- TOC entry 3262 (class 1259 OID 677477)
-- Name: idx_scraper__search_engine; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scraper__search_engine ON public.scraper USING btree (searchengine);


--
-- TOC entry 3263 (class 1259 OID 677478)
-- Name: idx_scraper__study; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scraper__study ON public.scraper USING btree (study);


--
-- TOC entry 3268 (class 1259 OID 677479)
-- Name: idx_searchengine_study; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_searchengine_study ON public.searchengine_study USING btree (study);


--
-- TOC entry 3271 (class 1259 OID 677480)
-- Name: idx_serp__scraper; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_serp__scraper ON public.serp USING btree (scraper);


--
-- TOC entry 3276 (class 1259 OID 677481)
-- Name: idx_statistic__study; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_statistic__study ON public.statistic USING btree (study);


--
-- TOC entry 3279 (class 1259 OID 677482)
-- Name: idx_study__study_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_study__study_type ON public.study USING btree (studytype);


--
-- TOC entry 3282 (class 1259 OID 677483)
-- Name: idx_study_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_study_user ON public.study_user USING btree ("user");


--
-- TOC entry 3287 (class 1259 OID 677484)
-- Name: idx_task__logger; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_task__logger ON public.task USING btree (logger);


--
-- TOC entry 3300 (class 2606 OID 677485)
-- Name: classifier_study classifier_study_relation_2; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classifier_study
    ADD CONSTRAINT classifier_study_relation_2 FOREIGN KEY (study) REFERENCES public.study(id);


--
-- TOC entry 3292 (class 2606 OID 677490)
-- Name: answer fk_answer__participant; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.answer
    ADD CONSTRAINT fk_answer__participant FOREIGN KEY (participant) REFERENCES public.participant(id) ON DELETE SET NULL;


--
-- TOC entry 3293 (class 2606 OID 677495)
-- Name: answer fk_answer__question; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.answer
    ADD CONSTRAINT fk_answer__question FOREIGN KEY (question) REFERENCES public.question(id) ON DELETE SET NULL;


--
-- TOC entry 3294 (class 2606 OID 677500)
-- Name: answer fk_answer__result; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.answer
    ADD CONSTRAINT fk_answer__result FOREIGN KEY (result) REFERENCES public.result(id) ON DELETE SET NULL;


--
-- TOC entry 3295 (class 2606 OID 677505)
-- Name: answer fk_answer__study; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.answer
    ADD CONSTRAINT fk_answer__study FOREIGN KEY (study) REFERENCES public.study(id);


--
-- TOC entry 3298 (class 2606 OID 677510)
-- Name: classifier_result fk_classifier_result__classifier; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classifier_result
    ADD CONSTRAINT fk_classifier_result__classifier FOREIGN KEY (classifier) REFERENCES public.classifier(id) NOT VALID;


--
-- TOC entry 3299 (class 2606 OID 677515)
-- Name: classifier_result fk_classifier_result__result; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classifier_result
    ADD CONSTRAINT fk_classifier_result__result FOREIGN KEY (result) REFERENCES public.result(id) NOT VALID;


--
-- TOC entry 3301 (class 2606 OID 677520)
-- Name: classifier_study fk_classifier_study__classifier; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classifier_study
    ADD CONSTRAINT fk_classifier_study__classifier FOREIGN KEY (classifier) REFERENCES public.classifier(id) NOT VALID;


--
-- TOC entry 3302 (class 2606 OID 677525)
-- Name: content fk_content__result; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.content
    ADD CONSTRAINT fk_content__result FOREIGN KEY (result) REFERENCES public.result(id) ON DELETE SET NULL;


--
-- TOC entry 3303 (class 2606 OID 677530)
-- Name: country_monitoring fk_country_monitoring__country; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.country_monitoring
    ADD CONSTRAINT fk_country_monitoring__country FOREIGN KEY (country) REFERENCES public.country(id);


--
-- TOC entry 3304 (class 2606 OID 677535)
-- Name: country_monitoring fk_country_monitoring__monitoring; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.country_monitoring
    ADD CONSTRAINT fk_country_monitoring__monitoring FOREIGN KEY (monitoring) REFERENCES public.monitoring(id);


--
-- TOC entry 3305 (class 2606 OID 677540)
-- Name: evaluation fk_evaluation__source; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluation
    ADD CONSTRAINT fk_evaluation__source FOREIGN KEY (source) REFERENCES public.source(id) ON DELETE SET NULL;


--
-- TOC entry 3306 (class 2606 OID 677545)
-- Name: experiment fk_experiment__study; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.experiment
    ADD CONSTRAINT fk_experiment__study FOREIGN KEY (study) REFERENCES public.study(id) ON DELETE SET NULL;


--
-- TOC entry 3307 (class 2606 OID 677550)
-- Name: incentive fk_incentive__participant; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.incentive
    ADD CONSTRAINT fk_incentive__participant FOREIGN KEY (participant) REFERENCES public.participant(id) ON DELETE SET NULL;


--
-- TOC entry 3308 (class 2606 OID 677555)
-- Name: incentive fk_incentive__study; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.incentive
    ADD CONSTRAINT fk_incentive__study FOREIGN KEY (study) REFERENCES public.study(id) ON DELETE SET NULL;


--
-- TOC entry 3296 (class 2606 OID 677560)
-- Name: classifier_indicator fk_indicator__classifier; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classifier_indicator
    ADD CONSTRAINT fk_indicator__classifier FOREIGN KEY (classifier) REFERENCES public.classifier(id) NOT VALID;


--
-- TOC entry 3297 (class 2606 OID 677565)
-- Name: classifier_indicator fk_indicator__result; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classifier_indicator
    ADD CONSTRAINT fk_indicator__result FOREIGN KEY (result) REFERENCES public.result(id) NOT VALID;


--
-- TOC entry 3309 (class 2606 OID 677570)
-- Name: language_study fk_language_study__language; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.language_study
    ADD CONSTRAINT fk_language_study__language FOREIGN KEY (language) REFERENCES public.language(id);


--
-- TOC entry 3310 (class 2606 OID 677575)
-- Name: language_study fk_language_study__study; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.language_study
    ADD CONSTRAINT fk_language_study__study FOREIGN KEY (study) REFERENCES public.study(id);


--
-- TOC entry 3311 (class 2606 OID 677580)
-- Name: logger_query fk_logger_query__logger; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_query
    ADD CONSTRAINT fk_logger_query__logger FOREIGN KEY (logger) REFERENCES public.logger(id);


--
-- TOC entry 3312 (class 2606 OID 677585)
-- Name: logger_query fk_logger_query__query; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_query
    ADD CONSTRAINT fk_logger_query__query FOREIGN KEY (query) REFERENCES public.query(id);


--
-- TOC entry 3313 (class 2606 OID 677590)
-- Name: logger_result fk_logger_result__logger; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_result
    ADD CONSTRAINT fk_logger_result__logger FOREIGN KEY (logger) REFERENCES public.logger(id);


--
-- TOC entry 3314 (class 2606 OID 677595)
-- Name: logger_result fk_logger_result__result; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_result
    ADD CONSTRAINT fk_logger_result__result FOREIGN KEY (result) REFERENCES public.result(id);


--
-- TOC entry 3315 (class 2606 OID 677600)
-- Name: logger_scraper fk_logger_scraper__logger; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_scraper
    ADD CONSTRAINT fk_logger_scraper__logger FOREIGN KEY (logger) REFERENCES public.logger(id);


--
-- TOC entry 3316 (class 2606 OID 677605)
-- Name: logger_scraper fk_logger_scraper__scraper; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_scraper
    ADD CONSTRAINT fk_logger_scraper__scraper FOREIGN KEY (scraper) REFERENCES public.scraper(id);


--
-- TOC entry 3317 (class 2606 OID 677610)
-- Name: logger_searchengine fk_logger_searchengine__logger; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_searchengine
    ADD CONSTRAINT fk_logger_searchengine__logger FOREIGN KEY (logger) REFERENCES public.logger(id);


--
-- TOC entry 3318 (class 2606 OID 677615)
-- Name: logger_searchengine fk_logger_searchengine__searchengine; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_searchengine
    ADD CONSTRAINT fk_logger_searchengine__searchengine FOREIGN KEY (searchengine) REFERENCES public.searchengine(id);


--
-- TOC entry 3319 (class 2606 OID 677620)
-- Name: logger_serp fk_logger_serp__logger; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_serp
    ADD CONSTRAINT fk_logger_serp__logger FOREIGN KEY (logger) REFERENCES public.logger(id);


--
-- TOC entry 3320 (class 2606 OID 677625)
-- Name: logger_serp fk_logger_serp__serp; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logger_serp
    ADD CONSTRAINT fk_logger_serp__serp FOREIGN KEY (serp) REFERENCES public.serp(id);


--
-- TOC entry 3321 (class 2606 OID 677630)
-- Name: monitoring fk_monitoring__resulttype; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.monitoring
    ADD CONSTRAINT fk_monitoring__resulttype FOREIGN KEY (resulttype) REFERENCES public.resulttype(id) ON DELETE SET NULL;


--
-- TOC entry 3322 (class 2606 OID 677635)
-- Name: option fk_option__question; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.option
    ADD CONSTRAINT fk_option__question FOREIGN KEY (question) REFERENCES public.question(id) ON DELETE SET NULL;


--
-- TOC entry 3323 (class 2606 OID 677640)
-- Name: participant fk_participant__group; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.participant
    ADD CONSTRAINT fk_participant__group FOREIGN KEY ("group") REFERENCES public."group"(id) ON DELETE SET NULL;


--
-- TOC entry 3324 (class 2606 OID 677645)
-- Name: participant_study fk_participant_study__participant; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.participant_study
    ADD CONSTRAINT fk_participant_study__participant FOREIGN KEY (participant) REFERENCES public.participant(id);


--
-- TOC entry 3325 (class 2606 OID 677650)
-- Name: participant_study fk_participant_study__study; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.participant_study
    ADD CONSTRAINT fk_participant_study__study FOREIGN KEY (study) REFERENCES public.study(id);


--
-- TOC entry 3326 (class 2606 OID 677655)
-- Name: query fk_query__monitoring; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.query
    ADD CONSTRAINT fk_query__monitoring FOREIGN KEY (monitoring) REFERENCES public.monitoring(id) ON DELETE SET NULL;


--
-- TOC entry 3327 (class 2606 OID 677660)
-- Name: query fk_query__study; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.query
    ADD CONSTRAINT fk_query__study FOREIGN KEY (study) REFERENCES public.study(id) ON DELETE SET NULL;


--
-- TOC entry 3328 (class 2606 OID 677665)
-- Name: question fk_question__question_template; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question
    ADD CONSTRAINT fk_question__question_template FOREIGN KEY (question_template) REFERENCES public.questiontemplate(id) ON DELETE SET NULL;


--
-- TOC entry 3329 (class 2606 OID 677670)
-- Name: question fk_question__question_type; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question
    ADD CONSTRAINT fk_question__question_type FOREIGN KEY (question_type) REFERENCES public.questiontype(id) ON DELETE SET NULL;


--
-- TOC entry 3330 (class 2606 OID 677675)
-- Name: question fk_question__study; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question
    ADD CONSTRAINT fk_question__study FOREIGN KEY (study) REFERENCES public.study(id) ON DELETE SET NULL;


--
-- TOC entry 3331 (class 2606 OID 677680)
-- Name: question_result fk_question_result__question; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_result
    ADD CONSTRAINT fk_question_result__question FOREIGN KEY (question) REFERENCES public.question(id);


--
-- TOC entry 3332 (class 2606 OID 677685)
-- Name: question_result fk_question_result__result; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_result
    ADD CONSTRAINT fk_question_result__result FOREIGN KEY (result) REFERENCES public.result(id);


--
-- TOC entry 3333 (class 2606 OID 677690)
-- Name: reporting fk_reporting__scraper; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reporting
    ADD CONSTRAINT fk_reporting__scraper FOREIGN KEY (scraper) REFERENCES public.scraper(id) ON DELETE SET NULL;


--
-- TOC entry 3334 (class 2606 OID 677695)
-- Name: result fk_result__monitoring; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.result
    ADD CONSTRAINT fk_result__monitoring FOREIGN KEY (monitoring) REFERENCES public.monitoring(id);


--
-- TOC entry 3335 (class 2606 OID 677700)
-- Name: result fk_result__query; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.result
    ADD CONSTRAINT fk_result__query FOREIGN KEY (query) REFERENCES public.query(id) ON DELETE SET NULL;


--
-- TOC entry 3336 (class 2606 OID 677705)
-- Name: result fk_result__serp; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.result
    ADD CONSTRAINT fk_result__serp FOREIGN KEY (serp) REFERENCES public.serp(id) ON DELETE SET NULL;


--
-- TOC entry 3337 (class 2606 OID 677710)
-- Name: result fk_result__study; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.result
    ADD CONSTRAINT fk_result__study FOREIGN KEY (study) REFERENCES public.study(id) ON DELETE SET NULL;


--
-- TOC entry 3338 (class 2606 OID 677715)
-- Name: result fk_result_resulttype; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.result
    ADD CONSTRAINT fk_result_resulttype FOREIGN KEY (resulttype) REFERENCES public.resulttype(id);


--
-- TOC entry 3339 (class 2606 OID 677720)
-- Name: result fk_result_scraper; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.result
    ADD CONSTRAINT fk_result_scraper FOREIGN KEY (scraper) REFERENCES public.scraper(id) ON DELETE SET NULL;


--
-- TOC entry 3340 (class 2606 OID 677725)
-- Name: result_source fk_result_source__result; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.result_source
    ADD CONSTRAINT fk_result_source__result FOREIGN KEY (result) REFERENCES public.result(id);


--
-- TOC entry 3341 (class 2606 OID 677730)
-- Name: result_source fk_result_source__source; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.result_source
    ADD CONSTRAINT fk_result_source__source FOREIGN KEY (source) REFERENCES public.source(id);


--
-- TOC entry 3342 (class 2606 OID 677735)
-- Name: scraper fk_scraper__query; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scraper
    ADD CONSTRAINT fk_scraper__query FOREIGN KEY (query) REFERENCES public.query(id) ON DELETE SET NULL;


--
-- TOC entry 3343 (class 2606 OID 677740)
-- Name: scraper fk_scraper__search_engine; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scraper
    ADD CONSTRAINT fk_scraper__search_engine FOREIGN KEY (searchengine) REFERENCES public.searchengine(id) ON DELETE SET NULL;


--
-- TOC entry 3344 (class 2606 OID 677745)
-- Name: scraper fk_scraper__study; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scraper
    ADD CONSTRAINT fk_scraper__study FOREIGN KEY (study) REFERENCES public.study(id) ON DELETE SET NULL;


--
-- TOC entry 3345 (class 2606 OID 677750)
-- Name: searchengine_study fk_searchengine_study__searchengine; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.searchengine_study
    ADD CONSTRAINT fk_searchengine_study__searchengine FOREIGN KEY (searchengine) REFERENCES public.searchengine(id);


--
-- TOC entry 3346 (class 2606 OID 677755)
-- Name: searchengine_study fk_searchengine_study__study; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.searchengine_study
    ADD CONSTRAINT fk_searchengine_study__study FOREIGN KEY (study) REFERENCES public.study(id);


--
-- TOC entry 3347 (class 2606 OID 677760)
-- Name: serp fk_serp__monitoring; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.serp
    ADD CONSTRAINT fk_serp__monitoring FOREIGN KEY (monitoring) REFERENCES public.monitoring(id) ON DELETE SET NULL;


--
-- TOC entry 3348 (class 2606 OID 677765)
-- Name: serp fk_serp__query; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.serp
    ADD CONSTRAINT fk_serp__query FOREIGN KEY (query) REFERENCES public.query(id) ON DELETE SET NULL;


--
-- TOC entry 3349 (class 2606 OID 677770)
-- Name: serp fk_serp__scraper; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.serp
    ADD CONSTRAINT fk_serp__scraper FOREIGN KEY (scraper) REFERENCES public.scraper(id) ON DELETE SET NULL;


--
-- TOC entry 3350 (class 2606 OID 677775)
-- Name: statistic fk_statistic__study; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.statistic
    ADD CONSTRAINT fk_statistic__study FOREIGN KEY (study) REFERENCES public.study(id) ON DELETE SET NULL;


--
-- TOC entry 3351 (class 2606 OID 677780)
-- Name: study fk_study__result_type; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study
    ADD CONSTRAINT fk_study__result_type FOREIGN KEY (resulttype) REFERENCES public.resulttype(id) ON DELETE SET NULL;


--
-- TOC entry 3352 (class 2606 OID 677785)
-- Name: study fk_study__study_type; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study
    ADD CONSTRAINT fk_study__study_type FOREIGN KEY (studytype) REFERENCES public.studytype(id) ON DELETE SET NULL;


--
-- TOC entry 3353 (class 2606 OID 677790)
-- Name: study_user fk_study_user__study; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_user
    ADD CONSTRAINT fk_study_user__study FOREIGN KEY (study) REFERENCES public.study(id);


--
-- TOC entry 3354 (class 2606 OID 677795)
-- Name: study_user fk_study_user__user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_user
    ADD CONSTRAINT fk_study_user__user FOREIGN KEY ("user") REFERENCES public."user"(id);


--
-- TOC entry 3355 (class 2606 OID 677800)
-- Name: task fk_task__logger; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task
    ADD CONSTRAINT fk_task__logger FOREIGN KEY (logger) REFERENCES public.logger(id) ON DELETE SET NULL;


--
-- TOC entry 3356 (class 2606 OID 677805)
-- Name: user_role user_role_relation_1; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_role
    ADD CONSTRAINT user_role_relation_1 FOREIGN KEY ("user") REFERENCES public."user"(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- TOC entry 3357 (class 2606 OID 677810)
-- Name: user_role user_role_relation_2; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_role
    ADD CONSTRAINT user_role_relation_2 FOREIGN KEY (role) REFERENCES public.role(id) ON UPDATE CASCADE ON DELETE CASCADE;


-- Completed on 2024-08-06 11:18:03

--
-- PostgreSQL database dump complete
--

