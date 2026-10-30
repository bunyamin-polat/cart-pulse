-- Star schema generated from the pgAdmin ERD. Identifiers are quoted because the course
-- requires these mixed-case names and PostgreSQL folds unquoted names to lower case.
-- Foreign keys are inline so dimensions must exist first and IF NOT EXISTS keeps re-runs safe.
BEGIN;

CREATE TABLE IF NOT EXISTS public."softcartDimDate" (
    dateid      integer NOT NULL,
    date        date NOT NULL,
    year        integer NOT NULL,
    quarter     integer NOT NULL,
    quartername character varying(2) NOT NULL,
    month       integer NOT NULL,
    monthname   character varying(10) NOT NULL,
    day         integer NOT NULL,
    weekday     integer NOT NULL,
    weekdayname character varying(10) NOT NULL,
    PRIMARY KEY (dateid)
);

CREATE TABLE IF NOT EXISTS public."softcartDimCategory" (
    categoryid integer NOT NULL,
    category   character varying(50) NOT NULL,
    PRIMARY KEY (categoryid)
);

CREATE TABLE IF NOT EXISTS public."softcartDimItem" (
    itemid integer NOT NULL,
    item   character varying(255) NOT NULL,
    PRIMARY KEY (itemid)
);

CREATE TABLE IF NOT EXISTS public."softcartDimCountry" (
    countryid integer NOT NULL,
    country   character varying(100) NOT NULL,
    PRIMARY KEY (countryid)
);

CREATE TABLE IF NOT EXISTS public."softcartFactSales" (
    orderid    integer NOT NULL,
    dateid     integer NOT NULL REFERENCES public."softcartDimDate" (dateid),
    categoryid integer NOT NULL REFERENCES public."softcartDimCategory" (categoryid),
    itemid     integer NOT NULL REFERENCES public."softcartDimItem" (itemid),
    countryid  integer NOT NULL REFERENCES public."softcartDimCountry" (countryid),
    price      numeric(10, 2) NOT NULL,
    PRIMARY KEY (orderid)
);

COMMIT;
