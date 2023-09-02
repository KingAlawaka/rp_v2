drop table if exists trans_tbl;
drop table if exists data_tbl;
drop table if exists subs_external_tbl;
drop table if exists subs_internal_tbl;
drop table if exists formula_cal_tbl;
drop table if exists formula_config_tbl;
drop table if exists data_dt_gen_tbl;
drop table if EXISTS cal_data_tbl;
drop table if EXISTS data_sent_tbl;
drop table if EXISTS qos_tbl;
drop table if EXISTS stdev_tbl;
drop table if EXISTS stdev_qos_tbl;
drop table if EXISTS final_value_tbl;
drop table if EXISTS dt_details_tbl;
drop table if EXISTS trend_analysis_tbl;

--record all the internal transaction happening in the DT
create table trans_tbl(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    trans TEXT NOT NULL,
    status INTEGER
);

create table qos_tbl(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    DT_ID INTEGER,
    API_ID INTEGER,
    elapsed_time float,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status INTEGER
);

-- trend analysis lib output
-- https://pypi.org/project/pymannkendall/
-- trend: tells the trend (increasing, decreasing or no trend)
-- h: True (if trend is present) or False (if the trend is absence)
-- p: p-value of the significance test
-- z: normalized test statistics
-- Tau: Kendall Tau
-- s: Mann-Kendal's score
-- var_s: Variance S
-- slope: Theil-Sen estimator/slope
-- intercept: intercept of Kendall-Theil Robust Line, for seasonal test, full period cycle consider as unit time step

create table trend_analysis_tbl(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    DT_ID INTEGER,
    type text, -- DT data, qos, or what type of data is analyzed
    trend text,
    h text,
    p float,
    z float,
    tau float,
    s float,
    var_s float,
    slope text,
    intercept float,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status INTEGER
);

create table dt_details_tbl(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    DT_ID INTEGER,
    type text,
    url text,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status INTEGER
);

--Standard deviation for each DT
create table stdev_tbl(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    DT_ID INTEGER,
    stdev_value float,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status INTEGER
);

create table final_value_tbl(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    DT_ID INTEGER, -- -1 to indicate final value
    data_type text,
    stdev_value float,
    min float,
    max float,
    avg float,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status INTEGER
);

-- QoS Standard deviation for each DT
create table stdev_qos_tbl(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    DT_ID INTEGER,
    stdev_value float,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status INTEGER
);

--record all the external transactions. When want to calculate the function get the next available value if used =0
create table data_tbl(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    req_type text,
    DT_ID INTEGER,
    API_ID integer,
    value float,
    used int, -- if value used to calculate the value 1 otherwise 0
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status INTEGER
);

--record all the values DT send to others
--DT_ID = DT that going to get the value
create table data_sent_tbl(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    req_type text,
    reciever_DT_ID INTEGER,
    API_ID integer,
    value float,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status INTEGER
);

--record DT generated values for calculation
create table data_dt_gen_tbl(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    formula_cal_id int,
    val_pos int,
    value float,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status INTEGER
);

--all the values use to calculate
--source means internal or external i= internal e=external
create table cal_data_tbl(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    formula_cal_id int,
    source text,
    val_pos int,
    value float,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status INTEGER
);

--subscriber table to record values need to send to others
--DT means subscribed DT and API ID means DT that going to give values
--URL means where values need to be send (POST)
--GET requests are not responsibility of the hosting DT. Other DT need to get that value
create table subs_external_tbl(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    direction text, --to (out) or from (in) 
    req_type text,
    DT_ID integer,
    API_ID integer,
    url text,
    ex_dt_url text,
    status integer, -- status 1 for use based on the trust index service can be terminate request DTTSA to provide a new DT
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

--subscriptions for internal calculations
create table subs_internal_tbl(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    direction text, --to (out) or from (in) 
    req_type text,
    DT_ID integer,
    API_ID integer,
    url text,
    formula_position integer,
    status integer, -- status 1 for use based on the trust index service can be terminate request DTTSA to provide a new DT
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


--calculation table
create table formula_cal_tbl(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    formula text,
    calculated float, 
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status INTEGER
);

--formula table
create table formula_config_tbl(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    DT_ID integer,
    API_ID integer,
    formula_position integer,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status INTEGER
);


