INSERT INTO public.search_engine(name, config) VALUES ('Google', '/config/google.ini');
INSERT INTO public.search_engine(name, config) VALUES ('Bing', '/config/bing.ini');
INSERT INTO public.search_engine(name, config) VALUES ('DuckDuckGo', '/config/duckduckgo.ini');
INSERT INTO public.search_engine(name, config) VALUES ('Metager', '/config/metager.ini');
INSERT INTO public.search_engine(name, config) VALUES ('Amazon', '/config/amazong.ini');
INSERT INTO public.search_engine(name, config) VALUES ('Ebay', '/config/ebay.ini');

INSERT INTO public.study_type(name) VALUES ('Relevance Assessment');
INSERT INTO public.study_type(name) VALUES ('Classification Task');
INSERT INTO public.study_type(name) VALUES ('Custom');

ALTER TABLE public.question_type ADD display text;

INSERT INTO public.question_type(name, display) VALUES ('Short Text', 'short-text');
INSERT INTO public.question_type(name, display) VALUES ('Long Text', 'long-text');
INSERT INTO public.question_type(name, display) VALUES ('True/False', 'true-false');
INSERT INTO public.question_type(name, display) VALUES ('Likert Scale', 'likert-scale');
INSERT INTO public.question_type(name, display) VALUES ('Multiple Choice', 'multiple-choice');
INSERT INTO public.question_type(name, display) VALUES ('Scale Number', 'scale-number');
