--
-- PostgreSQL database dump
--

-- Dumped from database version 11.20 (Debian 11.20-0+deb10u1)
-- Dumped by pg_dump version 16.0

-- Started on 2023-11-29 12:01:35

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
-- TOC entry 3135 (class 0 OID 332452)
-- Dependencies: 269
-- Data for Name: classifier; Type: TABLE DATA; Schema: public; Owner: rat
--

INSERT INTO public.classifier (id, name, display_name) VALUES (1, 'seo_rule_based', 'SEO (rule-based)');


--
-- TOC entry 3141 (class 0 OID 0)
-- Dependencies: 268
-- Name: classifier_id_seq; Type: SEQUENCE SET; Schema: public; Owner: rat
--

SELECT pg_catalog.setval('public.classifier_id_seq', 1, false);


-- Completed on 2023-11-29 12:01:38

--
-- PostgreSQL database dump complete
--

