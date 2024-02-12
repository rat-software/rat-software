--
-- PostgreSQL database dump
--

-- Dumped from database version 11.20 (Debian 11.20-0+deb10u1)
-- Dumped by pg_dump version 16.0

-- Started on 2023-11-29 11:52:10

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
-- TOC entry 3135 (class 0 OID 331911)
-- Dependencies: 249
-- Data for Name: searchengine; Type: TABLE DATA; Schema: public; Owner: rat
--

INSERT INTO public.searchengine VALUES (1, 'Google_DE', 'google_de.py', 1, NULL, 1, '1');
INSERT INTO public.searchengine VALUES (2, 'Bing_DE', 'bing_de.py', 1, NULL, 1, '1');
INSERT INTO public.searchengine VALUES (3, 'Google_SE', 'google_se.py', 1, NULL, 1, '3');
INSERT INTO public.searchengine VALUES (4, 'Ecosia_DE', 'ecosia_de.py', -1, NULL, 1, '1');
INSERT INTO public.searchengine VALUES (5, 'Katalogplus Bücher & mehr ', 'katalogplus_de_books.py', 1, NULL, 1, '1');
INSERT INTO public.searchengine VALUES (6, 'Katalogplus Artikel', 'katalogplus_de_articles.py', 1, NULL, 1, '1');
INSERT INTO public.searchengine VALUES (8, 'Google_US', 'google_us.py', 1, NULL, 1, '2');
INSERT INTO public.searchengine VALUES (9, 'Google_News_DE', 'google_news_de.py', -1, NULL, 5, '1');
INSERT INTO public.searchengine VALUES (10, 'Google_News_IE', 'google_news_ie.py', -1, NULL, 5, '4');
INSERT INTO public.searchengine VALUES (11, 'Google_News_MX', 'google_news_mx.py', -1, NULL, 5, '5');
INSERT INTO public.searchengine VALUES (12, 'Google_News_SE', 'google_news_se.py', -1, NULL, 5, '3');
INSERT INTO public.searchengine VALUES (13, 'Google_News_US', 'google_news_us.py', -1, NULL, 5, '2');


--
-- TOC entry 3143 (class 0 OID 0)
-- Dependencies: 250
-- Name: searchengine_id_seq; Type: SEQUENCE SET; Schema: public; Owner: rat
--

SELECT pg_catalog.setval('public.searchengine_id_seq', 5, true);


-- Completed on 2023-11-29 11:52:13

--
-- PostgreSQL database dump complete
--

