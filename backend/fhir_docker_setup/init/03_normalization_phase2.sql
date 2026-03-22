CREATE OR REPLACE VIEW fhir.v_patient_encounters AS
SELECT
    p.patient_id,
    p.full_name,
    e.encounter_id,
    e.start_time,
    e.end_time,
    e.type_text,
    pr.display_name  AS service_provider_display,
    loc.display_name AS location_display
FROM fhir.patient p
LEFT JOIN fhir.encounter e   ON e.patient_id       = p.patient_id
LEFT JOIN fhir.provider  pr  ON pr.provider_pk      = e.service_provider_pk
LEFT JOIN fhir.location  loc ON loc.location_pk     = e.location_pk;

CREATE OR REPLACE VIEW fhir.v_patient_claim_summary AS
SELECT
    c.patient_id,
    c.claim_id,
    c.created_time,
    c.type_display,
    pr.display_name  AS provider_display,
    c.total_value,
    c.total_currency,
    e.eob_id,
    e.outcome,
    e.payment_amount,
    e.payment_currency,
    e.insurer_display
FROM fhir.claim c
LEFT JOIN fhir.provider             pr ON pr.provider_pk = c.provider_pk
LEFT JOIN fhir.explanation_of_benefit e ON e.claim_id    = c.claim_id;

CREATE OR REPLACE VIEW fhir.v_recent_labs AS
SELECT
    o.patient_id,
    o.observation_id,
    o.effective_time,
    cd.display   AS code_display,
    o.value_num,
    o.value_unit,
    o.value_text,
    o.value_display
FROM fhir.observation o
JOIN fhir.code cd ON cd.code_pk = o.code_pk
WHERE o.category_text = 'laboratory'
   OR cd.system = 'http://loinc.org';

ALTER TABLE fhir.condition
    DROP COLUMN IF EXISTS code_system,
    DROP COLUMN IF EXISTS code,
    DROP COLUMN IF EXISTS code_display;

ALTER TABLE fhir.observation
    DROP COLUMN IF EXISTS code_system,
    DROP COLUMN IF EXISTS code,
    DROP COLUMN IF EXISTS code_display;

ALTER TABLE fhir.procedure
    DROP COLUMN IF EXISTS code_system,
    DROP COLUMN IF EXISTS code,
    DROP COLUMN IF EXISTS code_display;

ALTER TABLE fhir.immunization
    DROP COLUMN IF EXISTS vaccine_system,
    DROP COLUMN IF EXISTS vaccine_code,
    DROP COLUMN IF EXISTS vaccine_display;

ALTER TABLE fhir.medication
    DROP COLUMN IF EXISTS code_system,
    DROP COLUMN IF EXISTS code,
    DROP COLUMN IF EXISTS code_display;

ALTER TABLE fhir.diagnostic_report
    DROP COLUMN IF EXISTS code_system,
    DROP COLUMN IF EXISTS code,
    DROP COLUMN IF EXISTS code_display;

ALTER TABLE fhir.claim
    DROP COLUMN IF EXISTS provider_ref,
    DROP COLUMN IF EXISTS provider_display;

ALTER TABLE fhir.explanation_of_benefit
    DROP COLUMN IF EXISTS provider_ref;

ALTER TABLE fhir.encounter
    DROP COLUMN IF EXISTS service_provider_ref,
    DROP COLUMN IF EXISTS service_provider_display;

ALTER TABLE fhir.medication_request
    DROP COLUMN IF EXISTS requester_ref,
    DROP COLUMN IF EXISTS requester_display;

ALTER TABLE fhir.encounter
    DROP COLUMN IF EXISTS location_ref,
    DROP COLUMN IF EXISTS location_display;

ALTER TABLE fhir.procedure
    DROP COLUMN IF EXISTS location_ref,
    DROP COLUMN IF EXISTS location_display;

ALTER TABLE fhir.immunization
    DROP COLUMN IF EXISTS location_ref,
    DROP COLUMN IF EXISTS location_display;

ALTER TABLE fhir.imaging_study
    DROP COLUMN IF EXISTS location_ref,
    DROP COLUMN IF EXISTS location_display;

ALTER TABLE fhir.condition           DROP COLUMN IF EXISTS patient_ref;
ALTER TABLE fhir.observation         DROP COLUMN IF EXISTS patient_ref;
ALTER TABLE fhir.procedure           DROP COLUMN IF EXISTS patient_ref;
ALTER TABLE fhir.immunization        DROP COLUMN IF EXISTS patient_ref;
ALTER TABLE fhir.medication_request  DROP COLUMN IF EXISTS patient_ref;
ALTER TABLE fhir.medication_administration DROP COLUMN IF EXISTS patient_ref;
ALTER TABLE fhir.encounter           DROP COLUMN IF EXISTS patient_ref;
ALTER TABLE fhir.claim               DROP COLUMN IF EXISTS patient_ref;
ALTER TABLE fhir.explanation_of_benefit DROP COLUMN IF EXISTS patient_ref;
ALTER TABLE fhir.diagnostic_report   DROP COLUMN IF EXISTS patient_ref;
ALTER TABLE fhir.document_reference  DROP COLUMN IF EXISTS patient_ref;
ALTER TABLE fhir.care_team           DROP COLUMN IF EXISTS patient_ref;
ALTER TABLE fhir.care_plan           DROP COLUMN IF EXISTS patient_ref;
ALTER TABLE fhir.device              DROP COLUMN IF EXISTS patient_ref;
ALTER TABLE fhir.imaging_study       DROP COLUMN IF EXISTS patient_ref;

ALTER TABLE fhir.condition           DROP COLUMN IF EXISTS encounter_ref;
ALTER TABLE fhir.observation         DROP COLUMN IF EXISTS encounter_ref;
ALTER TABLE fhir.procedure           DROP COLUMN IF EXISTS encounter_ref;
ALTER TABLE fhir.immunization        DROP COLUMN IF EXISTS encounter_ref;
ALTER TABLE fhir.medication_request  DROP COLUMN IF EXISTS encounter_ref;
ALTER TABLE fhir.medication_administration DROP COLUMN IF EXISTS encounter_ref;
ALTER TABLE fhir.diagnostic_report   DROP COLUMN IF EXISTS encounter_ref;
ALTER TABLE fhir.document_reference  DROP COLUMN IF EXISTS encounter_ref;
ALTER TABLE fhir.care_team           DROP COLUMN IF EXISTS encounter_ref;
ALTER TABLE fhir.care_plan           DROP COLUMN IF EXISTS encounter_ref;
ALTER TABLE fhir.claim_item          DROP COLUMN IF EXISTS encounter_ref;
ALTER TABLE fhir.eob_item            DROP COLUMN IF EXISTS encounter_ref;
