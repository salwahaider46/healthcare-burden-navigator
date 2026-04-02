import json
import os
import sys
from typing import Any, Dict, Iterable, List, Optional, Tuple

import psycopg
from psycopg.types.json import Jsonb


def ref_to_id(ref: Optional[str]) -> Optional[str]:
    if not ref:
        return None
    if ref.startswith("urn:uuid:"):
        return ref.split(":")[-1]
    if ref.startswith("#"):
        return ref[1:]
    if "/" in ref and "?" not in ref:
        return ref.rsplit("/", 1)[-1]
    return ref


def get_coding_first(obj: Optional[Dict[str, Any]]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    if not obj:
        return None, None, None
    coding = (obj.get("coding") or [{}])[0]
    return coding.get("system"), coding.get("code"), coding.get("display") or obj.get("text")


def get_text(obj: Optional[Dict[str, Any]]) -> Optional[str]:
    if not obj:
        return None
    return obj.get("text") or ((obj.get("coding") or [{}])[0].get("display"))


def parse_patient(cur, resource_pk: int, r: Dict[str, Any]):
    name = (r.get("name") or [{}])[0]
    address = (r.get("address") or [{}])[0]
    telecom = (r.get("telecom") or [{}])[0]
    extensions = {e.get("url"): e for e in r.get("extension", [])}
    birth_sex = extensions.get("http://hl7.org/fhir/us/core/StructureDefinition/us-core-birthsex", {}).get("valueCode")
    race_ext = extensions.get("http://hl7.org/fhir/us/core/StructureDefinition/us-core-race", {})
    ethnicity_ext = extensions.get("http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity", {})

    def ext_text(ext_obj):
        for item in ext_obj.get("extension", []):
            if item.get("url") == "text":
                return item.get("valueString")
        return None

    cur.execute(
        """
        INSERT INTO fhir.patient (
            patient_id, resource_pk, full_name, family_name, given_names, gender,
            birth_date, marital_status, birth_sex, race_text, ethnicity_text,
            phone, city, state, postal_code, country, raw_json
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (patient_id) DO UPDATE SET
            resource_pk = EXCLUDED.resource_pk,
            full_name = EXCLUDED.full_name,
            family_name = EXCLUDED.family_name,
            given_names = EXCLUDED.given_names,
            gender = EXCLUDED.gender,
            birth_date = EXCLUDED.birth_date,
            marital_status = EXCLUDED.marital_status,
            birth_sex = EXCLUDED.birth_sex,
            race_text = EXCLUDED.race_text,
            ethnicity_text = EXCLUDED.ethnicity_text,
            phone = EXCLUDED.phone,
            city = EXCLUDED.city,
            state = EXCLUDED.state,
            postal_code = EXCLUDED.postal_code,
            country = EXCLUDED.country,
            raw_json = EXCLUDED.raw_json
        """,
        (
            r["id"],
            resource_pk,
            " ".join((name.get("prefix") or []) + (name.get("given") or []) + ([name.get("family")] if name.get("family") else [])).strip() or None,
            name.get("family"),
            name.get("given"),
            r.get("gender"),
            r.get("birthDate"),
            get_text(r.get("maritalStatus")),
            birth_sex,
            ext_text(race_ext),
            ext_text(ethnicity_ext),
            telecom.get("value"),
            address.get("city"),
            address.get("state"),
            address.get("postalCode"),
            address.get("country"),
            Jsonb(r),
        ),
    )


def parse_encounter(cur, resource_pk: int, r: Dict[str, Any]):
    subject = r.get("subject", {})
    service_provider = r.get("serviceProvider", {})
    location = ((r.get("location") or [{}])[0]).get("location", {})
    class_code = (r.get("class") or {}).get("code")
    cur.execute(
        """
        INSERT INTO fhir.encounter (
            encounter_id, resource_pk, patient_ref, patient_id, status, class_code,
            type_text, service_provider_ref, service_provider_display,
            location_ref, location_display, start_time, end_time, raw_json
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (encounter_id) DO UPDATE SET
            resource_pk = EXCLUDED.resource_pk,
            patient_ref = EXCLUDED.patient_ref,
            patient_id = EXCLUDED.patient_id,
            status = EXCLUDED.status,
            class_code = EXCLUDED.class_code,
            type_text = EXCLUDED.type_text,
            service_provider_ref = EXCLUDED.service_provider_ref,
            service_provider_display = EXCLUDED.service_provider_display,
            location_ref = EXCLUDED.location_ref,
            location_display = EXCLUDED.location_display,
            start_time = EXCLUDED.start_time,
            end_time = EXCLUDED.end_time,
            raw_json = EXCLUDED.raw_json
        """,
        (
            r["id"], resource_pk,
            subject.get("reference"), ref_to_id(subject.get("reference")),
            r.get("status"), class_code,
            get_text((r.get("type") or [{}])[0]),
            service_provider.get("reference"), service_provider.get("display"),
            location.get("reference"), location.get("display"),
            (r.get("period") or {}).get("start"),
            (r.get("period") or {}).get("end"),
            Jsonb(r),
        ),
    )


def parse_condition(cur, resource_pk: int, r: Dict[str, Any]):
    subject = r.get("subject", {})
    encounter = r.get("encounter", {})
    code_system, code, code_display = get_coding_first(r.get("code"))
    cur.execute(
        """
        INSERT INTO fhir.condition (
            condition_id, resource_pk, patient_ref, patient_id, encounter_ref, encounter_id,
            clinical_status, verification_status, category_text, code_system, code, code_display,
            onset_datetime, abatement_datetime, recorded_date, raw_json
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (condition_id) DO UPDATE SET
            resource_pk = EXCLUDED.resource_pk,
            patient_ref = EXCLUDED.patient_ref,
            patient_id = EXCLUDED.patient_id,
            encounter_ref = EXCLUDED.encounter_ref,
            encounter_id = EXCLUDED.encounter_id,
            clinical_status = EXCLUDED.clinical_status,
            verification_status = EXCLUDED.verification_status,
            category_text = EXCLUDED.category_text,
            code_system = EXCLUDED.code_system,
            code = EXCLUDED.code,
            code_display = EXCLUDED.code_display,
            onset_datetime = EXCLUDED.onset_datetime,
            abatement_datetime = EXCLUDED.abatement_datetime,
            recorded_date = EXCLUDED.recorded_date,
            raw_json = EXCLUDED.raw_json
        """,
        (
            r["id"], resource_pk,
            subject.get("reference"), ref_to_id(subject.get("reference")),
            encounter.get("reference"), ref_to_id(encounter.get("reference")),
            ((r.get("clinicalStatus") or {}).get("coding") or [{}])[0].get("code"),
            ((r.get("verificationStatus") or {}).get("coding") or [{}])[0].get("code"),
            get_text((r.get("category") or [{}])[0]),
            code_system, code, code_display,
            r.get("onsetDateTime"), r.get("abatementDateTime"), r.get("recordedDate"), Jsonb(r),
        ),
    )


def parse_observation(cur, resource_pk: int, r: Dict[str, Any]):
    subject = r.get("subject", {})
    encounter = r.get("encounter", {})
    code_system, code, code_display = get_coding_first(r.get("code"))
    value_type = None
    value_num = None
    value_unit = None
    value_code = None
    value_display = None
    value_text = None
    if "valueQuantity" in r:
        value_type = "Quantity"
        value_num = (r["valueQuantity"] or {}).get("value")
        value_unit = (r["valueQuantity"] or {}).get("unit")
    elif "valueCodeableConcept" in r:
        value_type = "CodeableConcept"
        _, value_code, value_display = get_coding_first(r.get("valueCodeableConcept"))
        value_text = get_text(r.get("valueCodeableConcept"))
    elif "valueString" in r:
        value_type = "string"
        value_text = r.get("valueString")

    cur.execute(
        """
        INSERT INTO fhir.observation (
            observation_id, resource_pk, patient_ref, patient_id, encounter_ref, encounter_id,
            status, category_text, code_system, code, code_display, effective_time, issued_time,
            value_type, value_num, value_unit, value_code, value_display, value_text, raw_json
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (observation_id) DO UPDATE SET
            resource_pk = EXCLUDED.resource_pk,
            patient_ref = EXCLUDED.patient_ref,
            patient_id = EXCLUDED.patient_id,
            encounter_ref = EXCLUDED.encounter_ref,
            encounter_id = EXCLUDED.encounter_id,
            status = EXCLUDED.status,
            category_text = EXCLUDED.category_text,
            code_system = EXCLUDED.code_system,
            code = EXCLUDED.code,
            code_display = EXCLUDED.code_display,
            effective_time = EXCLUDED.effective_time,
            issued_time = EXCLUDED.issued_time,
            value_type = EXCLUDED.value_type,
            value_num = EXCLUDED.value_num,
            value_unit = EXCLUDED.value_unit,
            value_code = EXCLUDED.value_code,
            value_display = EXCLUDED.value_display,
            value_text = EXCLUDED.value_text,
            raw_json = EXCLUDED.raw_json
        """,
        (
            r["id"], resource_pk,
            subject.get("reference"), ref_to_id(subject.get("reference")),
            encounter.get("reference"), ref_to_id(encounter.get("reference")),
            r.get("status"),
            get_text((r.get("category") or [{}])[0]),
            code_system, code, code_display,
            r.get("effectiveDateTime"), r.get("issued"),
            value_type, value_num, value_unit, value_code, value_display, value_text,
            Jsonb(r),
        ),
    )


def parse_diagnostic_report(cur, resource_pk: int, r: Dict[str, Any]):
    subject = r.get("subject", {})
    encounter = r.get("encounter", {})
    code_system, code, code_display = get_coding_first(r.get("code"))
    note_text_base64 = ((r.get("presentedForm") or [{}])[0]).get("data")
    cur.execute(
        """
        INSERT INTO fhir.diagnostic_report (
            diagnostic_report_id, resource_pk, patient_ref, patient_id, encounter_ref, encounter_id,
            status, code_system, code, code_display, effective_time, issued_time,
            note_text_base64, raw_json
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (diagnostic_report_id) DO UPDATE SET
            resource_pk = EXCLUDED.resource_pk,
            patient_ref = EXCLUDED.patient_ref,
            patient_id = EXCLUDED.patient_id,
            encounter_ref = EXCLUDED.encounter_ref,
            encounter_id = EXCLUDED.encounter_id,
            status = EXCLUDED.status,
            code_system = EXCLUDED.code_system,
            code = EXCLUDED.code,
            code_display = EXCLUDED.code_display,
            effective_time = EXCLUDED.effective_time,
            issued_time = EXCLUDED.issued_time,
            note_text_base64 = EXCLUDED.note_text_base64,
            raw_json = EXCLUDED.raw_json
        """,
        (
            r["id"], resource_pk,
            subject.get("reference"), ref_to_id(subject.get("reference")),
            encounter.get("reference"), ref_to_id(encounter.get("reference")),
            r.get("status"), code_system, code, code_display,
            r.get("effectiveDateTime"), r.get("issued"), note_text_base64, Jsonb(r)
        ),
    )


def parse_document_reference(cur, resource_pk: int, r: Dict[str, Any]):
    subject = r.get("subject", {})
    author = (r.get("author") or [{}])[0]
    content = ((r.get("content") or [{}])[0]).get("attachment", {})
    context_enc = (((r.get("context") or {}).get("encounter") or [{}])[0])
    cur.execute(
        """
        INSERT INTO fhir.document_reference (
            document_reference_id, resource_pk, patient_ref, patient_id, status, type_text,
            category_text, author_ref, author_display, custodian_ref, custodian_display,
            document_date, encounter_ref, encounter_id, content_type, content_data_base64, raw_json
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (document_reference_id) DO UPDATE SET
            resource_pk = EXCLUDED.resource_pk,
            patient_ref = EXCLUDED.patient_ref,
            patient_id = EXCLUDED.patient_id,
            status = EXCLUDED.status,
            type_text = EXCLUDED.type_text,
            category_text = EXCLUDED.category_text,
            author_ref = EXCLUDED.author_ref,
            author_display = EXCLUDED.author_display,
            custodian_ref = EXCLUDED.custodian_ref,
            custodian_display = EXCLUDED.custodian_display,
            document_date = EXCLUDED.document_date,
            encounter_ref = EXCLUDED.encounter_ref,
            encounter_id = EXCLUDED.encounter_id,
            content_type = EXCLUDED.content_type,
            content_data_base64 = EXCLUDED.content_data_base64,
            raw_json = EXCLUDED.raw_json
        """,
        (
            r["id"], resource_pk,
            subject.get("reference"), ref_to_id(subject.get("reference")),
            r.get("status"), get_text(r.get("type")), get_text((r.get("category") or [{}])[0]),
            author.get("reference"), author.get("display"),
            (r.get("custodian") or {}).get("reference"), (r.get("custodian") or {}).get("display"),
            r.get("date"), context_enc.get("reference"), ref_to_id(context_enc.get("reference")),
            content.get("contentType"), content.get("data"), Jsonb(r),
        ),
    )


def parse_claim(cur, resource_pk: int, r: Dict[str, Any]):
    patient = r.get("patient", {})
    provider = r.get("provider", {})
    facility = r.get("facility", {})
    type_system, type_code, type_display = get_coding_first(r.get("type"))
    priority_code = ((r.get("priority") or {}).get("coding") or [{}])[0].get("code")
    total = r.get("total") or {}
    cur.execute(
        """
        INSERT INTO fhir.claim (
            claim_id, resource_pk, patient_ref, patient_id, status, use_code, type_code, type_display,
            provider_ref, provider_display, facility_ref, facility_display,
            billable_start, billable_end, created_time, priority_code,
            total_value, total_currency, raw_json
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (claim_id) DO UPDATE SET
            resource_pk = EXCLUDED.resource_pk,
            patient_ref = EXCLUDED.patient_ref,
            patient_id = EXCLUDED.patient_id,
            status = EXCLUDED.status,
            use_code = EXCLUDED.use_code,
            type_code = EXCLUDED.type_code,
            type_display = EXCLUDED.type_display,
            provider_ref = EXCLUDED.provider_ref,
            provider_display = EXCLUDED.provider_display,
            facility_ref = EXCLUDED.facility_ref,
            facility_display = EXCLUDED.facility_display,
            billable_start = EXCLUDED.billable_start,
            billable_end = EXCLUDED.billable_end,
            created_time = EXCLUDED.created_time,
            priority_code = EXCLUDED.priority_code,
            total_value = EXCLUDED.total_value,
            total_currency = EXCLUDED.total_currency,
            raw_json = EXCLUDED.raw_json
        """,
        (
            r["id"], resource_pk,
            patient.get("reference"), ref_to_id(patient.get("reference")),
            r.get("status"), r.get("use"), type_code, type_display,
            provider.get("reference"), provider.get("display"),
            facility.get("reference"), facility.get("display"),
            (r.get("billablePeriod") or {}).get("start"), (r.get("billablePeriod") or {}).get("end"),
            r.get("created"), priority_code,
            total.get("value"), total.get("currency"), Jsonb(r)
        ),
    )
    cur.execute("DELETE FROM fhir.claim_item WHERE claim_id = %s", (r["id"],))
    for item in r.get("item", []):
        pos = item.get("productOrService") or {}
        ps_system, ps_code, ps_display = get_coding_first(pos)
        enc = (item.get("encounter") or [{}])[0]
        serviced_period = item.get("servicedPeriod") or {}
        cur.execute(
            """
            INSERT INTO fhir.claim_item (
                claim_id, sequence_no, product_system, product_code, product_display,
                encounter_ref, encounter_id, serviced_start, serviced_end,
                diagnosis_sequence, raw_json
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                r["id"], item.get("sequence"), ps_system, ps_code, ps_display,
                enc.get("reference"), ref_to_id(enc.get("reference")),
                serviced_period.get("start"), serviced_period.get("end"),
                item.get("diagnosisSequence"), Jsonb(item)
            ),
        )


def parse_eob(cur, resource_pk: int, r: Dict[str, Any]):
    patient = r.get("patient", {})
    claim = r.get("claim", {})
    provider = r.get("provider", {})
    facility = r.get("facility", {})
    type_system, type_code, type_display = get_coding_first(r.get("type"))
    payment = (r.get("payment") or {}).get("amount") or {}
    cur.execute(
        """
        INSERT INTO fhir.explanation_of_benefit (
            eob_id, resource_pk, patient_ref, patient_id, status, use_code, type_code, type_display,
            claim_ref, claim_id, provider_ref, facility_ref, insurer_display, outcome,
            billable_start, billable_end, created_time, payment_amount, payment_currency, raw_json
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (eob_id) DO UPDATE SET
            resource_pk = EXCLUDED.resource_pk,
            patient_ref = EXCLUDED.patient_ref,
            patient_id = EXCLUDED.patient_id,
            status = EXCLUDED.status,
            use_code = EXCLUDED.use_code,
            type_code = EXCLUDED.type_code,
            type_display = EXCLUDED.type_display,
            claim_ref = EXCLUDED.claim_ref,
            claim_id = EXCLUDED.claim_id,
            provider_ref = EXCLUDED.provider_ref,
            facility_ref = EXCLUDED.facility_ref,
            insurer_display = EXCLUDED.insurer_display,
            outcome = EXCLUDED.outcome,
            billable_start = EXCLUDED.billable_start,
            billable_end = EXCLUDED.billable_end,
            created_time = EXCLUDED.created_time,
            payment_amount = EXCLUDED.payment_amount,
            payment_currency = EXCLUDED.payment_currency,
            raw_json = EXCLUDED.raw_json
        """,
        (
            r["id"], resource_pk,
            patient.get("reference"), ref_to_id(patient.get("reference")),
            r.get("status"), r.get("use"), type_code, type_display,
            claim.get("reference"), ref_to_id(claim.get("reference")),
            provider.get("reference"), facility.get("reference"),
            (r.get("insurer") or {}).get("display"), r.get("outcome"),
            (r.get("billablePeriod") or {}).get("start"), (r.get("billablePeriod") or {}).get("end"),
            r.get("created"), payment.get("value"), payment.get("currency"), Jsonb(r)
        ),
    )
    cur.execute("DELETE FROM fhir.eob_item WHERE eob_id = %s", (r["id"],))
    cur.execute("DELETE FROM fhir.eob_total WHERE eob_id = %s", (r["id"],))
    for item in r.get("item", []):
        cat = item.get("category") or {}
        cat_system, cat_code, cat_display = get_coding_first(cat)
        pos = item.get("productOrService") or {}
        ps_system, ps_code, ps_display = get_coding_first(pos)
        enc = (item.get("encounter") or [{}])[0]
        serviced_period = item.get("servicedPeriod") or {}
        cur.execute(
            """
            INSERT INTO fhir.eob_item (
                eob_id, sequence_no, category_system, category_code, category_display,
                product_system, product_code, product_display, encounter_ref, encounter_id,
                serviced_start, serviced_end, diagnosis_sequence, raw_json
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                r["id"], item.get("sequence"), cat_system, cat_code, cat_display,
                ps_system, ps_code, ps_display,
                enc.get("reference"), ref_to_id(enc.get("reference")),
                serviced_period.get("start"), serviced_period.get("end"),
                item.get("diagnosisSequence"), Jsonb(item)
            ),
        )
    for total in r.get("total", []):
        cat = total.get("category") or {}
        amount = total.get("amount") or {}
        cat_system, cat_code, cat_display = get_coding_first(cat)
        cur.execute(
            """
            INSERT INTO fhir.eob_total (
                eob_id, category_system, category_code, category_display,
                amount_value, amount_currency, raw_json
            ) VALUES (%s,%s,%s,%s,%s,%s,%s)
            """,
            (r["id"], cat_system, cat_code, cat_display, amount.get("value"), amount.get("currency"), Jsonb(total)),
        )


def parse_medication(cur, resource_pk: int, r: Dict[str, Any]):
    code_system, code, code_display = get_coding_first(r.get("code"))
    cur.execute(
        """
        INSERT INTO fhir.medication (medication_id, resource_pk, status, code_system, code, code_display, raw_json)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (medication_id) DO UPDATE SET
            resource_pk = EXCLUDED.resource_pk,
            status = EXCLUDED.status,
            code_system = EXCLUDED.code_system,
            code = EXCLUDED.code,
            code_display = EXCLUDED.code_display,
            raw_json = EXCLUDED.raw_json
        """,
        (r["id"], resource_pk, r.get("status"), code_system, code, code_display, Jsonb(r)),
    )


def parse_medication_request(cur, resource_pk: int, r: Dict[str, Any]):
    subject = r.get("subject", {})
    encounter = r.get("encounter", {})
    requester = r.get("requester", {})
    med_ref = (r.get("medicationReference") or {}).get("reference")
    med_text = get_text(r.get("medicationCodeableConcept"))
    cur.execute(
        """
        INSERT INTO fhir.medication_request (
            medication_request_id, resource_pk, patient_ref, patient_id, encounter_ref, encounter_id,
            status, intent, authored_on, medication_ref, medication_id, medication_text,
            requester_ref, requester_display, raw_json
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (medication_request_id) DO UPDATE SET
            resource_pk = EXCLUDED.resource_pk,
            patient_ref = EXCLUDED.patient_ref,
            patient_id = EXCLUDED.patient_id,
            encounter_ref = EXCLUDED.encounter_ref,
            encounter_id = EXCLUDED.encounter_id,
            status = EXCLUDED.status,
            intent = EXCLUDED.intent,
            authored_on = EXCLUDED.authored_on,
            medication_ref = EXCLUDED.medication_ref,
            medication_id = EXCLUDED.medication_id,
            medication_text = EXCLUDED.medication_text,
            requester_ref = EXCLUDED.requester_ref,
            requester_display = EXCLUDED.requester_display,
            raw_json = EXCLUDED.raw_json
        """,
        (
            r["id"], resource_pk,
            subject.get("reference"), ref_to_id(subject.get("reference")),
            encounter.get("reference"), ref_to_id(encounter.get("reference")),
            r.get("status"), r.get("intent"), r.get("authoredOn"),
            med_ref, ref_to_id(med_ref), med_text,
            requester.get("reference"), requester.get("display"), Jsonb(r)
        ),
    )


def parse_medication_administration(cur, resource_pk: int, r: Dict[str, Any]):
    subject = r.get("subject", {})
    context = r.get("context", {})
    med_text = get_text(r.get("medicationCodeableConcept"))
    cur.execute(
        """
        INSERT INTO fhir.medication_administration (
            medication_administration_id, resource_pk, patient_ref, patient_id, encounter_ref, encounter_id,
            status, effective_time, medication_text, raw_json
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (medication_administration_id) DO UPDATE SET
            resource_pk = EXCLUDED.resource_pk,
            patient_ref = EXCLUDED.patient_ref,
            patient_id = EXCLUDED.patient_id,
            encounter_ref = EXCLUDED.encounter_ref,
            encounter_id = EXCLUDED.encounter_id,
            status = EXCLUDED.status,
            effective_time = EXCLUDED.effective_time,
            medication_text = EXCLUDED.medication_text,
            raw_json = EXCLUDED.raw_json
        """,
        (
            r["id"], resource_pk,
            subject.get("reference"), ref_to_id(subject.get("reference")),
            context.get("reference"), ref_to_id(context.get("reference")),
            r.get("status"), r.get("effectiveDateTime"), med_text, Jsonb(r)
        ),
    )


def parse_procedure(cur, resource_pk: int, r: Dict[str, Any]):
    subject = r.get("subject", {})
    encounter = r.get("encounter", {})
    location = r.get("location", {})
    code_system, code, code_display = get_coding_first(r.get("code"))
    performed = r.get("performedPeriod") or {}
    cur.execute(
        """
        INSERT INTO fhir.procedure (
            procedure_id, resource_pk, patient_ref, patient_id, encounter_ref, encounter_id,
            status, code_system, code, code_display, location_ref, location_display,
            performed_start, performed_end, raw_json
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (procedure_id) DO UPDATE SET
            resource_pk = EXCLUDED.resource_pk,
            patient_ref = EXCLUDED.patient_ref,
            patient_id = EXCLUDED.patient_id,
            encounter_ref = EXCLUDED.encounter_ref,
            encounter_id = EXCLUDED.encounter_id,
            status = EXCLUDED.status,
            code_system = EXCLUDED.code_system,
            code = EXCLUDED.code,
            code_display = EXCLUDED.code_display,
            location_ref = EXCLUDED.location_ref,
            location_display = EXCLUDED.location_display,
            performed_start = EXCLUDED.performed_start,
            performed_end = EXCLUDED.performed_end,
            raw_json = EXCLUDED.raw_json
        """,
        (
            r["id"], resource_pk,
            subject.get("reference"), ref_to_id(subject.get("reference")),
            encounter.get("reference"), ref_to_id(encounter.get("reference")),
            r.get("status"), code_system, code, code_display,
            location.get("reference"), location.get("display"),
            performed.get("start"), performed.get("end"), Jsonb(r)
        ),
    )


def parse_immunization(cur, resource_pk: int, r: Dict[str, Any]):
    patient = r.get("patient", {})
    encounter = r.get("encounter", {})
    location = r.get("location", {})
    v_system, v_code, v_display = get_coding_first(r.get("vaccineCode"))
    cur.execute(
        """
        INSERT INTO fhir.immunization (
            immunization_id, resource_pk, patient_ref, patient_id, encounter_ref, encounter_id,
            status, occurrence_time, vaccine_system, vaccine_code, vaccine_display,
            location_ref, location_display, raw_json
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (immunization_id) DO UPDATE SET
            resource_pk = EXCLUDED.resource_pk,
            patient_ref = EXCLUDED.patient_ref,
            patient_id = EXCLUDED.patient_id,
            encounter_ref = EXCLUDED.encounter_ref,
            encounter_id = EXCLUDED.encounter_id,
            status = EXCLUDED.status,
            occurrence_time = EXCLUDED.occurrence_time,
            vaccine_system = EXCLUDED.vaccine_system,
            vaccine_code = EXCLUDED.vaccine_code,
            vaccine_display = EXCLUDED.vaccine_display,
            location_ref = EXCLUDED.location_ref,
            location_display = EXCLUDED.location_display,
            raw_json = EXCLUDED.raw_json
        """,
        (
            r["id"], resource_pk,
            patient.get("reference"), ref_to_id(patient.get("reference")),
            encounter.get("reference"), ref_to_id(encounter.get("reference")),
            r.get("status"), r.get("occurrenceDateTime"),
            v_system, v_code, v_display,
            location.get("reference"), location.get("display"), Jsonb(r)
        ),
    )


def parse_imaging_study(cur, resource_pk: int, r: Dict[str, Any]):
    subject = r.get("subject", {})
    encounter = r.get("encounter", {})
    location = r.get("location", {})
    cur.execute(
        """
        INSERT INTO fhir.imaging_study (
            imaging_study_id, resource_pk, patient_ref, patient_id, encounter_ref, encounter_id,
            status, started_time, location_ref, location_display,
            number_of_series, number_of_instances, raw_json
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (imaging_study_id) DO UPDATE SET
            resource_pk = EXCLUDED.resource_pk,
            patient_ref = EXCLUDED.patient_ref,
            patient_id = EXCLUDED.patient_id,
            encounter_ref = EXCLUDED.encounter_ref,
            encounter_id = EXCLUDED.encounter_id,
            status = EXCLUDED.status,
            started_time = EXCLUDED.started_time,
            location_ref = EXCLUDED.location_ref,
            location_display = EXCLUDED.location_display,
            number_of_series = EXCLUDED.number_of_series,
            number_of_instances = EXCLUDED.number_of_instances,
            raw_json = EXCLUDED.raw_json
        """,
        (
            r["id"], resource_pk,
            subject.get("reference"), ref_to_id(subject.get("reference")),
            encounter.get("reference"), ref_to_id(encounter.get("reference")),
            r.get("status"), r.get("started"),
            location.get("reference"), location.get("display"),
            r.get("numberOfSeries"), r.get("numberOfInstances"), Jsonb(r)
        ),
    )


def parse_device(cur, resource_pk: int, r: Dict[str, Any]):
    patient = r.get("patient", {})
    cur.execute(
        """
        INSERT INTO fhir.device (
            device_id, resource_pk, patient_ref, patient_id, status, distinct_identifier,
            serial_number, lot_number, manufacture_date, expiration_date, type_text, raw_json
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (device_id) DO UPDATE SET
            resource_pk = EXCLUDED.resource_pk,
            patient_ref = EXCLUDED.patient_ref,
            patient_id = EXCLUDED.patient_id,
            status = EXCLUDED.status,
            distinct_identifier = EXCLUDED.distinct_identifier,
            serial_number = EXCLUDED.serial_number,
            lot_number = EXCLUDED.lot_number,
            manufacture_date = EXCLUDED.manufacture_date,
            expiration_date = EXCLUDED.expiration_date,
            type_text = EXCLUDED.type_text,
            raw_json = EXCLUDED.raw_json
        """,
        (
            r["id"], resource_pk,
            patient.get("reference"), ref_to_id(patient.get("reference")),
            r.get("status"), r.get("distinctIdentifier"), r.get("serialNumber"), r.get("lotNumber"),
            r.get("manufactureDate"), r.get("expirationDate"), get_text(r.get("type")), Jsonb(r)
        ),
    )


def parse_care_team(cur, resource_pk: int, r: Dict[str, Any]):
    subject = r.get("subject", {})
    encounter = r.get("encounter", {})
    cur.execute(
        """
        INSERT INTO fhir.care_team (care_team_id, resource_pk, patient_ref, patient_id, encounter_ref, encounter_id, status, raw_json)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (care_team_id) DO UPDATE SET
            resource_pk = EXCLUDED.resource_pk,
            patient_ref = EXCLUDED.patient_ref,
            patient_id = EXCLUDED.patient_id,
            encounter_ref = EXCLUDED.encounter_ref,
            encounter_id = EXCLUDED.encounter_id,
            status = EXCLUDED.status,
            raw_json = EXCLUDED.raw_json
        """,
        (r["id"], resource_pk, subject.get("reference"), ref_to_id(subject.get("reference")), encounter.get("reference"), ref_to_id(encounter.get("reference")), r.get("status"), Jsonb(r))
    )


def parse_care_plan(cur, resource_pk: int, r: Dict[str, Any]):
    subject = r.get("subject", {})
    encounter = r.get("encounter", {})
    period = r.get("period") or {}
    cur.execute(
        """
        INSERT INTO fhir.care_plan (care_plan_id, resource_pk, patient_ref, patient_id, encounter_ref, encounter_id, status, intent, start_time, end_time, raw_json)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (care_plan_id) DO UPDATE SET
            resource_pk = EXCLUDED.resource_pk,
            patient_ref = EXCLUDED.patient_ref,
            patient_id = EXCLUDED.patient_id,
            encounter_ref = EXCLUDED.encounter_ref,
            encounter_id = EXCLUDED.encounter_id,
            status = EXCLUDED.status,
            intent = EXCLUDED.intent,
            start_time = EXCLUDED.start_time,
            end_time = EXCLUDED.end_time,
            raw_json = EXCLUDED.raw_json
        """,
        (r["id"], resource_pk, subject.get("reference"), ref_to_id(subject.get("reference")), encounter.get("reference"), ref_to_id(encounter.get("reference")), r.get("status"), r.get("intent"), period.get("start"), period.get("end"), Jsonb(r))
    )


def parse_provenance(cur, resource_pk: int, r: Dict[str, Any]):
    cur.execute(
        """
        INSERT INTO fhir.provenance (provenance_id, resource_pk, recorded_time, raw_json)
        VALUES (%s,%s,%s,%s)
        ON CONFLICT (provenance_id) DO UPDATE SET
            resource_pk = EXCLUDED.resource_pk,
            recorded_time = EXCLUDED.recorded_time,
            raw_json = EXCLUDED.raw_json
        """,
        (r["id"], resource_pk, r.get("recorded"), Jsonb(r))
    )


def insert_identifiers(cur, resource_pk: int, r: Dict[str, Any]):
    cur.execute("DELETE FROM fhir.resource_identifier WHERE source_resource_pk = %s", (resource_pk,))
    for ident in r.get("identifier", []):
        cur.execute(
            """
            INSERT INTO fhir.resource_identifier (
                source_resource_pk, source_resource_type, source_resource_id,
                use_code, system, value, type_text, raw_json
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                resource_pk, r.get("resourceType"), r.get("id"),
                ident.get("use"), ident.get("system"), ident.get("value"), get_text(ident.get("type")), Jsonb(ident)
            ),
        )


def insert_codings(cur, resource_pk: int, r: Dict[str, Any]):
    cur.execute("DELETE FROM fhir.resource_coding WHERE source_resource_pk = %s", (resource_pk,))
    paths = {
        "type": r.get("type"),
        "code": r.get("code"),
        "category": (r.get("category") or [None])[0],
        "class": r.get("class"),
        "vaccineCode": r.get("vaccineCode"),
        "medicationCodeableConcept": r.get("medicationCodeableConcept"),
        "productOrService": r.get("productOrService"),
        "reasonCode": (r.get("reasonCode") or [None])[0],
    }
    for field_path, obj in paths.items():
        if not isinstance(obj, dict):
            continue
        for idx, coding in enumerate(obj.get("coding", [])):
            cur.execute(
                """
                INSERT INTO fhir.resource_coding (
                    source_resource_pk, source_resource_type, source_resource_id,
                    field_path, coding_idx, system, code, display, raw_json
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    resource_pk, r.get("resourceType"), r.get("id"),
                    field_path, idx, coding.get("system"), coding.get("code"), coding.get("display"), Jsonb(coding)
                ),
            )


def insert_references(cur, resource_pk: int, r: Dict[str, Any]):
    cur.execute("DELETE FROM fhir.resource_reference WHERE source_resource_pk = %s", (resource_pk,))

    def add_ref(field_path: str, obj: Optional[Dict[str, Any]]):
        if obj and obj.get("reference"):
            cur.execute(
                """
                INSERT INTO fhir.resource_reference (
                    source_resource_pk, source_resource_type, source_resource_id,
                    field_path, target_reference, target_display, raw_json
                ) VALUES (%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    resource_pk, r.get("resourceType"), r.get("id"),
                    field_path, obj.get("reference"), obj.get("display"), Jsonb(obj)
                ),
            )

    single_paths = ["subject", "patient", "encounter", "serviceProvider", "provider", "facility", "claim", "requester", "custodian", "location", "referral", "context"]
    for path in single_paths:
        val = r.get(path)
        if isinstance(val, dict):
            add_ref(path, val)

    list_of_dict_paths = ["author", "performer", "careTeam", "addresses", "reasonReference"]
    for path in list_of_dict_paths:
        for idx, item in enumerate(r.get(path, [])):
            if isinstance(item, dict):
                add_ref(f"{path}[{idx}]", item)

    for idx, item in enumerate(r.get("item", [])):
        for jdx, enc in enumerate(item.get("encounter", [])):
            add_ref(f"item[{idx}].encounter[{jdx}]", enc)

    ctx = r.get("context") or {}
    for idx, enc in enumerate(ctx.get("encounter", [])):
        add_ref(f"context.encounter[{idx}]", enc)

    for idx, d in enumerate(r.get("diagnosis", [])):
        add_ref(f"diagnosis[{idx}].diagnosisReference", d.get("diagnosisReference"))


def load_bundle(conn, bundle_path: str, source_filename: Optional[str] = None):
    with open(bundle_path, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    bundle_id = None
    for entry in bundle.get("entry", []):
        if (entry.get("resource") or {}).get("resourceType") == "Patient":
            bundle_id = entry["resource"].get("id")
            break
    if not bundle_id:
        bundle_id = os.path.basename(bundle_path)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO fhir.bundle (bundle_id, bundle_type, source_filename, bundle_json)
            VALUES (%s,%s,%s,%s)
            ON CONFLICT (bundle_id) DO UPDATE SET
                bundle_type = EXCLUDED.bundle_type,
                source_filename = EXCLUDED.source_filename,
                bundle_json = EXCLUDED.bundle_json
            """,
            (bundle_id, bundle.get("type"), source_filename or os.path.basename(bundle_path), Jsonb(bundle)),
        )

        for entry in bundle.get("entry", []):
            resource = entry.get("resource") or {}
            resource_type = resource.get("resourceType")
            resource_id = resource.get("id")
            if not resource_type or not resource_id:
                continue
            cur.execute(
                """
                INSERT INTO fhir.resource_raw (
                    bundle_id, full_url, resource_type, resource_id, request_method, request_url, resource_json
                ) VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (resource_type, resource_id) DO UPDATE SET
                    bundle_id = EXCLUDED.bundle_id,
                    full_url = EXCLUDED.full_url,
                    request_method = EXCLUDED.request_method,
                    request_url = EXCLUDED.request_url,
                    resource_json = EXCLUDED.resource_json
                RETURNING resource_pk
                """,
                (
                    bundle_id,
                    entry.get("fullUrl"),
                    resource_type,
                    resource_id,
                    (entry.get("request") or {}).get("method"),
                    (entry.get("request") or {}).get("url"),
                    Jsonb(resource),
                ),
            )
            resource_pk = cur.fetchone()[0]

            insert_identifiers(cur, resource_pk, resource)
            insert_codings(cur, resource_pk, resource)
            insert_references(cur, resource_pk, resource)

            if resource_type == "Patient":
                parse_patient(cur, resource_pk, resource)
            elif resource_type == "Encounter":
                parse_encounter(cur, resource_pk, resource)
            elif resource_type == "Condition":
                parse_condition(cur, resource_pk, resource)
            elif resource_type == "Observation":
                parse_observation(cur, resource_pk, resource)
            elif resource_type == "DiagnosticReport":
                parse_diagnostic_report(cur, resource_pk, resource)
            elif resource_type == "DocumentReference":
                parse_document_reference(cur, resource_pk, resource)
            elif resource_type == "Claim":
                parse_claim(cur, resource_pk, resource)
            elif resource_type == "ExplanationOfBenefit":
                parse_eob(cur, resource_pk, resource)
            elif resource_type == "Medication":
                parse_medication(cur, resource_pk, resource)
            elif resource_type == "MedicationRequest":
                parse_medication_request(cur, resource_pk, resource)
            elif resource_type == "MedicationAdministration":
                parse_medication_administration(cur, resource_pk, resource)
            elif resource_type == "Procedure":
                parse_procedure(cur, resource_pk, resource)
            elif resource_type == "Immunization":
                parse_immunization(cur, resource_pk, resource)
            elif resource_type == "ImagingStudy":
                parse_imaging_study(cur, resource_pk, resource)
            elif resource_type == "Device":
                parse_device(cur, resource_pk, resource)
            elif resource_type == "CareTeam":
                parse_care_team(cur, resource_pk, resource)
            elif resource_type == "CarePlan":
                parse_care_plan(cur, resource_pk, resource)
            elif resource_type == "Provenance":
                parse_provenance(cur, resource_pk, resource)

    conn.commit()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python load_fhir_bundle.py <postgres-conn-string> <bundle-json-path>")
        sys.exit(1)

    conn_string = sys.argv[1]
    bundle_path = sys.argv[2]

    with psycopg.connect(conn_string) as conn:
        load_bundle(conn, bundle_path)
        print(f"Loaded bundle from {bundle_path}")
