--
-- PostgreSQL database dump
--

-- Dumped from database version 11.14 (Debian 11.14-0+deb10u1)
-- Dumped by pg_dump version 14.1

-- Started on 2022-10-20 14:00:09 CEST

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
-- TOC entry 3117 (class 0 OID 133237)
-- Dependencies: 207
-- Data for Name: role; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.role (id, name, description, permissions, update_datetime) FROM stdin;
1	Admin	\N	\N	\N
2	Creator	\N	\N	\N
3	Editor	\N	\N	\N
\.


--
-- TOC entry 3123 (class 0 OID 0)
-- Dependencies: 206
-- Name: role_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.role_id_seq', 1, false);


-- Completed on 2022-10-20 14:00:12 CEST

--
-- PostgreSQL database dump complete
--


--
-- PostgreSQL database dump
--

-- Dumped from database version 11.14 (Debian 11.14-0+deb10u1)
-- Dumped by pg_dump version 14.1

-- Started on 2022-10-20 13:59:36 CEST

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
-- TOC entry 3117 (class 0 OID 133303)
-- Dependencies: 216
-- Data for Name: studytype; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.studytype (id, name, old_id) FROM stdin;
4	Experiment	\N
1	Relevance Assessment	0
2	Classification Task	1
5	Custom	2
3	IIR	\N
\.


--
-- TOC entry 3123 (class 0 OID 0)
-- Dependencies: 215
-- Name: studytype_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.studytype_id_seq', 5, true);


-- Completed on 2022-10-20 13:59:39 CEST

--
-- PostgreSQL database dump complete
--

--
-- PostgreSQL database dump
--

-- Dumped from database version 11.14 (Debian 11.14-0+deb10u1)
-- Dumped by pg_dump version 14.1

-- Started on 2022-10-20 13:59:14 CEST

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
-- TOC entry 3117 (class 0 OID 133248)
-- Dependencies: 209
-- Data for Name: searchengine; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.searchengine (id, name, config, old_id) FROM stdin;
1	Google	input/config/google.ini	1
2	Bing	input/config/bing.ini	2
3	Metager	input/config/metager.ini	3
4	Base Search	input/config/base_search.ini	4
5	DuckDuckGo	input/config/duckduckgo.ini	5
6	Amazon	input/config/amazon.ini	6
7	Blinde Kuh	input/config/blinde_kuh.ini	7
8	Ebay	input/config/ebay.ini	8
9	Econ Biz	input/config/econ_biz.ini	9
10	HAW Katalog	input/config/haw_katalog.ini	10
11	Stabi	input/config/stabi.ini	11
12	Youtube	input/config/youtube.ini	12
13	Stabi Artikel	input/config/stabi-artikel.ini	13
\.


--
-- TOC entry 3123 (class 0 OID 0)
-- Dependencies: 208
-- Name: searchengine_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.searchengine_id_seq', 13, true);


-- Completed on 2022-10-20 13:59:17 CEST

--
-- PostgreSQL database dump complete
--

--
-- PostgreSQL database dump
--

-- Dumped from database version 11.14 (Debian 11.14-0+deb10u1)
-- Dumped by pg_dump version 14.1

-- Started on 2022-10-20 13:58:48 CEST

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
-- TOC entry 3117 (class 0 OID 199680)
-- Dependencies: 259
-- Data for Name: resulttype; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.resulttype (id, name, display) FROM stdin;
1	Organic Results	organic
2	Snippets	snippet
3	Universal Search Results	universal
4	Advertisements	ad
\.


--
-- TOC entry 3123 (class 0 OID 0)
-- Dependencies: 258
-- Name: resulttype_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.resulttype_id_seq', 4, true);


-- Completed on 2022-10-20 13:58:51 CEST

--
-- PostgreSQL database dump complete
--

--
-- PostgreSQL database dump
--

-- Dumped from database version 11.14 (Debian 11.14-0+deb10u1)
-- Dumped by pg_dump version 14.1

-- Started on 2022-10-20 14:09:27 CEST

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
-- TOC entry 3117 (class 0 OID 133226)
-- Dependencies: 205
-- Data for Name: questiontype; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.questiontype (id, name, display) FROM stdin;
1	Short Text	short_text
2	Long Text	long_text
3	True/False	true_false
4	Rating Scale	likert_scale
5	Multiple Choice	multiple_choice
6	Number Scale	scale_number
\.


--
-- TOC entry 3123 (class 0 OID 0)
-- Dependencies: 204
-- Name: questiontype_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.questiontype_id_seq', 6, true);


-- Completed on 2022-10-20 14:09:30 CEST

--
-- PostgreSQL database dump complete
--
