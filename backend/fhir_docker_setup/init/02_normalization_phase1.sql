CREATE TABLE IF NOT EXISTS fhir.code (
    code_pk     bigserial PRIMARY KEY,
    system      text NOT NULL,
    code        text NOT NULL,
    display     text,
    UNIQUE (system, code)
);

CREATE INDEX IF NOT EXISTS idx_code_system_code ON fhir.code (system, code);

INSERT INTO fhir.code (system, code, display)
SELECT DISTINCT code_system, code, code_display
FROM fhir.condition
WHERE code_system IS NOT NULL AND code IS NOT NULL
ON CONFLICT (system, code) DO NOTHING;

INSERT INTO fhir.code (system, code, display)
SELECT DISTINCT code_system, code, code_display
FROM fhir.observation
WHERE code_system IS NOT NULL AND code IS NOT NULL
ON CONFLICT (system, code) DO NOTHING;

INSERT INTO fhir.code (system, code, display)
SELECT DISTINCT code_system, code, code_display
FROM fhir.procedure
WHERE code_system IS NOT NULL AND code IS NOT NULL
ON CONFLICT (system, code) DO NOTHING;

INSERT INTO fhir.code (system, code, display)
SELECT DISTINCT vaccine_system, vaccine_code, vaccine_display
FROM fhir.immunization
WHERE vaccine_system IS NOT NULL AND vaccine_code IS NOT NULL
ON CONFLICT (system, code) DO NOTHING;

INSERT INTO fhir.code (system, code, display)
SELECT DISTINCT code_system, code, code_display
FROM fhir.medication
WHERE code_system IS NOT NULL AND code IS NOT NULL
ON CONFLICT (system, code) DO NOTHING;

INSERT INTO fhir.code (system, code, display)
SELECT DISTINCT code_system, code, code_display
FROM fhir.diagnostic_report
WHERE code_system IS NOT NULL AND code IS NOT NULL
ON CONFLICT (system, code) DO NOTHING;

INSERT INTO fhir.code (system, code, display)
SELECT DISTINCT type_code, type_display, type_display
FROM fhir.claim
WHERE type_code IS NOT NULL AND type_display IS NOT NULL
ON CONFLICT (system, code) DO NOTHING;

INSERT INTO fhir.code (system, code, display)
SELECT DISTINCT product_system, product_code, product_display
FROM fhir.claim_item
WHERE product_system IS NOT NULL AND product_code IS NOT NULL
ON CONFLICT (system, code) DO NOTHING;

INSERT INTO fhir.code (system, code, display)
SELECT DISTINCT product_system, product_code, product_display
FROM fhir.eob_item
WHERE product_system IS NOT NULL AND product_code IS NOT NULL
ON CONFLICT (system, code) DO NOTHING;

CREATE TABLE IF NOT EXISTS fhir.provider (
    provider_pk      bigserial PRIMARY KEY,
    provider_ref     text NOT NULL UNIQUE,
    display_name     text
);

CREATE INDEX IF NOT EXISTS idx_provider_ref ON fhir.provider (provider_ref);
CREATE INDEX IF NOT EXISTS idx_provider_display ON fhir.provider (display_name);

INSERT INTO fhir.provider (provider_ref, display_name)
SELECT DISTINCT provider_ref, provider_display
FROM fhir.claim
WHERE provider_ref IS NOT NULL
ON CONFLICT (provider_ref) DO NOTHING;

INSERT INTO fhir.provider (provider_ref, display_name)
SELECT DISTINCT provider_ref, NULL
FROM fhir.explanation_of_benefit
WHERE provider_ref IS NOT NULL
ON CONFLICT (provider_ref) DO NOTHING;

INSERT INTO fhir.provider (provider_ref, display_name)
SELECT DISTINCT service_provider_ref, service_provider_display
FROM fhir.encounter
WHERE service_provider_ref IS NOT NULL
ON CONFLICT (provider_ref) DO NOTHING;

INSERT INTO fhir.provider (provider_ref, display_name)
SELECT DISTINCT requester_ref, requester_display
FROM fhir.medication_request
WHERE requester_ref IS NOT NULL
ON CONFLICT (provider_ref) DO NOTHING;

CREATE TABLE IF NOT EXISTS fhir.location (
    location_pk     bigserial PRIMARY KEY,
    location_ref    text NOT NULL UNIQUE,
    display_name    text
);

CREATE INDEX IF NOT EXISTS idx_location_ref ON fhir.location (location_ref);
CREATE INDEX IF NOT EXISTS idx_location_display ON fhir.location (display_name);

INSERT INTO fhir.location (location_ref, display_name)
SELECT DISTINCT location_ref, location_display
FROM fhir.encounter
WHERE location_ref IS NOT NULL
ON CONFLICT (location_ref) DO NOTHING;

INSERT INTO fhir.location (location_ref, display_name)
SELECT DISTINCT location_ref, location_display
FROM fhir.procedure
WHERE location_ref IS NOT NULL
ON CONFLICT (location_ref) DO NOTHING;

INSERT INTO fhir.location (location_ref, display_name)
SELECT DISTINCT location_ref, location_display
FROM fhir.immunization
WHERE location_ref IS NOT NULL
ON CONFLICT (location_ref) DO NOTHING;

INSERT INTO fhir.location (location_ref, display_name)
SELECT DISTINCT location_ref, location_display
FROM fhir.imaging_study
WHERE location_ref IS NOT NULL
ON CONFLICT (location_ref) DO NOTHING;

ALTER TABLE fhir.condition ADD COLUMN IF NOT EXISTS code_pk bigint REFERENCES fhir.code(code_pk);
UPDATE fhir.condition c SET code_pk = lk.code_pk
FROM fhir.code lk WHERE lk.system = c.code_system AND lk.code = c.code;
CREATE INDEX IF NOT EXISTS idx_condition_code_pk ON fhir.condition(code_pk);

ALTER TABLE fhir.observation ADD COLUMN IF NOT EXISTS code_pk bigint REFERENCES fhir.code(code_pk);
UPDATE fhir.observation o SET code_pk = lk.code_pk
FROM fhir.code lk WHERE lk.system = o.code_system AND lk.code = o.code;
CREATE INDEX IF NOT EXISTS idx_observation_code_pk ON fhir.observation(code_pk);

ALTER TABLE fhir.procedure ADD COLUMN IF NOT EXISTS code_pk bigint REFERENCES fhir.code(code_pk);
UPDATE fhir.procedure p SET code_pk = lk.code_pk
FROM fhir.code lk WHERE lk.system = p.code_system AND lk.code = p.code;
CREATE INDEX IF NOT EXISTS idx_procedure_code_pk ON fhir.procedure(code_pk);

ALTER TABLE fhir.immunization ADD COLUMN IF NOT EXISTS vaccine_code_pk bigint REFERENCES fhir.code(code_pk);
UPDATE fhir.immunization i SET vaccine_code_pk = lk.code_pk
FROM fhir.code lk WHERE lk.system = i.vaccine_system AND lk.code = i.vaccine_code;
CREATE INDEX IF NOT EXISTS idx_immunization_vaccine_code_pk ON fhir.immunization(vaccine_code_pk);

ALTER TABLE fhir.medication ADD COLUMN IF NOT EXISTS code_pk bigint REFERENCES fhir.code(code_pk);
UPDATE fhir.medication m SET code_pk = lk.code_pk
FROM fhir.code lk WHERE lk.system = m.code_system AND lk.code = m.code;
CREATE INDEX IF NOT EXISTS idx_medication_code_pk ON fhir.medication(code_pk);

ALTER TABLE fhir.diagnostic_report ADD COLUMN IF NOT EXISTS code_pk bigint REFERENCES fhir.code(code_pk);
UPDATE fhir.diagnostic_report dr SET code_pk = lk.code_pk
FROM fhir.code lk WHERE lk.system = dr.code_system AND lk.code = dr.code;
CREATE INDEX IF NOT EXISTS idx_diagnostic_report_code_pk ON fhir.diagnostic_report(code_pk);

ALTER TABLE fhir.claim ADD COLUMN IF NOT EXISTS provider_pk bigint REFERENCES fhir.provider(provider_pk);
UPDATE fhir.claim c SET provider_pk = p.provider_pk
FROM fhir.provider p WHERE p.provider_ref = c.provider_ref;
CREATE INDEX IF NOT EXISTS idx_claim_provider_pk ON fhir.claim(provider_pk);

ALTER TABLE fhir.explanation_of_benefit ADD COLUMN IF NOT EXISTS provider_pk bigint REFERENCES fhir.provider(provider_pk);
UPDATE fhir.explanation_of_benefit e SET provider_pk = p.provider_pk
FROM fhir.provider p WHERE p.provider_ref = e.provider_ref;
CREATE INDEX IF NOT EXISTS idx_eob_provider_pk ON fhir.explanation_of_benefit(provider_pk);

ALTER TABLE fhir.encounter ADD COLUMN IF NOT EXISTS service_provider_pk bigint REFERENCES fhir.provider(provider_pk);
UPDATE fhir.encounter e SET service_provider_pk = p.provider_pk
FROM fhir.provider p WHERE p.provider_ref = e.service_provider_ref;
CREATE INDEX IF NOT EXISTS idx_encounter_service_provider_pk ON fhir.encounter(service_provider_pk);

ALTER TABLE fhir.medication_request ADD COLUMN IF NOT EXISTS requester_pk bigint REFERENCES fhir.provider(provider_pk);
UPDATE fhir.medication_request m SET requester_pk = p.provider_pk
FROM fhir.provider p WHERE p.provider_ref = m.requester_ref;
CREATE INDEX IF NOT EXISTS idx_med_request_requester_pk ON fhir.medication_request(requester_pk);

ALTER TABLE fhir.encounter ADD COLUMN IF NOT EXISTS location_pk bigint REFERENCES fhir.location(location_pk);
UPDATE fhir.encounter e SET location_pk = l.location_pk
FROM fhir.location l WHERE l.location_ref = e.location_ref;
CREATE INDEX IF NOT EXISTS idx_encounter_location_pk ON fhir.encounter(location_pk);

ALTER TABLE fhir.procedure ADD COLUMN IF NOT EXISTS location_pk bigint REFERENCES fhir.location(location_pk);
UPDATE fhir.procedure p SET location_pk = l.location_pk
FROM fhir.location l WHERE l.location_ref = p.location_ref;
CREATE INDEX IF NOT EXISTS idx_procedure_location_pk ON fhir.procedure(location_pk);

ALTER TABLE fhir.immunization ADD COLUMN IF NOT EXISTS location_pk bigint REFERENCES fhir.location(location_pk);
UPDATE fhir.immunization i SET location_pk = l.location_pk
FROM fhir.location l WHERE l.location_ref = i.location_ref;
CREATE INDEX IF NOT EXISTS idx_immunization_location_pk ON fhir.immunization(location_pk);

ALTER TABLE fhir.imaging_study ADD COLUMN IF NOT EXISTS location_pk bigint REFERENCES fhir.location(location_pk);
UPDATE fhir.imaging_study s SET location_pk = l.location_pk
FROM fhir.location l WHERE l.location_ref = s.location_ref;
CREATE INDEX IF NOT EXISTS idx_imaging_study_location_pk ON fhir.imaging_study(location_pk);
