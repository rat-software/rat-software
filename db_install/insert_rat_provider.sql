PGDMP                       |            rat3    11.20 (Debian 11.20-0+deb10u1)    16.0     G           0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                      false            H           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                      false            I           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                      false            J           1262    331697    rat3    DATABASE     p   CREATE DATABASE rat3 WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'de_DE.UTF-8';
    DROP DATABASE rat3;
                rat    false            D          0    354240    provider 
   TABLE DATA           ,   COPY public.provider (id, name) FROM stdin;
    public          rat    false    279   �       L           0    0    provider_id_seq    SEQUENCE SET     =   SELECT pg_catalog.setval('public.provider_id_seq', 4, true);
          public          rat    false    278            D   ;   x�3�t��O�I�2���L.�/�O+�2�tM�/�L�2�.IL�T�H�M*-J����� ���     