--
-- PostgreSQL database dump
--

-- Dumped from database version 11.20 (Debian 11.20-0+deb10u1)
-- Dumped by pg_dump version 16.0

-- Started on 2023-11-29 11:53:23

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
-- TOC entry 3135 (class 0 OID 331957)
-- Dependencies: 261
-- Data for Name: studytype; Type: TABLE DATA; Schema: public; Owner: rat
--

INSERT INTO public.studytype (id, name) VALUES (1, 'Relevance Assessment');
INSERT INTO public.studytype (id, name) VALUES (2, 'Classification Task');
INSERT INTO public.studytype (id, name) VALUES (4, 'Experiment');
INSERT INTO public.studytype (id, name) VALUES (5, 'Custom');
INSERT INTO public.studytype (id, name) VALUES (3, 'Interactive Information Retrieval');


--
-- TOC entry 3143 (class 0 OID 0)
-- Dependencies: 262
-- Name: studytype_id_seq; Type: SEQUENCE SET; Schema: public; Owner: rat
--

SELECT pg_catalog.setval('public.studytype_id_seq', 6, true);


-- Completed on 2023-11-29 11:53:26

--
-- PostgreSQL database dump complete
--

