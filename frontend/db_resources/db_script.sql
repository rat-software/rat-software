CREATE TABLE "query" (
  "id" SERIAL PRIMARY KEY,
  "name" TEXT NOT NULL,
  "timestamp" TIMESTAMP NOT NULL,
  "description" TEXT NOT NULL,
  "query" TEXT NOT NULL
);

CREATE TABLE "question_template" (
  "id" SERIAL PRIMARY KEY,
  "name" TEXT NOT NULL,
  "description" TEXT NOT NULL
);

CREATE TABLE "question_type" (
  "id" SERIAL PRIMARY KEY,
  "name" TEXT NOT NULL,
  "display" TEXT NOT NULL
);

CREATE TABLE "scarper" (
  "id" SERIAL PRIMARY KEY,
  "progress" INTEGER NOT NULL,
  "limit" INTEGER,
  "timestamp" TIMESTAMP NOT NULL,
  "error_code" INTEGER
);

CREATE TABLE "query_scarper" (
  "query" INTEGER NOT NULL,
  "scarper" INTEGER NOT NULL,
  PRIMARY KEY ("query", "scarper")
);

CREATE INDEX "idx_query_scarper" ON "query_scarper" ("scarper");

ALTER TABLE "query_scarper" ADD CONSTRAINT "fk_query_scarper__query" FOREIGN KEY ("query") REFERENCES "query" ("id");

ALTER TABLE "query_scarper" ADD CONSTRAINT "fk_query_scarper__scarper" FOREIGN KEY ("scarper") REFERENCES "scarper" ("id");

CREATE TABLE "search_engine" (
  "id" SERIAL PRIMARY KEY,
  "name" TEXT NOT NULL,
  "config" TEXT NOT NULL
);

CREATE TABLE "scarper_search_engine" (
  "scarper" INTEGER NOT NULL,
  "search_engine" INTEGER NOT NULL,
  PRIMARY KEY ("scarper", "search_engine")
);

CREATE INDEX "idx_scarper_search_engine" ON "scarper_search_engine" ("search_engine");

ALTER TABLE "scarper_search_engine" ADD CONSTRAINT "fk_scarper_search_engine__scarper" FOREIGN KEY ("scarper") REFERENCES "scarper" ("id");

ALTER TABLE "scarper_search_engine" ADD CONSTRAINT "fk_scarper_search_engine__search_engine" FOREIGN KEY ("search_engine") REFERENCES "search_engine" ("id");

CREATE TABLE "serp" (
  "id" SERIAL PRIMARY KEY,
  "page" INTEGER NOT NULL,
  "code" TEXT NOT NULL,
  "img" TEXT NOT NULL,
  "progress" INTEGER NOT NULL,
  "timestamp" TIMESTAMP NOT NULL
);

CREATE TABLE "source" (
  "id" SERIAL PRIMARY KEY,
  "code" TEXT NOT NULL,
  "bin" TEXT NOT NULL,
  "url" TEXT NOT NULL,
  "progress" INTEGER NOT NULL,
  "mime_type" TEXT NOT NULL,
  "error_code" TEXT NOT NULL,
  "status_code" INTEGER,
  "final_url" TEXT NOT NULL,
  "timestamp" TIMESTAMP NOT NULL
);

CREATE TABLE "result" (
  "id" SERIAL PRIMARY KEY,
  "url" TEXT NOT NULL,
  "query" INTEGER NOT NULL,
  "scarper" INTEGER NOT NULL,
  "position" INTEGER NOT NULL,
  "main" TEXT NOT NULL,
  "title" TEXT NOT NULL,
  "description" TEXT NOT NULL,
  "timestamp" TIMESTAMP NOT NULL,
  "ip" TEXT NOT NULL,
  "origin" TEXT NOT NULL,
  "serp" INTEGER NOT NULL,
  "source" INTEGER NOT NULL
);

CREATE INDEX "idx_result__query" ON "result" ("query");

CREATE INDEX "idx_result__scarper" ON "result" ("scarper");

CREATE INDEX "idx_result__serp" ON "result" ("serp");

CREATE INDEX "idx_result__source" ON "result" ("source");

ALTER TABLE "result" ADD CONSTRAINT "fk_result__query" FOREIGN KEY ("query") REFERENCES "query" ("id") ON DELETE CASCADE;

ALTER TABLE "result" ADD CONSTRAINT "fk_result__scarper" FOREIGN KEY ("scarper") REFERENCES "scarper" ("id") ON DELETE CASCADE;

ALTER TABLE "result" ADD CONSTRAINT "fk_result__serp" FOREIGN KEY ("serp") REFERENCES "serp" ("id") ON DELETE CASCADE;

ALTER TABLE "result" ADD CONSTRAINT "fk_result__source" FOREIGN KEY ("source") REFERENCES "source" ("id") ON DELETE CASCADE;

CREATE TABLE "result_search_engine" (
  "result" INTEGER NOT NULL,
  "search_engine" INTEGER NOT NULL,
  PRIMARY KEY ("result", "search_engine")
);

CREATE INDEX "idx_result_search_engine" ON "result_search_engine" ("search_engine");

ALTER TABLE "result_search_engine" ADD CONSTRAINT "fk_result_search_engine__result" FOREIGN KEY ("result") REFERENCES "result" ("id");

ALTER TABLE "result_search_engine" ADD CONSTRAINT "fk_result_search_engine__search_engine" FOREIGN KEY ("search_engine") REFERENCES "search_engine" ("id");

CREATE TABLE "study" (
  "id" SERIAL PRIMARY KEY,
  "name" TEXT NOT NULL,
  "timestamp" TIMESTAMP,
  "description" TEXT NOT NULL,
  "imported" BOOLEAN
);

CREATE TABLE "query_study" (
  "query" INTEGER NOT NULL,
  "study" INTEGER NOT NULL,
  PRIMARY KEY ("query", "study")
);

CREATE INDEX "idx_query_study" ON "query_study" ("study");

ALTER TABLE "query_study" ADD CONSTRAINT "fk_query_study__query" FOREIGN KEY ("query") REFERENCES "query" ("id");

ALTER TABLE "query_study" ADD CONSTRAINT "fk_query_study__study" FOREIGN KEY ("study") REFERENCES "study" ("id");

CREATE TABLE "question" (
  "id" SERIAL PRIMARY KEY,
  "title" TEXT NOT NULL,
  "description" TEXT NOT NULL,
  "question__type" INTEGER NOT NULL,
  "study" INTEGER NOT NULL
);

CREATE INDEX "idx_question__question__type" ON "question" ("question__type");

CREATE INDEX "idx_question__study" ON "question" ("study");

ALTER TABLE "question" ADD CONSTRAINT "fk_question__question__type" FOREIGN KEY ("question__type") REFERENCES "question_type" ("id") ON DELETE CASCADE;

ALTER TABLE "question" ADD CONSTRAINT "fk_question__study" FOREIGN KEY ("study") REFERENCES "study" ("id") ON DELETE CASCADE;

CREATE TABLE "answer" (
  "id" SERIAL PRIMARY KEY,
  "result" INTEGER,
  "value" TEXT NOT NULL,
  "question" INTEGER NOT NULL
);

CREATE INDEX "idx_answer__question" ON "answer" ("question");

CREATE INDEX "idx_answer__result" ON "answer" ("result");

ALTER TABLE "answer" ADD CONSTRAINT "fk_answer__question" FOREIGN KEY ("question") REFERENCES "question" ("id") ON DELETE CASCADE;

ALTER TABLE "answer" ADD CONSTRAINT "fk_answer__result" FOREIGN KEY ("result") REFERENCES "result" ("id") ON DELETE SET NULL;

CREATE TABLE "option" (
  "id" SERIAL PRIMARY KEY,
  "value" TEXT NOT NULL,
  "label" TEXT NOT NULL,
  "position" INTEGER,
  "question" INTEGER
);

CREATE INDEX "idx_option__question" ON "option" ("question");

ALTER TABLE "option" ADD CONSTRAINT "fk_option__question" FOREIGN KEY ("question") REFERENCES "question" ("id") ON DELETE SET NULL;

CREATE TABLE "question_question_template" (
  "question" INTEGER NOT NULL,
  "question_template" INTEGER NOT NULL,
  PRIMARY KEY ("question", "question_template")
);

CREATE INDEX "idx_question_question_template" ON "question_question_template" ("question_template");

ALTER TABLE "question_question_template" ADD CONSTRAINT "fk_question_question_template__question" FOREIGN KEY ("question") REFERENCES "question" ("id");

ALTER TABLE "question_question_template" ADD CONSTRAINT "fk_question_question_template__question_template" FOREIGN KEY ("question_template") REFERENCES "question_template" ("id");

CREATE TABLE "result_study" (
  "result" INTEGER NOT NULL,
  "study" INTEGER NOT NULL,
  PRIMARY KEY ("result", "study")
);

CREATE INDEX "idx_result_study" ON "result_study" ("study");

ALTER TABLE "result_study" ADD CONSTRAINT "fk_result_study__result" FOREIGN KEY ("result") REFERENCES "result" ("id");

ALTER TABLE "result_study" ADD CONSTRAINT "fk_result_study__study" FOREIGN KEY ("study") REFERENCES "study" ("id");

CREATE TABLE "scarper_study" (
  "scarper" INTEGER NOT NULL,
  "study" INTEGER NOT NULL,
  PRIMARY KEY ("scarper", "study")
);

CREATE INDEX "idx_scarper_study" ON "scarper_study" ("study");

ALTER TABLE "scarper_study" ADD CONSTRAINT "fk_scarper_study__scarper" FOREIGN KEY ("scarper") REFERENCES "scarper" ("id");

ALTER TABLE "scarper_study" ADD CONSTRAINT "fk_scarper_study__study" FOREIGN KEY ("study") REFERENCES "study" ("id");

CREATE TABLE "search_engine_study" (
  "search_engine" INTEGER NOT NULL,
  "study" INTEGER NOT NULL,
  PRIMARY KEY ("search_engine", "study")
);

CREATE INDEX "idx_search_engine_study" ON "search_engine_study" ("study");

ALTER TABLE "search_engine_study" ADD CONSTRAINT "fk_search_engine_study__search_engine" FOREIGN KEY ("search_engine") REFERENCES "search_engine" ("id");

ALTER TABLE "search_engine_study" ADD CONSTRAINT "fk_search_engine_study__study" FOREIGN KEY ("study") REFERENCES "study" ("id");

CREATE TABLE "study_type" (
  "id" SERIAL PRIMARY KEY,
  "name" TEXT NOT NULL
);

CREATE TABLE "study_study_type" (
  "study" INTEGER NOT NULL,
  "study_type" INTEGER NOT NULL,
  PRIMARY KEY ("study", "study_type")
);

CREATE INDEX "idx_study_study_type" ON "study_study_type" ("study_type");

ALTER TABLE "study_study_type" ADD CONSTRAINT "fk_study_study_type__study" FOREIGN KEY ("study") REFERENCES "study" ("id");

ALTER TABLE "study_study_type" ADD CONSTRAINT "fk_study_study_type__study_type" FOREIGN KEY ("study_type") REFERENCES "study_type" ("id");

CREATE TABLE "trend" (
  "id" SERIAL PRIMARY KEY,
  "query" TEXT NOT NULL,
  "traffic" INTEGER NOT NULL,
  "related_queries" TEXT NOT NULL,
  "sample_article" TEXT NOT NULL,
  "date" TIMESTAMP NOT NULL,
  "country" TEXT NOT NULL,
  "position" INTEGER NOT NULL,
  "timestamp" TIMESTAMP NOT NULL
);
