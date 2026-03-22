CREATE SCHEMA IF NOT EXISTS fhir;

-- Optional but helpful for JSONB indexing.
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- =========================================================
-- 1) Lossless raw store: every FHIR resource exactly as received
-- =========================================================
CREATE TABLE IF NOT EXISTS fhir.bundle (
    bundle_id           text PRIMARY KEY,
    bundle_type         text,
    source_filename     text,
    inserted_at         timestamptz NOT NULL DEFAULT now(),
    bundle_json         jsonb NOT NULL
);

CREATE TABLE IF NOT EXISTS fhir.resource_raw (
    resource_pk         bigserial PRIMARY KEY,
    bundle_id           text REFERENCES fhir.bundle(bundle_id) ON DELETE CASCADE,
    full_url            text,
    resource_type       text NOT NULL,
    resource_id         text NOT NULL,
    request_method      text,
    request_url         text,
    resource_json       jsonb NOT NULL,
    inserted_at         timestamptz NOT NULL DEFAULT now(),
    UNIQUE (resource_type, resource_id)
);

CREATE INDEX IF NOT EXISTS idx_resource_raw_type_id
    ON fhir.resource_raw (resource_type, resource_id);

CREATE INDEX IF NOT EXISTS idx_resource_raw_json_gin
    ON fhir.resource_raw USING gin (resource_json jsonb_path_ops);

CREATE INDEX IF NOT EXISTS idx_resource_raw_bundle
    ON fhir.resource_raw (bundle_id);

-- =========================================================
-- 2) Generic helper tables for repeated FHIR patterns
-- =========================================================
CREATE TABLE IF NOT EXISTS fhir.resource_identifier (
    id                  bigserial PRIMARY KEY,
    source_resource_pk  bigint NOT NULL REFERENCES fhir.resource_raw(resource_pk) ON DELETE CASCADE,
    source_resource_type text NOT NULL,
    source_resource_id  text NOT NULL,
    use_code            text,
    system              text,
    value               text,
    type_text           text,
    raw_json            jsonb NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_resource_identifier_src
    ON fhir.resource_identifier (source_resource_type, source_resource_id);
CREATE INDEX IF NOT EXISTS idx_resource_identifier_system_value
    ON fhir.resource_identifier (system, value);

CREATE TABLE IF NOT EXISTS fhir.resource_coding (
    id                  bigserial PRIMARY KEY,
    source_resource_pk  bigint NOT NULL REFERENCES fhir.resource_raw(resource_pk) ON DELETE CASCADE,
    source_resource_type text NOT NULL,
    source_resource_id  text NOT NULL,
    field_path          text NOT NULL,
    coding_idx          integer,
    system              text,
    code                text,
    display             text,
    raw_json            jsonb NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_resource_coding_src
    ON fhir.resource_coding (source_resource_type, source_resource_id);
CREATE INDEX IF NOT EXISTS idx_resource_coding_lookup
    ON fhir.resource_coding (system, code);

CREATE TABLE IF NOT EXISTS fhir.resource_reference (
    id                  bigserial PRIMARY KEY,
    source_resource_pk  bigint NOT NULL REFERENCES fhir.resource_raw(resource_pk) ON DELETE CASCADE,
    source_resource_type text NOT NULL,
    source_resource_id  text NOT NULL,
    field_path          text NOT NULL,
    target_reference    text NOT NULL,
    target_display      text,
    raw_json            jsonb NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_resource_reference_src
    ON fhir.resource_reference (source_resource_type, source_resource_id);
CREATE INDEX IF NOT EXISTS idx_resource_reference_target
    ON fhir.resource_reference (target_reference);

-- =========================================================
-- 3) Core domain tables for app queries
-- =========================================================
CREATE TABLE IF NOT EXISTS fhir.patient (
    patient_id          text PRIMARY KEY,
    resource_pk         bigint NOT NULL UNIQUE REFERENCES fhir.resource_raw(resource_pk) ON DELETE CASCADE,
    full_name           text,
    family_name         text,
    given_names         text[],
    gender              text,
    birth_date          date,
    marital_status      text,
    birth_sex           text,
    race_text           text,
    ethnicity_text      text,
    phone               text,
    city                text,
    state               text,
    postal_code         text,
    country             text,
    deceased_datetime   timestamptz,
    raw_json            jsonb NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_patient_name_trgm
    ON fhir.patient USING gin (full_name gin_trgm_ops);

CREATE TABLE IF NOT EXISTS fhir.encounter (
    encounter_id        text PRIMARY KEY,
    resource_pk         bigint NOT NULL UNIQUE REFERENCES fhir.resource_raw(resource_pk) ON DELETE CASCADE,
    patient_ref         text,
    patient_id          text,
    status              text,
    class_code          text,
    type_text           text,
    service_provider_ref text,
    service_provider_display text,
    location_ref        text,
    location_display    text,
    start_time          timestamptz,
    end_time            timestamptz,
    raw_json            jsonb NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_encounter_patient_id ON fhir.encounter(patient_id);
CREATE INDEX IF NOT EXISTS idx_encounter_start_time ON fhir.encounter(start_time);

CREATE TABLE IF NOT EXISTS fhir.condition (
    condition_id        text PRIMARY KEY,
    resource_pk         bigint NOT NULL UNIQUE REFERENCES fhir.resource_raw(resource_pk) ON DELETE CASCADE,
    patient_ref         text,
    patient_id          text,
    encounter_ref       text,
    encounter_id        text,
    clinical_status     text,
    verification_status text,
    category_text       text,
    code_system         text,
    code                text,
    code_display        text,
    onset_datetime      timestamptz,
    abatement_datetime  timestamptz,
    recorded_date       timestamptz,
    raw_json            jsonb NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_condition_patient_id ON fhir.condition(patient_id);
CREATE INDEX IF NOT EXISTS idx_condition_code ON fhir.condition(code_system, code);

CREATE TABLE IF NOT EXISTS fhir.observation (
    observation_id      text PRIMARY KEY,
    resource_pk         bigint NOT NULL UNIQUE REFERENCES fhir.resource_raw(resource_pk) ON DELETE CASCADE,
    patient_ref         text,
    patient_id          text,
    encounter_ref       text,
    encounter_id        text,
    status              text,
    category_text       text,
    code_system         text,
    code                text,
    code_display        text,
    effective_time      timestamptz,
    issued_time         timestamptz,
    value_type          text,
    value_num           numeric,
    value_unit          text,
    value_code          text,
    value_display       text,
    value_text          text,
    raw_json            jsonb NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_observation_patient_id ON fhir.observation(patient_id);
CREATE INDEX IF NOT EXISTS idx_observation_code ON fhir.observation(code_system, code);
CREATE INDEX IF NOT EXISTS idx_observation_effective_time ON fhir.observation(effective_time);

CREATE TABLE IF NOT EXISTS fhir.diagnostic_report (
    diagnostic_report_id text PRIMARY KEY,
    resource_pk         bigint NOT NULL UNIQUE REFERENCES fhir.resource_raw(resource_pk) ON DELETE CASCADE,
    patient_ref         text,
    patient_id          text,
    encounter_ref       text,
    encounter_id        text,
    status              text,
    code_system         text,
    code                text,
    code_display        text,
    effective_time      timestamptz,
    issued_time         timestamptz,
    note_text_base64    text,
    raw_json            jsonb NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_diagnostic_report_patient_id ON fhir.diagnostic_report(patient_id);
CREATE INDEX IF NOT EXISTS idx_diagnostic_report_encounter_id ON fhir.diagnostic_report(encounter_id);

CREATE TABLE IF NOT EXISTS fhir.document_reference (
    document_reference_id text PRIMARY KEY,
    resource_pk         bigint NOT NULL UNIQUE REFERENCES fhir.resource_raw(resource_pk) ON DELETE CASCADE,
    patient_ref         text,
    patient_id          text,
    status              text,
    type_text           text,
    category_text       text,
    author_ref          text,
    author_display      text,
    custodian_ref       text,
    custodian_display   text,
    document_date       timestamptz,
    encounter_ref       text,
    encounter_id        text,
    content_type        text,
    content_data_base64 text,
    raw_json            jsonb NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_document_reference_patient_id ON fhir.document_reference(patient_id);
CREATE INDEX IF NOT EXISTS idx_document_reference_encounter_id ON fhir.document_reference(encounter_id);

CREATE TABLE IF NOT EXISTS fhir.claim (
    claim_id            text PRIMARY KEY,
    resource_pk         bigint NOT NULL UNIQUE REFERENCES fhir.resource_raw(resource_pk) ON DELETE CASCADE,
    patient_ref         text,
    patient_id          text,
    status              text,
    use_code            text,
    type_code           text,
    type_display        text,
    provider_ref        text,
    provider_display    text,
    facility_ref        text,
    facility_display    text,
    billable_start      timestamptz,
    billable_end        timestamptz,
    created_time        timestamptz,
    priority_code       text,
    total_value         numeric,
    total_currency      text,
    raw_json            jsonb NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_claim_patient_id ON fhir.claim(patient_id);
CREATE INDEX IF NOT EXISTS idx_claim_created_time ON fhir.claim(created_time);

CREATE TABLE IF NOT EXISTS fhir.claim_item (
    claim_item_pk       bigserial PRIMARY KEY,
    claim_id            text NOT NULL REFERENCES fhir.claim(claim_id) ON DELETE CASCADE,
    sequence_no         integer,
    product_system      text,
    product_code        text,
    product_display     text,
    encounter_ref       text,
    encounter_id        text,
    serviced_start      timestamptz,
    serviced_end        timestamptz,
    diagnosis_sequence  integer[],
    raw_json            jsonb NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_claim_item_claim_id ON fhir.claim_item(claim_id);
CREATE INDEX IF NOT EXISTS idx_claim_item_encounter_id ON fhir.claim_item(encounter_id);

CREATE TABLE IF NOT EXISTS fhir.explanation_of_benefit (
    eob_id              text PRIMARY KEY,
    resource_pk         bigint NOT NULL UNIQUE REFERENCES fhir.resource_raw(resource_pk) ON DELETE CASCADE,
    patient_ref         text,
    patient_id          text,
    status              text,
    use_code            text,
    type_code           text,
    type_display        text,
    claim_ref           text,
    claim_id            text,
    provider_ref        text,
    facility_ref        text,
    insurer_display     text,
    outcome             text,
    billable_start      timestamptz,
    billable_end        timestamptz,
    created_time        timestamptz,
    payment_amount      numeric,
    payment_currency    text,
    raw_json            jsonb NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_eob_patient_id ON fhir.explanation_of_benefit(patient_id);
CREATE INDEX IF NOT EXISTS idx_eob_claim_id ON fhir.explanation_of_benefit(claim_id);

CREATE TABLE IF NOT EXISTS fhir.eob_item (
    eob_item_pk         bigserial PRIMARY KEY,
    eob_id              text NOT NULL REFERENCES fhir.explanation_of_benefit(eob_id) ON DELETE CASCADE,
    sequence_no         integer,
    category_system     text,
    category_code       text,
    category_display    text,
    product_system      text,
    product_code        text,
    product_display     text,
    encounter_ref       text,
    encounter_id        text,
    serviced_start      timestamptz,
    serviced_end        timestamptz,
    diagnosis_sequence  integer[],
    raw_json            jsonb NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_eob_item_eob_id ON fhir.eob_item(eob_id);
CREATE INDEX IF NOT EXISTS idx_eob_item_encounter_id ON fhir.eob_item(encounter_id);

CREATE TABLE IF NOT EXISTS fhir.eob_total (
    eob_total_pk        bigserial PRIMARY KEY,
    eob_id              text NOT NULL REFERENCES fhir.explanation_of_benefit(eob_id) ON DELETE CASCADE,
    category_system     text,
    category_code       text,
    category_display    text,
    amount_value        numeric,
    amount_currency     text,
    raw_json            jsonb NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_eob_total_eob_id ON fhir.eob_total(eob_id);

CREATE TABLE IF NOT EXISTS fhir.medication (
    medication_id       text PRIMARY KEY,
    resource_pk         bigint NOT NULL UNIQUE REFERENCES fhir.resource_raw(resource_pk) ON DELETE CASCADE,
    status              text,
    code_system         text,
    code                text,
    code_display        text,
    raw_json            jsonb NOT NULL
);

CREATE TABLE IF NOT EXISTS fhir.medication_request (
    medication_request_id text PRIMARY KEY,
    resource_pk         bigint NOT NULL UNIQUE REFERENCES fhir.resource_raw(resource_pk) ON DELETE CASCADE,
    patient_ref         text,
    patient_id          text,
    encounter_ref       text,
    encounter_id        text,
    status              text,
    intent              text,
    authored_on         timestamptz,
    medication_ref      text,
    medication_id       text,
    medication_text     text,
    requester_ref       text,
    requester_display   text,
    raw_json            jsonb NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_med_request_patient_id ON fhir.medication_request(patient_id);
CREATE INDEX IF NOT EXISTS idx_med_request_encounter_id ON fhir.medication_request(encounter_id);

CREATE TABLE IF NOT EXISTS fhir.medication_administration (
    medication_administration_id text PRIMARY KEY,
    resource_pk         bigint NOT NULL UNIQUE REFERENCES fhir.resource_raw(resource_pk) ON DELETE CASCADE,
    patient_ref         text,
    patient_id          text,
    encounter_ref       text,
    encounter_id        text,
    status              text,
    effective_time      timestamptz,
    medication_text     text,
    raw_json            jsonb NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_med_admin_patient_id ON fhir.medication_administration(patient_id);

CREATE TABLE IF NOT EXISTS fhir.procedure (
    procedure_id        text PRIMARY KEY,
    resource_pk         bigint NOT NULL UNIQUE REFERENCES fhir.resource_raw(resource_pk) ON DELETE CASCADE,
    patient_ref         text,
    patient_id          text,
    encounter_ref       text,
    encounter_id        text,
    status              text,
    code_system         text,
    code                text,
    code_display        text,
    location_ref        text,
    location_display    text,
    performed_start     timestamptz,
    performed_end       timestamptz,
    raw_json            jsonb NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_procedure_patient_id ON fhir.procedure(patient_id);
CREATE INDEX IF NOT EXISTS idx_procedure_encounter_id ON fhir.procedure(encounter_id);

CREATE TABLE IF NOT EXISTS fhir.immunization (
    immunization_id     text PRIMARY KEY,
    resource_pk         bigint NOT NULL UNIQUE REFERENCES fhir.resource_raw(resource_pk) ON DELETE CASCADE,
    patient_ref         text,
    patient_id          text,
    encounter_ref       text,
    encounter_id        text,
    status              text,
    occurrence_time     timestamptz,
    vaccine_system      text,
    vaccine_code        text,
    vaccine_display     text,
    location_ref        text,
    location_display    text,
    raw_json            jsonb NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_immunization_patient_id ON fhir.immunization(patient_id);

CREATE TABLE IF NOT EXISTS fhir.imaging_study (
    imaging_study_id    text PRIMARY KEY,
    resource_pk         bigint NOT NULL UNIQUE REFERENCES fhir.resource_raw(resource_pk) ON DELETE CASCADE,
    patient_ref         text,
    patient_id          text,
    encounter_ref       text,
    encounter_id        text,
    status              text,
    started_time        timestamptz,
    location_ref        text,
    location_display    text,
    number_of_series    integer,
    number_of_instances integer,
    raw_json            jsonb NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_imaging_study_patient_id ON fhir.imaging_study(patient_id);

CREATE TABLE IF NOT EXISTS fhir.device (
    device_id           text PRIMARY KEY,
    resource_pk         bigint NOT NULL UNIQUE REFERENCES fhir.resource_raw(resource_pk) ON DELETE CASCADE,
    patient_ref         text,
    patient_id          text,
    status              text,
    distinct_identifier text,
    serial_number       text,
    lot_number          text,
    manufacture_date    timestamptz,
    expiration_date     timestamptz,
    type_text           text,
    raw_json            jsonb NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_device_patient_id ON fhir.device(patient_id);

CREATE TABLE IF NOT EXISTS fhir.care_team (
    care_team_id        text PRIMARY KEY,
    resource_pk         bigint NOT NULL UNIQUE REFERENCES fhir.resource_raw(resource_pk) ON DELETE CASCADE,
    patient_ref         text,
    patient_id          text,
    encounter_ref       text,
    encounter_id        text,
    status              text,
    raw_json            jsonb NOT NULL
);

CREATE TABLE IF NOT EXISTS fhir.care_plan (
    care_plan_id        text PRIMARY KEY,
    resource_pk         bigint NOT NULL UNIQUE REFERENCES fhir.resource_raw(resource_pk) ON DELETE CASCADE,
    patient_ref         text,
    patient_id          text,
    encounter_ref       text,
    encounter_id        text,
    status              text,
    intent              text,
    start_time          timestamptz,
    end_time            timestamptz,
    raw_json            jsonb NOT NULL
);

CREATE TABLE IF NOT EXISTS fhir.provenance (
    provenance_id       text PRIMARY KEY,
    resource_pk         bigint NOT NULL UNIQUE REFERENCES fhir.resource_raw(resource_pk) ON DELETE CASCADE,
    recorded_time       timestamptz,
    raw_json            jsonb NOT NULL
);

-- =========================================================
-- 4) Helpful views for common app queries
-- =========================================================
CREATE OR REPLACE VIEW fhir.v_patient_encounters AS
SELECT
    p.patient_id,
    p.full_name,
    e.encounter_id,
    e.start_time,
    e.end_time,
    e.type_text,
    e.service_provider_display,
    e.location_display
FROM fhir.patient p
LEFT JOIN fhir.encounter e ON e.patient_id = p.patient_id;

CREATE OR REPLACE VIEW fhir.v_patient_claim_summary AS
SELECT
    c.patient_id,
    c.claim_id,
    c.created_time,
    c.type_display,
    c.provider_display,
    c.total_value,
    c.total_currency,
    e.eob_id,
    e.outcome,
    e.payment_amount,
    e.payment_currency,
    e.insurer_display
FROM fhir.claim c
LEFT JOIN fhir.explanation_of_benefit e ON e.claim_id = c.claim_id;

CREATE OR REPLACE VIEW fhir.v_recent_labs AS
SELECT
    o.patient_id,
    o.observation_id,
    o.effective_time,
    o.code_display,
    o.value_num,
    o.value_unit,
    o.value_text,
    o.value_display
FROM fhir.observation o
WHERE o.category_text = 'laboratory' OR o.code_system = 'http://loinc.org';
