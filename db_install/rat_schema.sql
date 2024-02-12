PGDMP      ,            
    {            rat3    11.20 (Debian 11.20-0+deb10u1)    16.0 1   X           0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                      false            Y           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                      false            Z           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                      false            [           1262    331697    rat3    DATABASE     p   CREATE DATABASE rat3 WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'de_DE.UTF-8';
    DROP DATABASE rat3;
                rat    false                        2615    2200    public    SCHEMA     2   -- *not* creating schema, since initdb creates it
 2   -- *not* dropping schema, since initdb creates it
                postgres    false            \           0    0    SCHEMA public    ACL     Q   REVOKE USAGE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO PUBLIC;
                   postgres    false    6            �            1259    331698    answer    TABLE       CREATE TABLE public.answer (
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
    DROP TABLE public.answer;
       public            rat    false    6            �            1259    331704    answer_id_seq    SEQUENCE     �   CREATE SEQUENCE public.answer_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 $   DROP SEQUENCE public.answer_id_seq;
       public          rat    false    196    6            ]           0    0    answer_id_seq    SEQUENCE OWNED BY     ?   ALTER SEQUENCE public.answer_id_seq OWNED BY public.answer.id;
          public          rat    false    197                       1259    332452 
   classifier    TABLE     }   CREATE TABLE public.classifier (
    id integer NOT NULL,
    name text NOT NULL,
    display_name character varying(255)
);
    DROP TABLE public.classifier;
       public            rat    false    6                       1259    332450    classifier_id_seq    SEQUENCE     �   CREATE SEQUENCE public.classifier_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 (   DROP SEQUENCE public.classifier_id_seq;
       public          rat    false    6    269            ^           0    0    classifier_id_seq    SEQUENCE OWNED BY     G   ALTER SEQUENCE public.classifier_id_seq OWNED BY public.classifier.id;
          public          rat    false    268                       1259    332463    classifier_indicator    TABLE     �   CREATE TABLE public.classifier_indicator (
    id integer NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    indicator text,
    value text,
    result integer NOT NULL,
    classifier integer NOT NULL
);
 (   DROP TABLE public.classifier_indicator;
       public            rat    false    6                       1259    332461    classifier_indicator_id_seq    SEQUENCE     �   CREATE SEQUENCE public.classifier_indicator_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 2   DROP SEQUENCE public.classifier_indicator_id_seq;
       public          rat    false    271    6            _           0    0    classifier_indicator_id_seq    SEQUENCE OWNED BY     [   ALTER SEQUENCE public.classifier_indicator_id_seq OWNED BY public.classifier_indicator.id;
          public          rat    false    270                       1259    332475    classifier_result    TABLE     �   CREATE TABLE public.classifier_result (
    id integer NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    value text,
    result integer,
    classifier integer
);
 %   DROP TABLE public.classifier_result;
       public            rat    false    6                       1259    332473    classifier_result_id_seq    SEQUENCE     �   CREATE SEQUENCE public.classifier_result_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 /   DROP SEQUENCE public.classifier_result_id_seq;
       public          rat    false    273    6            `           0    0    classifier_result_id_seq    SEQUENCE OWNED BY     U   ALTER SEQUENCE public.classifier_result_id_seq OWNED BY public.classifier_result.id;
          public          rat    false    272                       1259    332485    classifier_study_id_seq    SEQUENCE     �   CREATE SEQUENCE public.classifier_study_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 .   DROP SEQUENCE public.classifier_study_id_seq;
       public          rat    false    6                       1259    332487    classifier_study    TABLE     �   CREATE TABLE public.classifier_study (
    id integer DEFAULT nextval('public.classifier_study_id_seq'::regclass) NOT NULL,
    classifier integer,
    study integer
);
 $   DROP TABLE public.classifier_study;
       public            rat    false    274    6            �            1259    331722    content    TABLE     ]   CREATE TABLE public.content (
    id integer NOT NULL,
    result integer,
    value text
);
    DROP TABLE public.content;
       public            rat    false    6            �            1259    331728    content_id_seq    SEQUENCE     �   CREATE SEQUENCE public.content_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 %   DROP SEQUENCE public.content_id_seq;
       public          rat    false    6    198            a           0    0    content_id_seq    SEQUENCE OWNED BY     A   ALTER SEQUENCE public.content_id_seq OWNED BY public.content.id;
          public          rat    false    199            �            1259    331730    country    TABLE     m   CREATE TABLE public.country (
    id integer NOT NULL,
    name text,
    code text,
    language integer
);
    DROP TABLE public.country;
       public            rat    false    6            �            1259    331736    country_id_seq    SEQUENCE     �   CREATE SEQUENCE public.country_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 %   DROP SEQUENCE public.country_id_seq;
       public          rat    false    200    6            b           0    0    country_id_seq    SEQUENCE OWNED BY     A   ALTER SEQUENCE public.country_id_seq OWNED BY public.country.id;
          public          rat    false    201            �            1259    331738    country_monitoring    TABLE     X   CREATE TABLE public.country_monitoring (
    country integer,
    monitoring integer
);
 &   DROP TABLE public.country_monitoring;
       public            rat    false    6            �            1259    331741    dummy_table    TABLE     �   CREATE TABLE public.dummy_table (
    id integer NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    name text,
    description text
);
    DROP TABLE public.dummy_table;
       public            rat    false    6            �            1259    331748    dummy_table_id_seq    SEQUENCE     �   CREATE SEQUENCE public.dummy_table_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 )   DROP SEQUENCE public.dummy_table_id_seq;
       public          rat    false    203    6            c           0    0    dummy_table_id_seq    SEQUENCE OWNED BY     I   ALTER SEQUENCE public.dummy_table_id_seq OWNED BY public.dummy_table.id;
          public          rat    false    204            �            1259    331750 
   evaluation    TABLE     v   CREATE TABLE public.evaluation (
    id integer NOT NULL,
    source integer,
    comment text,
    status integer
);
    DROP TABLE public.evaluation;
       public            rat    false    6            �            1259    331756    evaluation_id_seq    SEQUENCE     �   CREATE SEQUENCE public.evaluation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 (   DROP SEQUENCE public.evaluation_id_seq;
       public          rat    false    6    205            d           0    0    evaluation_id_seq    SEQUENCE OWNED BY     G   ALTER SEQUENCE public.evaluation_id_seq OWNED BY public.evaluation.id;
          public          rat    false    206            �            1259    331758 
   experiment    TABLE     O   CREATE TABLE public.experiment (
    id integer NOT NULL,
    study integer
);
    DROP TABLE public.experiment;
       public            rat    false    6            �            1259    331761    experiment_id_seq    SEQUENCE     �   CREATE SEQUENCE public.experiment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 (   DROP SEQUENCE public.experiment_id_seq;
       public          rat    false    6    207            e           0    0    experiment_id_seq    SEQUENCE OWNED BY     G   ALTER SEQUENCE public.experiment_id_seq OWNED BY public.experiment.id;
          public          rat    false    208            �            1259    331763    group    TABLE     ^   CREATE TABLE public."group" (
    id integer NOT NULL,
    name text,
    description text
);
    DROP TABLE public."group";
       public            rat    false    6            �            1259    331769    group_id_seq    SEQUENCE     �   CREATE SEQUENCE public.group_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 #   DROP SEQUENCE public.group_id_seq;
       public          rat    false    6    209            f           0    0    group_id_seq    SEQUENCE OWNED BY     ?   ALTER SEQUENCE public.group_id_seq OWNED BY public."group".id;
          public          rat    false    210            �            1259    331771 	   incentive    TABLE     g   CREATE TABLE public.incentive (
    id integer NOT NULL,
    study integer,
    participant integer
);
    DROP TABLE public.incentive;
       public            rat    false    6            �            1259    331774    incentive_id_seq    SEQUENCE     �   CREATE SEQUENCE public.incentive_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 '   DROP SEQUENCE public.incentive_id_seq;
       public          rat    false    211    6            g           0    0    incentive_id_seq    SEQUENCE OWNED BY     E   ALTER SEQUENCE public.incentive_id_seq OWNED BY public.incentive.id;
          public          rat    false    212            �            1259    331776    language    TABLE     }   CREATE TABLE public.language (
    id integer NOT NULL,
    name text,
    code text,
    translate boolean DEFAULT false
);
    DROP TABLE public.language;
       public            rat    false    6            �            1259    331783    language_id_seq    SEQUENCE     �   CREATE SEQUENCE public.language_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 &   DROP SEQUENCE public.language_id_seq;
       public          rat    false    6    213            h           0    0    language_id_seq    SEQUENCE OWNED BY     C   ALTER SEQUENCE public.language_id_seq OWNED BY public.language.id;
          public          rat    false    214            �            1259    331785    language_study    TABLE     b   CREATE TABLE public.language_study (
    language integer NOT NULL,
    study integer NOT NULL
);
 "   DROP TABLE public.language_study;
       public            rat    false    6            �            1259    331788    logger    TABLE     _   CREATE TABLE public.logger (
    id integer NOT NULL,
    clicked boolean,
    "limit" text
);
    DROP TABLE public.logger;
       public            rat    false    6            �            1259    331794    logger_id_seq    SEQUENCE     �   CREATE SEQUENCE public.logger_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 $   DROP SEQUENCE public.logger_id_seq;
       public          rat    false    6    216            i           0    0    logger_id_seq    SEQUENCE OWNED BY     ?   ALTER SEQUENCE public.logger_id_seq OWNED BY public.logger.id;
          public          rat    false    217            �            1259    331796    logger_query    TABLE     ^   CREATE TABLE public.logger_query (
    logger integer NOT NULL,
    query integer NOT NULL
);
     DROP TABLE public.logger_query;
       public            rat    false    6            �            1259    331799    logger_result    TABLE     `   CREATE TABLE public.logger_result (
    logger integer NOT NULL,
    result integer NOT NULL
);
 !   DROP TABLE public.logger_result;
       public            rat    false    6            �            1259    331802    logger_scraper    TABLE     b   CREATE TABLE public.logger_scraper (
    logger integer NOT NULL,
    scraper integer NOT NULL
);
 "   DROP TABLE public.logger_scraper;
       public            rat    false    6            �            1259    331805    logger_searchengine    TABLE     l   CREATE TABLE public.logger_searchengine (
    logger integer NOT NULL,
    searchengine integer NOT NULL
);
 '   DROP TABLE public.logger_searchengine;
       public            rat    false    6            �            1259    331808    logger_serp    TABLE     \   CREATE TABLE public.logger_serp (
    logger integer NOT NULL,
    serp integer NOT NULL
);
    DROP TABLE public.logger_serp;
       public            rat    false    6            �            1259    331811 
   monitoring    TABLE       CREATE TABLE public.monitoring (
    id integer NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    name text,
    description text,
    interval_mode integer,
    interval_frequency integer,
    result_count integer,
    resulttype integer
);
    DROP TABLE public.monitoring;
       public            rat    false    6            �            1259    331818    monitoring_id_seq    SEQUENCE     �   CREATE SEQUENCE public.monitoring_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 (   DROP SEQUENCE public.monitoring_id_seq;
       public          rat    false    6    223            j           0    0    monitoring_id_seq    SEQUENCE OWNED BY     G   ALTER SEQUENCE public.monitoring_id_seq OWNED BY public.monitoring.id;
          public          rat    false    224            �            1259    331820    option    TABLE     �   CREATE TABLE public.option (
    id integer NOT NULL,
    value text,
    label text,
    "position" integer,
    question integer
);
    DROP TABLE public.option;
       public            rat    false    6            �            1259    331826    option_id_seq    SEQUENCE     �   CREATE SEQUENCE public.option_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 $   DROP SEQUENCE public.option_id_seq;
       public          rat    false    6    225            k           0    0    option_id_seq    SEQUENCE OWNED BY     ?   ALTER SEQUENCE public.option_id_seq OWNED BY public.option.id;
          public          rat    false    226            �            1259    331828    participant    TABLE     �   CREATE TABLE public.participant (
    id integer NOT NULL,
    "group" integer,
    name text,
    created_at timestamp(6) without time zone,
    updated_at timestamp(6) without time zone,
    password integer
);
    DROP TABLE public.participant;
       public            rat    false    6            �            1259    331834    participant_id_seq    SEQUENCE     �   CREATE SEQUENCE public.participant_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 )   DROP SEQUENCE public.participant_id_seq;
       public          rat    false    227    6            l           0    0    participant_id_seq    SEQUENCE OWNED BY     I   ALTER SEQUENCE public.participant_id_seq OWNED BY public.participant.id;
          public          rat    false    228            �            1259    331836    participant_study    TABLE     h   CREATE TABLE public.participant_study (
    participant integer NOT NULL,
    study integer NOT NULL
);
 %   DROP TABLE public.participant_study;
       public            rat    false    6            �            1259    331839    query    TABLE     �   CREATE TABLE public.query (
    id integer NOT NULL,
    query text,
    created_at timestamp without time zone,
    study integer,
    description text,
    "limit" integer,
    monitoring integer
);
    DROP TABLE public.query;
       public            rat    false    6            �            1259    331845    query_id_seq    SEQUENCE     �   CREATE SEQUENCE public.query_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 #   DROP SEQUENCE public.query_id_seq;
       public          rat    false    6    230            m           0    0    query_id_seq    SEQUENCE OWNED BY     =   ALTER SEQUENCE public.query_id_seq OWNED BY public.query.id;
          public          rat    false    231            �            1259    331847    question    TABLE     �   CREATE TABLE public.question (
    id integer NOT NULL,
    study integer,
    title text,
    description text,
    question_type integer,
    question_template integer,
    "position" integer,
    "interval" integer
);
    DROP TABLE public.question;
       public            rat    false    6            �            1259    331853    question_id_seq    SEQUENCE     �   CREATE SEQUENCE public.question_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 &   DROP SEQUENCE public.question_id_seq;
       public          rat    false    232    6            n           0    0    question_id_seq    SEQUENCE OWNED BY     C   ALTER SEQUENCE public.question_id_seq OWNED BY public.question.id;
          public          rat    false    233            �            1259    331855    question_result    TABLE     d   CREATE TABLE public.question_result (
    question integer NOT NULL,
    result integer NOT NULL
);
 #   DROP TABLE public.question_result;
       public            rat    false    6            �            1259    331858    questiontemplate    TABLE     g   CREATE TABLE public.questiontemplate (
    id integer NOT NULL,
    name text,
    description text
);
 $   DROP TABLE public.questiontemplate;
       public            rat    false    6            �            1259    331864    questiontemplate_id_seq    SEQUENCE     �   CREATE SEQUENCE public.questiontemplate_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 .   DROP SEQUENCE public.questiontemplate_id_seq;
       public          rat    false    6    235            o           0    0    questiontemplate_id_seq    SEQUENCE OWNED BY     S   ALTER SEQUENCE public.questiontemplate_id_seq OWNED BY public.questiontemplate.id;
          public          rat    false    236            �            1259    331866    questiontype    TABLE     _   CREATE TABLE public.questiontype (
    id integer NOT NULL,
    name text,
    display text
);
     DROP TABLE public.questiontype;
       public            rat    false    6            �            1259    331872    questiontype_id_seq    SEQUENCE     �   CREATE SEQUENCE public.questiontype_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 *   DROP SEQUENCE public.questiontype_id_seq;
       public          rat    false    237    6            p           0    0    questiontype_id_seq    SEQUENCE OWNED BY     K   ALTER SEQUENCE public.questiontype_id_seq OWNED BY public.questiontype.id;
          public          rat    false    238            �            1259    331874 	   reporting    TABLE       CREATE TABLE public.reporting (
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
    DROP TABLE public.reporting;
       public            rat    false    6            �            1259    331880    reporting_id_seq    SEQUENCE     �   CREATE SEQUENCE public.reporting_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 '   DROP SEQUENCE public.reporting_id_seq;
       public          rat    false    239    6            q           0    0    reporting_id_seq    SEQUENCE OWNED BY     E   ALTER SEQUENCE public.reporting_id_seq OWNED BY public.reporting.id;
          public          rat    false    240            �            1259    331882    result    TABLE     �  CREATE TABLE public.result (
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
    DROP TABLE public.result;
       public            rat    false    6            �            1259    331888    result_id_seq    SEQUENCE     �   CREATE SEQUENCE public.result_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 $   DROP SEQUENCE public.result_id_seq;
       public          rat    false    6    241            r           0    0    result_id_seq    SEQUENCE OWNED BY     ?   ALTER SEQUENCE public.result_id_seq OWNED BY public.result.id;
          public          rat    false    242                       1259    332523    result_source    TABLE     �   CREATE TABLE public.result_source (
    result integer,
    source integer,
    progress integer,
    id integer NOT NULL,
    counter integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone,
    error_code text,
    job_server text
);
 !   DROP TABLE public.result_source;
       public            rat    false    6                       1259    335446    result_source_id_seq    SEQUENCE     �   CREATE SEQUENCE public.result_source_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 +   DROP SEQUENCE public.result_source_id_seq;
       public          rat    false    276    6            s           0    0    result_source_id_seq    SEQUENCE OWNED BY     M   ALTER SEQUENCE public.result_source_id_seq OWNED BY public.result_source.id;
          public          rat    false    277            �            1259    331890 
   resulttype    TABLE     ]   CREATE TABLE public.resulttype (
    id integer NOT NULL,
    name text,
    display text
);
    DROP TABLE public.resulttype;
       public            rat    false    6            �            1259    331896    resulttype_id_seq    SEQUENCE     �   CREATE SEQUENCE public.resulttype_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 (   DROP SEQUENCE public.resulttype_id_seq;
       public          rat    false    243    6            t           0    0    resulttype_id_seq    SEQUENCE OWNED BY     G   ALTER SEQUENCE public.resulttype_id_seq OWNED BY public.resulttype.id;
          public          rat    false    244            �            1259    331898    role    TABLE     �   CREATE TABLE public.role (
    id integer NOT NULL,
    name text,
    description text,
    permissions text,
    update_datetime timestamp(6) without time zone
);
    DROP TABLE public.role;
       public            rat    false    6            �            1259    331904    role_id_seq    SEQUENCE     �   CREATE SEQUENCE public.role_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 "   DROP SEQUENCE public.role_id_seq;
       public          rat    false    6    245            u           0    0    role_id_seq    SEQUENCE OWNED BY     ;   ALTER SEQUENCE public.role_id_seq OWNED BY public.role.id;
          public          rat    false    246            �            1259    331906    scraper    TABLE     $  CREATE TABLE public.scraper (
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
    DROP TABLE public.scraper;
       public            rat    false    6            �            1259    331909    scraper_id_seq    SEQUENCE     �   CREATE SEQUENCE public.scraper_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 %   DROP SEQUENCE public.scraper_id_seq;
       public          rat    false    6    247            v           0    0    scraper_id_seq    SEQUENCE OWNED BY     A   ALTER SEQUENCE public.scraper_id_seq OWNED BY public.scraper.id;
          public          rat    false    248            �            1259    331911    searchengine    TABLE     �   CREATE TABLE public.searchengine (
    id integer NOT NULL,
    name text,
    module text,
    test integer,
    error_code text,
    resulttype integer,
    country text
);
     DROP TABLE public.searchengine;
       public            rat    false    6            �            1259    331917    searchengine_id_seq    SEQUENCE     �   CREATE SEQUENCE public.searchengine_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 *   DROP SEQUENCE public.searchengine_id_seq;
       public          rat    false    6    249            w           0    0    searchengine_id_seq    SEQUENCE OWNED BY     K   ALTER SEQUENCE public.searchengine_id_seq OWNED BY public.searchengine.id;
          public          rat    false    250            �            1259    331919    searchengine_study    TABLE     j   CREATE TABLE public.searchengine_study (
    searchengine integer NOT NULL,
    study integer NOT NULL
);
 &   DROP TABLE public.searchengine_study;
       public            rat    false    6            �            1259    331922    serp    TABLE     �   CREATE TABLE public.serp (
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
    DROP TABLE public.serp;
       public            rat    false    6            �            1259    331928    serp_id_seq    SEQUENCE     �   CREATE SEQUENCE public.serp_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 "   DROP SEQUENCE public.serp_id_seq;
       public          rat    false    6    252            x           0    0    serp_id_seq    SEQUENCE OWNED BY     ;   ALTER SEQUENCE public.serp_id_seq OWNED BY public.serp.id;
          public          rat    false    253            �            1259    331930    source    TABLE       CREATE TABLE public.source (
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
    DROP TABLE public.source;
       public            rat    false    6            �            1259    331936    source_id_seq    SEQUENCE     �   CREATE SEQUENCE public.source_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 $   DROP SEQUENCE public.source_id_seq;
       public          rat    false    254    6            y           0    0    source_id_seq    SEQUENCE OWNED BY     ?   ALTER SEQUENCE public.source_id_seq OWNED BY public.source.id;
          public          rat    false    255                        1259    331938 	   statistic    TABLE     m   CREATE TABLE public.statistic (
    id integer NOT NULL,
    study integer,
    name text,
    value text
);
    DROP TABLE public.statistic;
       public            rat    false    6                       1259    331944    statistic_id_seq    SEQUENCE     �   CREATE SEQUENCE public.statistic_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 '   DROP SEQUENCE public.statistic_id_seq;
       public          rat    false    256    6            z           0    0    statistic_id_seq    SEQUENCE OWNED BY     E   ALTER SEQUENCE public.statistic_id_seq OWNED BY public.statistic.id;
          public          rat    false    257                       1259    331946    study    TABLE     P  CREATE TABLE public.study (
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
    DROP TABLE public.study;
       public            rat    false    6                       1259    331952    study_id_seq    SEQUENCE     �   CREATE SEQUENCE public.study_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 #   DROP SEQUENCE public.study_id_seq;
       public          rat    false    258    6            {           0    0    study_id_seq    SEQUENCE OWNED BY     =   ALTER SEQUENCE public.study_id_seq OWNED BY public.study.id;
          public          rat    false    259                       1259    331954 
   study_user    TABLE     \   CREATE TABLE public.study_user (
    study integer NOT NULL,
    "user" integer NOT NULL
);
    DROP TABLE public.study_user;
       public            rat    false    6                       1259    331957 	   studytype    TABLE     J   CREATE TABLE public.studytype (
    id integer NOT NULL,
    name text
);
    DROP TABLE public.studytype;
       public            rat    false    6                       1259    331963    studytype_id_seq    SEQUENCE     �   CREATE SEQUENCE public.studytype_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 '   DROP SEQUENCE public.studytype_id_seq;
       public          rat    false    261    6            |           0    0    studytype_id_seq    SEQUENCE OWNED BY     E   ALTER SEQUENCE public.studytype_id_seq OWNED BY public.studytype.id;
          public          rat    false    262                       1259    331965    task    TABLE     J   CREATE TABLE public.task (
    id integer NOT NULL,
    logger integer
);
    DROP TABLE public.task;
       public            rat    false    6                       1259    331968    task_id_seq    SEQUENCE     �   CREATE SEQUENCE public.task_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 "   DROP SEQUENCE public.task_id_seq;
       public          rat    false    6    263            }           0    0    task_id_seq    SEQUENCE OWNED BY     ;   ALTER SEQUENCE public.task_id_seq OWNED BY public.task.id;
          public          rat    false    264            	           1259    331970    user    TABLE     �  CREATE TABLE public."user" (
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
    DROP TABLE public."user";
       public            rat    false    6            
           1259    331976    user_id_seq    SEQUENCE     �   CREATE SEQUENCE public.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 "   DROP SEQUENCE public.user_id_seq;
       public          rat    false    6    265            ~           0    0    user_id_seq    SEQUENCE OWNED BY     =   ALTER SEQUENCE public.user_id_seq OWNED BY public."user".id;
          public          rat    false    266                       1259    331978 	   user_role    TABLE     H   CREATE TABLE public.user_role (
    "user" integer,
    role integer
);
    DROP TABLE public.user_role;
       public            rat    false    6            �           2604    331981 	   answer id    DEFAULT     f   ALTER TABLE ONLY public.answer ALTER COLUMN id SET DEFAULT nextval('public.answer_id_seq'::regclass);
 8   ALTER TABLE public.answer ALTER COLUMN id DROP DEFAULT;
       public          rat    false    197    196                       2604    332455    classifier id    DEFAULT     n   ALTER TABLE ONLY public.classifier ALTER COLUMN id SET DEFAULT nextval('public.classifier_id_seq'::regclass);
 <   ALTER TABLE public.classifier ALTER COLUMN id DROP DEFAULT;
       public          rat    false    268    269    269                       2604    332466    classifier_indicator id    DEFAULT     �   ALTER TABLE ONLY public.classifier_indicator ALTER COLUMN id SET DEFAULT nextval('public.classifier_indicator_id_seq'::regclass);
 F   ALTER TABLE public.classifier_indicator ALTER COLUMN id DROP DEFAULT;
       public          rat    false    270    271    271                       2604    332478    classifier_result id    DEFAULT     |   ALTER TABLE ONLY public.classifier_result ALTER COLUMN id SET DEFAULT nextval('public.classifier_result_id_seq'::regclass);
 C   ALTER TABLE public.classifier_result ALTER COLUMN id DROP DEFAULT;
       public          rat    false    272    273    273            �           2604    331984 
   content id    DEFAULT     h   ALTER TABLE ONLY public.content ALTER COLUMN id SET DEFAULT nextval('public.content_id_seq'::regclass);
 9   ALTER TABLE public.content ALTER COLUMN id DROP DEFAULT;
       public          rat    false    199    198            �           2604    331985 
   country id    DEFAULT     h   ALTER TABLE ONLY public.country ALTER COLUMN id SET DEFAULT nextval('public.country_id_seq'::regclass);
 9   ALTER TABLE public.country ALTER COLUMN id DROP DEFAULT;
       public          rat    false    201    200            �           2604    331986    dummy_table id    DEFAULT     p   ALTER TABLE ONLY public.dummy_table ALTER COLUMN id SET DEFAULT nextval('public.dummy_table_id_seq'::regclass);
 =   ALTER TABLE public.dummy_table ALTER COLUMN id DROP DEFAULT;
       public          rat    false    204    203            �           2604    331987    evaluation id    DEFAULT     n   ALTER TABLE ONLY public.evaluation ALTER COLUMN id SET DEFAULT nextval('public.evaluation_id_seq'::regclass);
 <   ALTER TABLE public.evaluation ALTER COLUMN id DROP DEFAULT;
       public          rat    false    206    205            �           2604    331988    experiment id    DEFAULT     n   ALTER TABLE ONLY public.experiment ALTER COLUMN id SET DEFAULT nextval('public.experiment_id_seq'::regclass);
 <   ALTER TABLE public.experiment ALTER COLUMN id DROP DEFAULT;
       public          rat    false    208    207            �           2604    331989    group id    DEFAULT     f   ALTER TABLE ONLY public."group" ALTER COLUMN id SET DEFAULT nextval('public.group_id_seq'::regclass);
 9   ALTER TABLE public."group" ALTER COLUMN id DROP DEFAULT;
       public          rat    false    210    209            �           2604    331990    incentive id    DEFAULT     l   ALTER TABLE ONLY public.incentive ALTER COLUMN id SET DEFAULT nextval('public.incentive_id_seq'::regclass);
 ;   ALTER TABLE public.incentive ALTER COLUMN id DROP DEFAULT;
       public          rat    false    212    211            �           2604    331991    language id    DEFAULT     j   ALTER TABLE ONLY public.language ALTER COLUMN id SET DEFAULT nextval('public.language_id_seq'::regclass);
 :   ALTER TABLE public.language ALTER COLUMN id DROP DEFAULT;
       public          rat    false    214    213            �           2604    331992 	   logger id    DEFAULT     f   ALTER TABLE ONLY public.logger ALTER COLUMN id SET DEFAULT nextval('public.logger_id_seq'::regclass);
 8   ALTER TABLE public.logger ALTER COLUMN id DROP DEFAULT;
       public          rat    false    217    216            �           2604    331993    monitoring id    DEFAULT     n   ALTER TABLE ONLY public.monitoring ALTER COLUMN id SET DEFAULT nextval('public.monitoring_id_seq'::regclass);
 <   ALTER TABLE public.monitoring ALTER COLUMN id DROP DEFAULT;
       public          rat    false    224    223                        2604    331994 	   option id    DEFAULT     f   ALTER TABLE ONLY public.option ALTER COLUMN id SET DEFAULT nextval('public.option_id_seq'::regclass);
 8   ALTER TABLE public.option ALTER COLUMN id DROP DEFAULT;
       public          rat    false    226    225                       2604    331995    participant id    DEFAULT     p   ALTER TABLE ONLY public.participant ALTER COLUMN id SET DEFAULT nextval('public.participant_id_seq'::regclass);
 =   ALTER TABLE public.participant ALTER COLUMN id DROP DEFAULT;
       public          rat    false    228    227                       2604    331996    query id    DEFAULT     d   ALTER TABLE ONLY public.query ALTER COLUMN id SET DEFAULT nextval('public.query_id_seq'::regclass);
 7   ALTER TABLE public.query ALTER COLUMN id DROP DEFAULT;
       public          rat    false    231    230                       2604    331997    question id    DEFAULT     j   ALTER TABLE ONLY public.question ALTER COLUMN id SET DEFAULT nextval('public.question_id_seq'::regclass);
 :   ALTER TABLE public.question ALTER COLUMN id DROP DEFAULT;
       public          rat    false    233    232                       2604    331998    questiontemplate id    DEFAULT     z   ALTER TABLE ONLY public.questiontemplate ALTER COLUMN id SET DEFAULT nextval('public.questiontemplate_id_seq'::regclass);
 B   ALTER TABLE public.questiontemplate ALTER COLUMN id DROP DEFAULT;
       public          rat    false    236    235                       2604    331999    questiontype id    DEFAULT     r   ALTER TABLE ONLY public.questiontype ALTER COLUMN id SET DEFAULT nextval('public.questiontype_id_seq'::regclass);
 >   ALTER TABLE public.questiontype ALTER COLUMN id DROP DEFAULT;
       public          rat    false    238    237                       2604    332000    reporting id    DEFAULT     l   ALTER TABLE ONLY public.reporting ALTER COLUMN id SET DEFAULT nextval('public.reporting_id_seq'::regclass);
 ;   ALTER TABLE public.reporting ALTER COLUMN id DROP DEFAULT;
       public          rat    false    240    239                       2604    332001 	   result id    DEFAULT     f   ALTER TABLE ONLY public.result ALTER COLUMN id SET DEFAULT nextval('public.result_id_seq'::regclass);
 8   ALTER TABLE public.result ALTER COLUMN id DROP DEFAULT;
       public          rat    false    242    241                       2604    335448    result_source id    DEFAULT     t   ALTER TABLE ONLY public.result_source ALTER COLUMN id SET DEFAULT nextval('public.result_source_id_seq'::regclass);
 ?   ALTER TABLE public.result_source ALTER COLUMN id DROP DEFAULT;
       public          rat    false    277    276                       2604    332002    resulttype id    DEFAULT     n   ALTER TABLE ONLY public.resulttype ALTER COLUMN id SET DEFAULT nextval('public.resulttype_id_seq'::regclass);
 <   ALTER TABLE public.resulttype ALTER COLUMN id DROP DEFAULT;
       public          rat    false    244    243            	           2604    332003    role id    DEFAULT     b   ALTER TABLE ONLY public.role ALTER COLUMN id SET DEFAULT nextval('public.role_id_seq'::regclass);
 6   ALTER TABLE public.role ALTER COLUMN id DROP DEFAULT;
       public          rat    false    246    245            
           2604    332004 
   scraper id    DEFAULT     h   ALTER TABLE ONLY public.scraper ALTER COLUMN id SET DEFAULT nextval('public.scraper_id_seq'::regclass);
 9   ALTER TABLE public.scraper ALTER COLUMN id DROP DEFAULT;
       public          rat    false    248    247                       2604    332005    searchengine id    DEFAULT     r   ALTER TABLE ONLY public.searchengine ALTER COLUMN id SET DEFAULT nextval('public.searchengine_id_seq'::regclass);
 >   ALTER TABLE public.searchengine ALTER COLUMN id DROP DEFAULT;
       public          rat    false    250    249                       2604    332006    serp id    DEFAULT     b   ALTER TABLE ONLY public.serp ALTER COLUMN id SET DEFAULT nextval('public.serp_id_seq'::regclass);
 6   ALTER TABLE public.serp ALTER COLUMN id DROP DEFAULT;
       public          rat    false    253    252                       2604    332007 	   source id    DEFAULT     f   ALTER TABLE ONLY public.source ALTER COLUMN id SET DEFAULT nextval('public.source_id_seq'::regclass);
 8   ALTER TABLE public.source ALTER COLUMN id DROP DEFAULT;
       public          rat    false    255    254                       2604    332008    statistic id    DEFAULT     l   ALTER TABLE ONLY public.statistic ALTER COLUMN id SET DEFAULT nextval('public.statistic_id_seq'::regclass);
 ;   ALTER TABLE public.statistic ALTER COLUMN id DROP DEFAULT;
       public          rat    false    257    256                       2604    332009    study id    DEFAULT     d   ALTER TABLE ONLY public.study ALTER COLUMN id SET DEFAULT nextval('public.study_id_seq'::regclass);
 7   ALTER TABLE public.study ALTER COLUMN id DROP DEFAULT;
       public          rat    false    259    258                       2604    332010    studytype id    DEFAULT     l   ALTER TABLE ONLY public.studytype ALTER COLUMN id SET DEFAULT nextval('public.studytype_id_seq'::regclass);
 ;   ALTER TABLE public.studytype ALTER COLUMN id DROP DEFAULT;
       public          rat    false    262    261                       2604    332011    task id    DEFAULT     b   ALTER TABLE ONLY public.task ALTER COLUMN id SET DEFAULT nextval('public.task_id_seq'::regclass);
 6   ALTER TABLE public.task ALTER COLUMN id DROP DEFAULT;
       public          rat    false    264    263                       2604    332012    user id    DEFAULT     d   ALTER TABLE ONLY public."user" ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);
 8   ALTER TABLE public."user" ALTER COLUMN id DROP DEFAULT;
       public          rat    false    266    265                       2606    332014    answer answer_pkey 
   CONSTRAINT     P   ALTER TABLE ONLY public.answer
    ADD CONSTRAINT answer_pkey PRIMARY KEY (id);
 <   ALTER TABLE ONLY public.answer DROP CONSTRAINT answer_pkey;
       public            rat    false    196            �           2606    332472 .   classifier_indicator classifier_indicator_pkey 
   CONSTRAINT     l   ALTER TABLE ONLY public.classifier_indicator
    ADD CONSTRAINT classifier_indicator_pkey PRIMARY KEY (id);
 X   ALTER TABLE ONLY public.classifier_indicator DROP CONSTRAINT classifier_indicator_pkey;
       public            rat    false    271            �           2606    332460    classifier classifier_pkey 
   CONSTRAINT     X   ALTER TABLE ONLY public.classifier
    ADD CONSTRAINT classifier_pkey PRIMARY KEY (id);
 D   ALTER TABLE ONLY public.classifier DROP CONSTRAINT classifier_pkey;
       public            rat    false    269            �           2606    332484 (   classifier_result classifier_result_pkey 
   CONSTRAINT     f   ALTER TABLE ONLY public.classifier_result
    ADD CONSTRAINT classifier_result_pkey PRIMARY KEY (id);
 R   ALTER TABLE ONLY public.classifier_result DROP CONSTRAINT classifier_result_pkey;
       public            rat    false    273            �           2606    332492 &   classifier_study classifier_study_pkey 
   CONSTRAINT     d   ALTER TABLE ONLY public.classifier_study
    ADD CONSTRAINT classifier_study_pkey PRIMARY KEY (id);
 P   ALTER TABLE ONLY public.classifier_study DROP CONSTRAINT classifier_study_pkey;
       public            rat    false    275            "           2606    332020    content content_pkey 
   CONSTRAINT     R   ALTER TABLE ONLY public.content
    ADD CONSTRAINT content_pkey PRIMARY KEY (id);
 >   ALTER TABLE ONLY public.content DROP CONSTRAINT content_pkey;
       public            rat    false    198            %           2606    332022    country country_pkey 
   CONSTRAINT     R   ALTER TABLE ONLY public.country
    ADD CONSTRAINT country_pkey PRIMARY KEY (id);
 >   ALTER TABLE ONLY public.country DROP CONSTRAINT country_pkey;
       public            rat    false    200            '           2606    332024    dummy_table dummy_table_pkey 
   CONSTRAINT     Z   ALTER TABLE ONLY public.dummy_table
    ADD CONSTRAINT dummy_table_pkey PRIMARY KEY (id);
 F   ALTER TABLE ONLY public.dummy_table DROP CONSTRAINT dummy_table_pkey;
       public            rat    false    203            )           2606    332026    evaluation evaluation_pkey 
   CONSTRAINT     X   ALTER TABLE ONLY public.evaluation
    ADD CONSTRAINT evaluation_pkey PRIMARY KEY (id);
 D   ALTER TABLE ONLY public.evaluation DROP CONSTRAINT evaluation_pkey;
       public            rat    false    205            ,           2606    332028    experiment experiment_pkey 
   CONSTRAINT     X   ALTER TABLE ONLY public.experiment
    ADD CONSTRAINT experiment_pkey PRIMARY KEY (id);
 D   ALTER TABLE ONLY public.experiment DROP CONSTRAINT experiment_pkey;
       public            rat    false    207            /           2606    332030    group group_pkey 
   CONSTRAINT     P   ALTER TABLE ONLY public."group"
    ADD CONSTRAINT group_pkey PRIMARY KEY (id);
 <   ALTER TABLE ONLY public."group" DROP CONSTRAINT group_pkey;
       public            rat    false    209            3           2606    332032    incentive incentive_pkey 
   CONSTRAINT     V   ALTER TABLE ONLY public.incentive
    ADD CONSTRAINT incentive_pkey PRIMARY KEY (id);
 B   ALTER TABLE ONLY public.incentive DROP CONSTRAINT incentive_pkey;
       public            rat    false    211            5           2606    332034    language language_pkey 
   CONSTRAINT     T   ALTER TABLE ONLY public.language
    ADD CONSTRAINT language_pkey PRIMARY KEY (id);
 @   ALTER TABLE ONLY public.language DROP CONSTRAINT language_pkey;
       public            rat    false    213            8           2606    332036 "   language_study language_study_pkey 
   CONSTRAINT     m   ALTER TABLE ONLY public.language_study
    ADD CONSTRAINT language_study_pkey PRIMARY KEY (language, study);
 L   ALTER TABLE ONLY public.language_study DROP CONSTRAINT language_study_pkey;
       public            rat    false    215    215            :           2606    332038    logger logger_pkey 
   CONSTRAINT     P   ALTER TABLE ONLY public.logger
    ADD CONSTRAINT logger_pkey PRIMARY KEY (id);
 <   ALTER TABLE ONLY public.logger DROP CONSTRAINT logger_pkey;
       public            rat    false    216            =           2606    332040    logger_query logger_query_pkey 
   CONSTRAINT     g   ALTER TABLE ONLY public.logger_query
    ADD CONSTRAINT logger_query_pkey PRIMARY KEY (logger, query);
 H   ALTER TABLE ONLY public.logger_query DROP CONSTRAINT logger_query_pkey;
       public            rat    false    218    218            @           2606    332042     logger_result logger_result_pkey 
   CONSTRAINT     j   ALTER TABLE ONLY public.logger_result
    ADD CONSTRAINT logger_result_pkey PRIMARY KEY (logger, result);
 J   ALTER TABLE ONLY public.logger_result DROP CONSTRAINT logger_result_pkey;
       public            rat    false    219    219            C           2606    332044 "   logger_scraper logger_scraper_pkey 
   CONSTRAINT     m   ALTER TABLE ONLY public.logger_scraper
    ADD CONSTRAINT logger_scraper_pkey PRIMARY KEY (logger, scraper);
 L   ALTER TABLE ONLY public.logger_scraper DROP CONSTRAINT logger_scraper_pkey;
       public            rat    false    220    220            F           2606    332046 ,   logger_searchengine logger_searchengine_pkey 
   CONSTRAINT     |   ALTER TABLE ONLY public.logger_searchengine
    ADD CONSTRAINT logger_searchengine_pkey PRIMARY KEY (logger, searchengine);
 V   ALTER TABLE ONLY public.logger_searchengine DROP CONSTRAINT logger_searchengine_pkey;
       public            rat    false    221    221            I           2606    332048    logger_serp logger_serp_pkey 
   CONSTRAINT     d   ALTER TABLE ONLY public.logger_serp
    ADD CONSTRAINT logger_serp_pkey PRIMARY KEY (logger, serp);
 F   ALTER TABLE ONLY public.logger_serp DROP CONSTRAINT logger_serp_pkey;
       public            rat    false    222    222            K           2606    332050    monitoring monitoring_pkey 
   CONSTRAINT     X   ALTER TABLE ONLY public.monitoring
    ADD CONSTRAINT monitoring_pkey PRIMARY KEY (id);
 D   ALTER TABLE ONLY public.monitoring DROP CONSTRAINT monitoring_pkey;
       public            rat    false    223            N           2606    332052    option option_pkey 
   CONSTRAINT     P   ALTER TABLE ONLY public.option
    ADD CONSTRAINT option_pkey PRIMARY KEY (id);
 <   ALTER TABLE ONLY public.option DROP CONSTRAINT option_pkey;
       public            rat    false    225            Q           2606    332054    participant participant_pkey 
   CONSTRAINT     Z   ALTER TABLE ONLY public.participant
    ADD CONSTRAINT participant_pkey PRIMARY KEY (id);
 F   ALTER TABLE ONLY public.participant DROP CONSTRAINT participant_pkey;
       public            rat    false    227            T           2606    332056 (   participant_study participant_study_pkey 
   CONSTRAINT     v   ALTER TABLE ONLY public.participant_study
    ADD CONSTRAINT participant_study_pkey PRIMARY KEY (participant, study);
 R   ALTER TABLE ONLY public.participant_study DROP CONSTRAINT participant_study_pkey;
       public            rat    false    229    229            W           2606    332058    query query_pkey 
   CONSTRAINT     N   ALTER TABLE ONLY public.query
    ADD CONSTRAINT query_pkey PRIMARY KEY (id);
 :   ALTER TABLE ONLY public.query DROP CONSTRAINT query_pkey;
       public            rat    false    230            \           2606    332060    question question_pkey 
   CONSTRAINT     T   ALTER TABLE ONLY public.question
    ADD CONSTRAINT question_pkey PRIMARY KEY (id);
 @   ALTER TABLE ONLY public.question DROP CONSTRAINT question_pkey;
       public            rat    false    232            _           2606    332062 $   question_result question_result_pkey 
   CONSTRAINT     p   ALTER TABLE ONLY public.question_result
    ADD CONSTRAINT question_result_pkey PRIMARY KEY (question, result);
 N   ALTER TABLE ONLY public.question_result DROP CONSTRAINT question_result_pkey;
       public            rat    false    234    234            a           2606    332064 &   questiontemplate questiontemplate_pkey 
   CONSTRAINT     d   ALTER TABLE ONLY public.questiontemplate
    ADD CONSTRAINT questiontemplate_pkey PRIMARY KEY (id);
 P   ALTER TABLE ONLY public.questiontemplate DROP CONSTRAINT questiontemplate_pkey;
       public            rat    false    235            c           2606    332066    questiontype questiontype_pkey 
   CONSTRAINT     \   ALTER TABLE ONLY public.questiontype
    ADD CONSTRAINT questiontype_pkey PRIMARY KEY (id);
 H   ALTER TABLE ONLY public.questiontype DROP CONSTRAINT questiontype_pkey;
       public            rat    false    237            f           2606    332068    reporting reporting_pkey 
   CONSTRAINT     V   ALTER TABLE ONLY public.reporting
    ADD CONSTRAINT reporting_pkey PRIMARY KEY (id);
 B   ALTER TABLE ONLY public.reporting DROP CONSTRAINT reporting_pkey;
       public            rat    false    239            l           2606    332070    result result_pkey 
   CONSTRAINT     P   ALTER TABLE ONLY public.result
    ADD CONSTRAINT result_pkey PRIMARY KEY (id);
 <   ALTER TABLE ONLY public.result DROP CONSTRAINT result_pkey;
       public            rat    false    241            �           2606    335450     result_source result_source_pkey 
   CONSTRAINT     ^   ALTER TABLE ONLY public.result_source
    ADD CONSTRAINT result_source_pkey PRIMARY KEY (id);
 J   ALTER TABLE ONLY public.result_source DROP CONSTRAINT result_source_pkey;
       public            rat    false    276            n           2606    332072    resulttype resulttype_pkey 
   CONSTRAINT     X   ALTER TABLE ONLY public.resulttype
    ADD CONSTRAINT resulttype_pkey PRIMARY KEY (id);
 D   ALTER TABLE ONLY public.resulttype DROP CONSTRAINT resulttype_pkey;
       public            rat    false    243            p           2606    332074    role role_pkey 
   CONSTRAINT     L   ALTER TABLE ONLY public.role
    ADD CONSTRAINT role_pkey PRIMARY KEY (id);
 8   ALTER TABLE ONLY public.role DROP CONSTRAINT role_pkey;
       public            rat    false    245            u           2606    332076    scraper scraper_pkey 
   CONSTRAINT     R   ALTER TABLE ONLY public.scraper
    ADD CONSTRAINT scraper_pkey PRIMARY KEY (id);
 >   ALTER TABLE ONLY public.scraper DROP CONSTRAINT scraper_pkey;
       public            rat    false    247            w           2606    332078    searchengine searchengine_pkey 
   CONSTRAINT     \   ALTER TABLE ONLY public.searchengine
    ADD CONSTRAINT searchengine_pkey PRIMARY KEY (id);
 H   ALTER TABLE ONLY public.searchengine DROP CONSTRAINT searchengine_pkey;
       public            rat    false    249            z           2606    332080 *   searchengine_study searchengine_study_pkey 
   CONSTRAINT     y   ALTER TABLE ONLY public.searchengine_study
    ADD CONSTRAINT searchengine_study_pkey PRIMARY KEY (searchengine, study);
 T   ALTER TABLE ONLY public.searchengine_study DROP CONSTRAINT searchengine_study_pkey;
       public            rat    false    251    251            }           2606    332082    serp serp_pkey 
   CONSTRAINT     L   ALTER TABLE ONLY public.serp
    ADD CONSTRAINT serp_pkey PRIMARY KEY (id);
 8   ALTER TABLE ONLY public.serp DROP CONSTRAINT serp_pkey;
       public            rat    false    252                       2606    332084    source source_pkey 
   CONSTRAINT     P   ALTER TABLE ONLY public.source
    ADD CONSTRAINT source_pkey PRIMARY KEY (id);
 <   ALTER TABLE ONLY public.source DROP CONSTRAINT source_pkey;
       public            rat    false    254            �           2606    332086    statistic statistic_pkey 
   CONSTRAINT     V   ALTER TABLE ONLY public.statistic
    ADD CONSTRAINT statistic_pkey PRIMARY KEY (id);
 B   ALTER TABLE ONLY public.statistic DROP CONSTRAINT statistic_pkey;
       public            rat    false    256            �           2606    332088    study study_pkey 
   CONSTRAINT     N   ALTER TABLE ONLY public.study
    ADD CONSTRAINT study_pkey PRIMARY KEY (id);
 :   ALTER TABLE ONLY public.study DROP CONSTRAINT study_pkey;
       public            rat    false    258            �           2606    332090    study_user study_user_pkey 
   CONSTRAINT     c   ALTER TABLE ONLY public.study_user
    ADD CONSTRAINT study_user_pkey PRIMARY KEY (study, "user");
 D   ALTER TABLE ONLY public.study_user DROP CONSTRAINT study_user_pkey;
       public            rat    false    260    260            �           2606    332092    studytype studytype_pkey 
   CONSTRAINT     V   ALTER TABLE ONLY public.studytype
    ADD CONSTRAINT studytype_pkey PRIMARY KEY (id);
 B   ALTER TABLE ONLY public.studytype DROP CONSTRAINT studytype_pkey;
       public            rat    false    261            �           2606    332094    task task_pkey 
   CONSTRAINT     L   ALTER TABLE ONLY public.task
    ADD CONSTRAINT task_pkey PRIMARY KEY (id);
 8   ALTER TABLE ONLY public.task DROP CONSTRAINT task_pkey;
       public            rat    false    263            �           2606    332096    user user_pkey 
   CONSTRAINT     N   ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);
 :   ALTER TABLE ONLY public."user" DROP CONSTRAINT user_pkey;
       public            rat    false    265            g           1259    332099    fki_fk_result__serp    INDEX     F   CREATE INDEX fki_fk_result__serp ON public.result USING btree (serp);
 '   DROP INDEX public.fki_fk_result__serp;
       public            rat    false    241            h           1259    332100    fki_r    INDEX     8   CREATE INDEX fki_r ON public.result USING btree (serp);
    DROP INDEX public.fki_r;
       public            rat    false    241                       1259    332101    idx_answer__participant    INDEX     Q   CREATE INDEX idx_answer__participant ON public.answer USING btree (participant);
 +   DROP INDEX public.idx_answer__participant;
       public            rat    false    196                       1259    332102    idx_answer__question    INDEX     K   CREATE INDEX idx_answer__question ON public.answer USING btree (question);
 (   DROP INDEX public.idx_answer__question;
       public            rat    false    196                       1259    332103    idx_answer__result    INDEX     G   CREATE INDEX idx_answer__result ON public.answer USING btree (result);
 &   DROP INDEX public.idx_answer__result;
       public            rat    false    196                        1259    332104    idx_answer__study    INDEX     E   CREATE INDEX idx_answer__study ON public.answer USING btree (study);
 %   DROP INDEX public.idx_answer__study;
       public            rat    false    196            #           1259    332105    idx_content__result    INDEX     I   CREATE INDEX idx_content__result ON public.content USING btree (result);
 '   DROP INDEX public.idx_content__result;
       public            rat    false    198            *           1259    332106    idx_evaluation__source    INDEX     O   CREATE INDEX idx_evaluation__source ON public.evaluation USING btree (source);
 *   DROP INDEX public.idx_evaluation__source;
       public            rat    false    205            -           1259    332107    idx_experiment__study    INDEX     M   CREATE INDEX idx_experiment__study ON public.experiment USING btree (study);
 )   DROP INDEX public.idx_experiment__study;
       public            rat    false    207            0           1259    332108    idx_incentive__participant    INDEX     W   CREATE INDEX idx_incentive__participant ON public.incentive USING btree (participant);
 .   DROP INDEX public.idx_incentive__participant;
       public            rat    false    211            1           1259    332109    idx_incentive__study    INDEX     K   CREATE INDEX idx_incentive__study ON public.incentive USING btree (study);
 (   DROP INDEX public.idx_incentive__study;
       public            rat    false    211            6           1259    332110    idx_language_study    INDEX     N   CREATE INDEX idx_language_study ON public.language_study USING btree (study);
 &   DROP INDEX public.idx_language_study;
       public            rat    false    215            ;           1259    332111    idx_logger_query    INDEX     J   CREATE INDEX idx_logger_query ON public.logger_query USING btree (query);
 $   DROP INDEX public.idx_logger_query;
       public            rat    false    218            >           1259    332112    idx_logger_result    INDEX     M   CREATE INDEX idx_logger_result ON public.logger_result USING btree (result);
 %   DROP INDEX public.idx_logger_result;
       public            rat    false    219            A           1259    332113    idx_logger_scraper    INDEX     P   CREATE INDEX idx_logger_scraper ON public.logger_scraper USING btree (scraper);
 &   DROP INDEX public.idx_logger_scraper;
       public            rat    false    220            D           1259    332114    idx_logger_searchengine    INDEX     _   CREATE INDEX idx_logger_searchengine ON public.logger_searchengine USING btree (searchengine);
 +   DROP INDEX public.idx_logger_searchengine;
       public            rat    false    221            G           1259    332115    idx_logger_serp    INDEX     G   CREATE INDEX idx_logger_serp ON public.logger_serp USING btree (serp);
 #   DROP INDEX public.idx_logger_serp;
       public            rat    false    222            L           1259    332116    idx_option__question    INDEX     K   CREATE INDEX idx_option__question ON public.option USING btree (question);
 (   DROP INDEX public.idx_option__question;
       public            rat    false    225            O           1259    332117    idx_participant__group    INDEX     Q   CREATE INDEX idx_participant__group ON public.participant USING btree ("group");
 *   DROP INDEX public.idx_participant__group;
       public            rat    false    227            R           1259    332118    idx_participant_study    INDEX     T   CREATE INDEX idx_participant_study ON public.participant_study USING btree (study);
 )   DROP INDEX public.idx_participant_study;
       public            rat    false    229            U           1259    332119    idx_query__study    INDEX     C   CREATE INDEX idx_query__study ON public.query USING btree (study);
 $   DROP INDEX public.idx_query__study;
       public            rat    false    230            X           1259    332120    idx_question__question_template    INDEX     a   CREATE INDEX idx_question__question_template ON public.question USING btree (question_template);
 3   DROP INDEX public.idx_question__question_template;
       public            rat    false    232            Y           1259    332121    idx_question__question_type    INDEX     Y   CREATE INDEX idx_question__question_type ON public.question USING btree (question_type);
 /   DROP INDEX public.idx_question__question_type;
       public            rat    false    232            Z           1259    332122    idx_question__study    INDEX     I   CREATE INDEX idx_question__study ON public.question USING btree (study);
 '   DROP INDEX public.idx_question__study;
       public            rat    false    232            ]           1259    332123    idx_question_result    INDEX     Q   CREATE INDEX idx_question_result ON public.question_result USING btree (result);
 '   DROP INDEX public.idx_question_result;
       public            rat    false    234            d           1259    332124    idx_reporting__scraper    INDEX     O   CREATE INDEX idx_reporting__scraper ON public.reporting USING btree (scraper);
 *   DROP INDEX public.idx_reporting__scraper;
       public            rat    false    239            i           1259    332125    idx_result__scraper    INDEX     I   CREATE INDEX idx_result__scraper ON public.result USING btree (scraper);
 '   DROP INDEX public.idx_result__scraper;
       public            rat    false    241            j           1259    332126    idx_result__study    INDEX     E   CREATE INDEX idx_result__study ON public.result USING btree (study);
 %   DROP INDEX public.idx_result__study;
       public            rat    false    241            q           1259    332127    idx_scraper__query    INDEX     G   CREATE INDEX idx_scraper__query ON public.scraper USING btree (query);
 &   DROP INDEX public.idx_scraper__query;
       public            rat    false    247            r           1259    332128    idx_scraper__search_engine    INDEX     V   CREATE INDEX idx_scraper__search_engine ON public.scraper USING btree (searchengine);
 .   DROP INDEX public.idx_scraper__search_engine;
       public            rat    false    247            s           1259    332129    idx_scraper__study    INDEX     G   CREATE INDEX idx_scraper__study ON public.scraper USING btree (study);
 &   DROP INDEX public.idx_scraper__study;
       public            rat    false    247            x           1259    332130    idx_searchengine_study    INDEX     V   CREATE INDEX idx_searchengine_study ON public.searchengine_study USING btree (study);
 *   DROP INDEX public.idx_searchengine_study;
       public            rat    false    251            {           1259    332131    idx_serp__scraper    INDEX     E   CREATE INDEX idx_serp__scraper ON public.serp USING btree (scraper);
 %   DROP INDEX public.idx_serp__scraper;
       public            rat    false    252            �           1259    332132    idx_statistic__study    INDEX     K   CREATE INDEX idx_statistic__study ON public.statistic USING btree (study);
 (   DROP INDEX public.idx_statistic__study;
       public            rat    false    256            �           1259    332133    idx_study__study_type    INDEX     L   CREATE INDEX idx_study__study_type ON public.study USING btree (studytype);
 )   DROP INDEX public.idx_study__study_type;
       public            rat    false    258            �           1259    332134    idx_study_user    INDEX     G   CREATE INDEX idx_study_user ON public.study_user USING btree ("user");
 "   DROP INDEX public.idx_study_user;
       public            rat    false    260            �           1259    332135    idx_task__logger    INDEX     C   CREATE INDEX idx_task__logger ON public.task USING btree (logger);
 $   DROP INDEX public.idx_task__logger;
       public            rat    false    263            �           2606    336017 ,   classifier_study classifier_study_relation_2    FK CONSTRAINT     �   ALTER TABLE ONLY public.classifier_study
    ADD CONSTRAINT classifier_study_relation_2 FOREIGN KEY (study) REFERENCES public.study(id);
 V   ALTER TABLE ONLY public.classifier_study DROP CONSTRAINT classifier_study_relation_2;
       public          rat    false    275    258    3205            �           2606    332141    answer fk_answer__participant    FK CONSTRAINT     �   ALTER TABLE ONLY public.answer
    ADD CONSTRAINT fk_answer__participant FOREIGN KEY (participant) REFERENCES public.participant(id) ON DELETE SET NULL;
 G   ALTER TABLE ONLY public.answer DROP CONSTRAINT fk_answer__participant;
       public          rat    false    227    196    3153            �           2606    332146    answer fk_answer__question    FK CONSTRAINT     �   ALTER TABLE ONLY public.answer
    ADD CONSTRAINT fk_answer__question FOREIGN KEY (question) REFERENCES public.question(id) ON DELETE SET NULL;
 D   ALTER TABLE ONLY public.answer DROP CONSTRAINT fk_answer__question;
       public          rat    false    232    196    3164            �           2606    332151    answer fk_answer__result    FK CONSTRAINT     �   ALTER TABLE ONLY public.answer
    ADD CONSTRAINT fk_answer__result FOREIGN KEY (result) REFERENCES public.result(id) ON DELETE SET NULL;
 B   ALTER TABLE ONLY public.answer DROP CONSTRAINT fk_answer__result;
       public          rat    false    196    3180    241            �           2606    332156    answer fk_answer__study    FK CONSTRAINT     t   ALTER TABLE ONLY public.answer
    ADD CONSTRAINT fk_answer__study FOREIGN KEY (study) REFERENCES public.study(id);
 A   ALTER TABLE ONLY public.answer DROP CONSTRAINT fk_answer__study;
       public          rat    false    3205    196    258            �           2606    332508 2   classifier_result fk_classifier_result__classifier    FK CONSTRAINT     �   ALTER TABLE ONLY public.classifier_result
    ADD CONSTRAINT fk_classifier_result__classifier FOREIGN KEY (classifier) REFERENCES public.classifier(id) NOT VALID;
 \   ALTER TABLE ONLY public.classifier_result DROP CONSTRAINT fk_classifier_result__classifier;
       public          rat    false    3217    273    269            �           2606    332513 .   classifier_result fk_classifier_result__result    FK CONSTRAINT     �   ALTER TABLE ONLY public.classifier_result
    ADD CONSTRAINT fk_classifier_result__result FOREIGN KEY (result) REFERENCES public.result(id) NOT VALID;
 X   ALTER TABLE ONLY public.classifier_result DROP CONSTRAINT fk_classifier_result__result;
       public          rat    false    241    3180    273            �           2606    332518 0   classifier_study fk_classifier_study__classifier    FK CONSTRAINT     �   ALTER TABLE ONLY public.classifier_study
    ADD CONSTRAINT fk_classifier_study__classifier FOREIGN KEY (classifier) REFERENCES public.classifier(id) NOT VALID;
 Z   ALTER TABLE ONLY public.classifier_study DROP CONSTRAINT fk_classifier_study__classifier;
       public          rat    false    269    275    3217            �           2606    332161    content fk_content__result    FK CONSTRAINT     �   ALTER TABLE ONLY public.content
    ADD CONSTRAINT fk_content__result FOREIGN KEY (result) REFERENCES public.result(id) ON DELETE SET NULL;
 D   ALTER TABLE ONLY public.content DROP CONSTRAINT fk_content__result;
       public          rat    false    3180    198    241            �           2606    332166    country fk_country__language    FK CONSTRAINT        ALTER TABLE ONLY public.country
    ADD CONSTRAINT fk_country__language FOREIGN KEY (language) REFERENCES public.language(id);
 F   ALTER TABLE ONLY public.country DROP CONSTRAINT fk_country__language;
       public          rat    false    200    213    3125            �           2606    332176 1   country_monitoring fk_country_monitoring__country    FK CONSTRAINT     �   ALTER TABLE ONLY public.country_monitoring
    ADD CONSTRAINT fk_country_monitoring__country FOREIGN KEY (country) REFERENCES public.country(id);
 [   ALTER TABLE ONLY public.country_monitoring DROP CONSTRAINT fk_country_monitoring__country;
       public          rat    false    200    202    3109            �           2606    332181 4   country_monitoring fk_country_monitoring__monitoring    FK CONSTRAINT     �   ALTER TABLE ONLY public.country_monitoring
    ADD CONSTRAINT fk_country_monitoring__monitoring FOREIGN KEY (monitoring) REFERENCES public.monitoring(id);
 ^   ALTER TABLE ONLY public.country_monitoring DROP CONSTRAINT fk_country_monitoring__monitoring;
       public          rat    false    202    223    3147            �           2606    332186     evaluation fk_evaluation__source    FK CONSTRAINT     �   ALTER TABLE ONLY public.evaluation
    ADD CONSTRAINT fk_evaluation__source FOREIGN KEY (source) REFERENCES public.source(id) ON DELETE SET NULL;
 J   ALTER TABLE ONLY public.evaluation DROP CONSTRAINT fk_evaluation__source;
       public          rat    false    3199    205    254            �           2606    332191    experiment fk_experiment__study    FK CONSTRAINT     �   ALTER TABLE ONLY public.experiment
    ADD CONSTRAINT fk_experiment__study FOREIGN KEY (study) REFERENCES public.study(id) ON DELETE SET NULL;
 I   ALTER TABLE ONLY public.experiment DROP CONSTRAINT fk_experiment__study;
       public          rat    false    207    3205    258            �           2606    332196 #   incentive fk_incentive__participant    FK CONSTRAINT     �   ALTER TABLE ONLY public.incentive
    ADD CONSTRAINT fk_incentive__participant FOREIGN KEY (participant) REFERENCES public.participant(id) ON DELETE SET NULL;
 M   ALTER TABLE ONLY public.incentive DROP CONSTRAINT fk_incentive__participant;
       public          rat    false    227    3153    211            �           2606    332201    incentive fk_incentive__study    FK CONSTRAINT     �   ALTER TABLE ONLY public.incentive
    ADD CONSTRAINT fk_incentive__study FOREIGN KEY (study) REFERENCES public.study(id) ON DELETE SET NULL;
 G   ALTER TABLE ONLY public.incentive DROP CONSTRAINT fk_incentive__study;
       public          rat    false    211    258    3205            �           2606    332493 -   classifier_indicator fk_indicator__classifier    FK CONSTRAINT     �   ALTER TABLE ONLY public.classifier_indicator
    ADD CONSTRAINT fk_indicator__classifier FOREIGN KEY (classifier) REFERENCES public.classifier(id) NOT VALID;
 W   ALTER TABLE ONLY public.classifier_indicator DROP CONSTRAINT fk_indicator__classifier;
       public          rat    false    271    3217    269            �           2606    332498 )   classifier_indicator fk_indicator__result    FK CONSTRAINT     �   ALTER TABLE ONLY public.classifier_indicator
    ADD CONSTRAINT fk_indicator__result FOREIGN KEY (result) REFERENCES public.result(id) NOT VALID;
 S   ALTER TABLE ONLY public.classifier_indicator DROP CONSTRAINT fk_indicator__result;
       public          rat    false    241    271    3180            �           2606    332206 *   language_study fk_language_study__language    FK CONSTRAINT     �   ALTER TABLE ONLY public.language_study
    ADD CONSTRAINT fk_language_study__language FOREIGN KEY (language) REFERENCES public.language(id);
 T   ALTER TABLE ONLY public.language_study DROP CONSTRAINT fk_language_study__language;
       public          rat    false    215    213    3125            �           2606    332211 '   language_study fk_language_study__study    FK CONSTRAINT     �   ALTER TABLE ONLY public.language_study
    ADD CONSTRAINT fk_language_study__study FOREIGN KEY (study) REFERENCES public.study(id);
 Q   ALTER TABLE ONLY public.language_study DROP CONSTRAINT fk_language_study__study;
       public          rat    false    215    258    3205            �           2606    332216 $   logger_query fk_logger_query__logger    FK CONSTRAINT     �   ALTER TABLE ONLY public.logger_query
    ADD CONSTRAINT fk_logger_query__logger FOREIGN KEY (logger) REFERENCES public.logger(id);
 N   ALTER TABLE ONLY public.logger_query DROP CONSTRAINT fk_logger_query__logger;
       public          rat    false    216    3130    218            �           2606    332221 #   logger_query fk_logger_query__query    FK CONSTRAINT     �   ALTER TABLE ONLY public.logger_query
    ADD CONSTRAINT fk_logger_query__query FOREIGN KEY (query) REFERENCES public.query(id);
 M   ALTER TABLE ONLY public.logger_query DROP CONSTRAINT fk_logger_query__query;
       public          rat    false    3159    230    218            �           2606    332226 &   logger_result fk_logger_result__logger    FK CONSTRAINT     �   ALTER TABLE ONLY public.logger_result
    ADD CONSTRAINT fk_logger_result__logger FOREIGN KEY (logger) REFERENCES public.logger(id);
 P   ALTER TABLE ONLY public.logger_result DROP CONSTRAINT fk_logger_result__logger;
       public          rat    false    216    3130    219            �           2606    332231 &   logger_result fk_logger_result__result    FK CONSTRAINT     �   ALTER TABLE ONLY public.logger_result
    ADD CONSTRAINT fk_logger_result__result FOREIGN KEY (result) REFERENCES public.result(id);
 P   ALTER TABLE ONLY public.logger_result DROP CONSTRAINT fk_logger_result__result;
       public          rat    false    241    3180    219            �           2606    332236 (   logger_scraper fk_logger_scraper__logger    FK CONSTRAINT     �   ALTER TABLE ONLY public.logger_scraper
    ADD CONSTRAINT fk_logger_scraper__logger FOREIGN KEY (logger) REFERENCES public.logger(id);
 R   ALTER TABLE ONLY public.logger_scraper DROP CONSTRAINT fk_logger_scraper__logger;
       public          rat    false    220    216    3130            �           2606    332241 )   logger_scraper fk_logger_scraper__scraper    FK CONSTRAINT     �   ALTER TABLE ONLY public.logger_scraper
    ADD CONSTRAINT fk_logger_scraper__scraper FOREIGN KEY (scraper) REFERENCES public.scraper(id);
 S   ALTER TABLE ONLY public.logger_scraper DROP CONSTRAINT fk_logger_scraper__scraper;
       public          rat    false    3189    247    220            �           2606    332246 2   logger_searchengine fk_logger_searchengine__logger    FK CONSTRAINT     �   ALTER TABLE ONLY public.logger_searchengine
    ADD CONSTRAINT fk_logger_searchengine__logger FOREIGN KEY (logger) REFERENCES public.logger(id);
 \   ALTER TABLE ONLY public.logger_searchengine DROP CONSTRAINT fk_logger_searchengine__logger;
       public          rat    false    3130    221    216            �           2606    332251 8   logger_searchengine fk_logger_searchengine__searchengine    FK CONSTRAINT     �   ALTER TABLE ONLY public.logger_searchengine
    ADD CONSTRAINT fk_logger_searchengine__searchengine FOREIGN KEY (searchengine) REFERENCES public.searchengine(id);
 b   ALTER TABLE ONLY public.logger_searchengine DROP CONSTRAINT fk_logger_searchengine__searchengine;
       public          rat    false    249    3191    221            �           2606    332256 "   logger_serp fk_logger_serp__logger    FK CONSTRAINT     �   ALTER TABLE ONLY public.logger_serp
    ADD CONSTRAINT fk_logger_serp__logger FOREIGN KEY (logger) REFERENCES public.logger(id);
 L   ALTER TABLE ONLY public.logger_serp DROP CONSTRAINT fk_logger_serp__logger;
       public          rat    false    3130    222    216            �           2606    332261     logger_serp fk_logger_serp__serp    FK CONSTRAINT     {   ALTER TABLE ONLY public.logger_serp
    ADD CONSTRAINT fk_logger_serp__serp FOREIGN KEY (serp) REFERENCES public.serp(id);
 J   ALTER TABLE ONLY public.logger_serp DROP CONSTRAINT fk_logger_serp__serp;
       public          rat    false    252    222    3197            �           2606    332266 $   monitoring fk_monitoring__resulttype    FK CONSTRAINT     �   ALTER TABLE ONLY public.monitoring
    ADD CONSTRAINT fk_monitoring__resulttype FOREIGN KEY (resulttype) REFERENCES public.resulttype(id) ON DELETE SET NULL;
 N   ALTER TABLE ONLY public.monitoring DROP CONSTRAINT fk_monitoring__resulttype;
       public          rat    false    223    3182    243            �           2606    332271    option fk_option__question    FK CONSTRAINT     �   ALTER TABLE ONLY public.option
    ADD CONSTRAINT fk_option__question FOREIGN KEY (question) REFERENCES public.question(id) ON DELETE SET NULL;
 D   ALTER TABLE ONLY public.option DROP CONSTRAINT fk_option__question;
       public          rat    false    232    3164    225            �           2606    332276 !   participant fk_participant__group    FK CONSTRAINT     �   ALTER TABLE ONLY public.participant
    ADD CONSTRAINT fk_participant__group FOREIGN KEY ("group") REFERENCES public."group"(id) ON DELETE SET NULL;
 K   ALTER TABLE ONLY public.participant DROP CONSTRAINT fk_participant__group;
       public          rat    false    3119    227    209            �           2606    332281 3   participant_study fk_participant_study__participant    FK CONSTRAINT     �   ALTER TABLE ONLY public.participant_study
    ADD CONSTRAINT fk_participant_study__participant FOREIGN KEY (participant) REFERENCES public.participant(id);
 ]   ALTER TABLE ONLY public.participant_study DROP CONSTRAINT fk_participant_study__participant;
       public          rat    false    227    229    3153            �           2606    332286 -   participant_study fk_participant_study__study    FK CONSTRAINT     �   ALTER TABLE ONLY public.participant_study
    ADD CONSTRAINT fk_participant_study__study FOREIGN KEY (study) REFERENCES public.study(id);
 W   ALTER TABLE ONLY public.participant_study DROP CONSTRAINT fk_participant_study__study;
       public          rat    false    229    258    3205            �           2606    332291    query fk_query__monitoring    FK CONSTRAINT     �   ALTER TABLE ONLY public.query
    ADD CONSTRAINT fk_query__monitoring FOREIGN KEY (monitoring) REFERENCES public.monitoring(id) ON DELETE SET NULL;
 D   ALTER TABLE ONLY public.query DROP CONSTRAINT fk_query__monitoring;
       public          rat    false    223    3147    230            �           2606    332296    query fk_query__study    FK CONSTRAINT     �   ALTER TABLE ONLY public.query
    ADD CONSTRAINT fk_query__study FOREIGN KEY (study) REFERENCES public.study(id) ON DELETE SET NULL;
 ?   ALTER TABLE ONLY public.query DROP CONSTRAINT fk_query__study;
       public          rat    false    3205    258    230            �           2606    332301 '   question fk_question__question_template    FK CONSTRAINT     �   ALTER TABLE ONLY public.question
    ADD CONSTRAINT fk_question__question_template FOREIGN KEY (question_template) REFERENCES public.questiontemplate(id) ON DELETE SET NULL;
 Q   ALTER TABLE ONLY public.question DROP CONSTRAINT fk_question__question_template;
       public          rat    false    232    3169    235            �           2606    332306 #   question fk_question__question_type    FK CONSTRAINT     �   ALTER TABLE ONLY public.question
    ADD CONSTRAINT fk_question__question_type FOREIGN KEY (question_type) REFERENCES public.questiontype(id) ON DELETE SET NULL;
 M   ALTER TABLE ONLY public.question DROP CONSTRAINT fk_question__question_type;
       public          rat    false    237    3171    232            �           2606    332311    question fk_question__study    FK CONSTRAINT     �   ALTER TABLE ONLY public.question
    ADD CONSTRAINT fk_question__study FOREIGN KEY (study) REFERENCES public.study(id) ON DELETE SET NULL;
 E   ALTER TABLE ONLY public.question DROP CONSTRAINT fk_question__study;
       public          rat    false    3205    258    232            �           2606    332316 ,   question_result fk_question_result__question    FK CONSTRAINT     �   ALTER TABLE ONLY public.question_result
    ADD CONSTRAINT fk_question_result__question FOREIGN KEY (question) REFERENCES public.question(id);
 V   ALTER TABLE ONLY public.question_result DROP CONSTRAINT fk_question_result__question;
       public          rat    false    3164    234    232            �           2606    332321 *   question_result fk_question_result__result    FK CONSTRAINT     �   ALTER TABLE ONLY public.question_result
    ADD CONSTRAINT fk_question_result__result FOREIGN KEY (result) REFERENCES public.result(id);
 T   ALTER TABLE ONLY public.question_result DROP CONSTRAINT fk_question_result__result;
       public          rat    false    3180    241    234            �           2606    332326    reporting fk_reporting__scraper    FK CONSTRAINT     �   ALTER TABLE ONLY public.reporting
    ADD CONSTRAINT fk_reporting__scraper FOREIGN KEY (scraper) REFERENCES public.scraper(id) ON DELETE SET NULL;
 I   ALTER TABLE ONLY public.reporting DROP CONSTRAINT fk_reporting__scraper;
       public          rat    false    239    247    3189            �           2606    332331    result fk_result__monitoring    FK CONSTRAINT     �   ALTER TABLE ONLY public.result
    ADD CONSTRAINT fk_result__monitoring FOREIGN KEY (monitoring) REFERENCES public.monitoring(id);
 F   ALTER TABLE ONLY public.result DROP CONSTRAINT fk_result__monitoring;
       public          rat    false    241    3147    223            �           2606    332336    result fk_result__query    FK CONSTRAINT     �   ALTER TABLE ONLY public.result
    ADD CONSTRAINT fk_result__query FOREIGN KEY (query) REFERENCES public.query(id) ON DELETE SET NULL;
 A   ALTER TABLE ONLY public.result DROP CONSTRAINT fk_result__query;
       public          rat    false    230    3159    241            �           2606    332341    result fk_result__serp    FK CONSTRAINT     �   ALTER TABLE ONLY public.result
    ADD CONSTRAINT fk_result__serp FOREIGN KEY (serp) REFERENCES public.serp(id) ON DELETE SET NULL;
 @   ALTER TABLE ONLY public.result DROP CONSTRAINT fk_result__serp;
       public          rat    false    241    3197    252            �           2606    332346    result fk_result__study    FK CONSTRAINT     �   ALTER TABLE ONLY public.result
    ADD CONSTRAINT fk_result__study FOREIGN KEY (study) REFERENCES public.study(id) ON DELETE SET NULL;
 A   ALTER TABLE ONLY public.result DROP CONSTRAINT fk_result__study;
       public          rat    false    3205    241    258            �           2606    332351    result fk_result_resulttype    FK CONSTRAINT     �   ALTER TABLE ONLY public.result
    ADD CONSTRAINT fk_result_resulttype FOREIGN KEY (resulttype) REFERENCES public.resulttype(id);
 E   ALTER TABLE ONLY public.result DROP CONSTRAINT fk_result_resulttype;
       public          rat    false    241    3182    243            �           2606    332356    result fk_result_scraper    FK CONSTRAINT     �   ALTER TABLE ONLY public.result
    ADD CONSTRAINT fk_result_scraper FOREIGN KEY (scraper) REFERENCES public.scraper(id) ON DELETE SET NULL;
 B   ALTER TABLE ONLY public.result DROP CONSTRAINT fk_result_scraper;
       public          rat    false    241    247    3189            �           2606    332526 &   result_source fk_result_source__result    FK CONSTRAINT     �   ALTER TABLE ONLY public.result_source
    ADD CONSTRAINT fk_result_source__result FOREIGN KEY (result) REFERENCES public.result(id);
 P   ALTER TABLE ONLY public.result_source DROP CONSTRAINT fk_result_source__result;
       public          rat    false    241    276    3180            �           2606    332531 &   result_source fk_result_source__source    FK CONSTRAINT     �   ALTER TABLE ONLY public.result_source
    ADD CONSTRAINT fk_result_source__source FOREIGN KEY (source) REFERENCES public.source(id);
 P   ALTER TABLE ONLY public.result_source DROP CONSTRAINT fk_result_source__source;
       public          rat    false    276    254    3199            �           2606    332361    scraper fk_scraper__query    FK CONSTRAINT     �   ALTER TABLE ONLY public.scraper
    ADD CONSTRAINT fk_scraper__query FOREIGN KEY (query) REFERENCES public.query(id) ON DELETE SET NULL;
 C   ALTER TABLE ONLY public.scraper DROP CONSTRAINT fk_scraper__query;
       public          rat    false    230    247    3159            �           2606    332366 !   scraper fk_scraper__search_engine    FK CONSTRAINT     �   ALTER TABLE ONLY public.scraper
    ADD CONSTRAINT fk_scraper__search_engine FOREIGN KEY (searchengine) REFERENCES public.searchengine(id) ON DELETE SET NULL;
 K   ALTER TABLE ONLY public.scraper DROP CONSTRAINT fk_scraper__search_engine;
       public          rat    false    249    247    3191            �           2606    332371    scraper fk_scraper__study    FK CONSTRAINT     �   ALTER TABLE ONLY public.scraper
    ADD CONSTRAINT fk_scraper__study FOREIGN KEY (study) REFERENCES public.study(id) ON DELETE SET NULL;
 C   ALTER TABLE ONLY public.scraper DROP CONSTRAINT fk_scraper__study;
       public          rat    false    247    258    3205            �           2606    332376 6   searchengine_study fk_searchengine_study__searchengine    FK CONSTRAINT     �   ALTER TABLE ONLY public.searchengine_study
    ADD CONSTRAINT fk_searchengine_study__searchengine FOREIGN KEY (searchengine) REFERENCES public.searchengine(id);
 `   ALTER TABLE ONLY public.searchengine_study DROP CONSTRAINT fk_searchengine_study__searchengine;
       public          rat    false    251    249    3191            �           2606    332381 /   searchengine_study fk_searchengine_study__study    FK CONSTRAINT     �   ALTER TABLE ONLY public.searchengine_study
    ADD CONSTRAINT fk_searchengine_study__study FOREIGN KEY (study) REFERENCES public.study(id);
 Y   ALTER TABLE ONLY public.searchengine_study DROP CONSTRAINT fk_searchengine_study__study;
       public          rat    false    251    258    3205            �           2606    332386    serp fk_serp__monitoring    FK CONSTRAINT     �   ALTER TABLE ONLY public.serp
    ADD CONSTRAINT fk_serp__monitoring FOREIGN KEY (monitoring) REFERENCES public.monitoring(id) ON DELETE SET NULL;
 B   ALTER TABLE ONLY public.serp DROP CONSTRAINT fk_serp__monitoring;
       public          rat    false    223    3147    252            �           2606    332391    serp fk_serp__query    FK CONSTRAINT     �   ALTER TABLE ONLY public.serp
    ADD CONSTRAINT fk_serp__query FOREIGN KEY (query) REFERENCES public.query(id) ON DELETE SET NULL;
 =   ALTER TABLE ONLY public.serp DROP CONSTRAINT fk_serp__query;
       public          rat    false    230    3159    252            �           2606    332396    serp fk_serp__scraper    FK CONSTRAINT     �   ALTER TABLE ONLY public.serp
    ADD CONSTRAINT fk_serp__scraper FOREIGN KEY (scraper) REFERENCES public.scraper(id) ON DELETE SET NULL;
 ?   ALTER TABLE ONLY public.serp DROP CONSTRAINT fk_serp__scraper;
       public          rat    false    252    3189    247            �           2606    332401    statistic fk_statistic__study    FK CONSTRAINT     �   ALTER TABLE ONLY public.statistic
    ADD CONSTRAINT fk_statistic__study FOREIGN KEY (study) REFERENCES public.study(id) ON DELETE SET NULL;
 G   ALTER TABLE ONLY public.statistic DROP CONSTRAINT fk_statistic__study;
       public          rat    false    258    256    3205            �           2606    332406    study fk_study__result_type    FK CONSTRAINT     �   ALTER TABLE ONLY public.study
    ADD CONSTRAINT fk_study__result_type FOREIGN KEY (resulttype) REFERENCES public.resulttype(id) ON DELETE SET NULL;
 E   ALTER TABLE ONLY public.study DROP CONSTRAINT fk_study__result_type;
       public          rat    false    258    243    3182            �           2606    332411    study fk_study__study_type    FK CONSTRAINT     �   ALTER TABLE ONLY public.study
    ADD CONSTRAINT fk_study__study_type FOREIGN KEY (studytype) REFERENCES public.studytype(id) ON DELETE SET NULL;
 D   ALTER TABLE ONLY public.study DROP CONSTRAINT fk_study__study_type;
       public          rat    false    3210    261    258            �           2606    332416    study_user fk_study_user__study    FK CONSTRAINT     |   ALTER TABLE ONLY public.study_user
    ADD CONSTRAINT fk_study_user__study FOREIGN KEY (study) REFERENCES public.study(id);
 I   ALTER TABLE ONLY public.study_user DROP CONSTRAINT fk_study_user__study;
       public          rat    false    258    260    3205            �           2606    332421    study_user fk_study_user__user    FK CONSTRAINT     }   ALTER TABLE ONLY public.study_user
    ADD CONSTRAINT fk_study_user__user FOREIGN KEY ("user") REFERENCES public."user"(id);
 H   ALTER TABLE ONLY public.study_user DROP CONSTRAINT fk_study_user__user;
       public          rat    false    260    3215    265            �           2606    332426    task fk_task__logger    FK CONSTRAINT     �   ALTER TABLE ONLY public.task
    ADD CONSTRAINT fk_task__logger FOREIGN KEY (logger) REFERENCES public.logger(id) ON DELETE SET NULL;
 >   ALTER TABLE ONLY public.task DROP CONSTRAINT fk_task__logger;
       public          rat    false    216    3130    263            �           2606    332436    user_role user_role_relation_1    FK CONSTRAINT     �   ALTER TABLE ONLY public.user_role
    ADD CONSTRAINT user_role_relation_1 FOREIGN KEY ("user") REFERENCES public."user"(id) ON UPDATE CASCADE ON DELETE CASCADE;
 H   ALTER TABLE ONLY public.user_role DROP CONSTRAINT user_role_relation_1;
       public          rat    false    267    265    3215            �           2606    332441    user_role user_role_relation_2    FK CONSTRAINT     �   ALTER TABLE ONLY public.user_role
    ADD CONSTRAINT user_role_relation_2 FOREIGN KEY (role) REFERENCES public.role(id) ON UPDATE CASCADE ON DELETE CASCADE;
 H   ALTER TABLE ONLY public.user_role DROP CONSTRAINT user_role_relation_2;
       public          rat    false    267    3184    245           