from datetime import datetime

from fhir.resources import imagingstudy
from fhir.resources import identifier
from fhir.resources import codeableconcept
from fhir.resources import coding
from fhir.resources import patient
from fhir.resources import humanname
from fhir.resources import fhirdate

from pydicom import FileDataset

TERMINOLOGY_CODING_SYS = "http://terminology.hl7.org/CodeSystem/v2-0203"
TERMINOLOGY_CODING_SYS_CODE_ACCESSION = "ACSN"
TERMINOLOGY_CODING_SYS_CODE_MRN = "MR"

ACQUISITION_MODALITY_SYS = "http://dicom.nema.org/resources/ontology/DCM"

SOP_CLASS_SYS ="urn:ietf:rfc:3986"

def gen_accession_identifier(id):
    idf = identifier.Identifier()
    idf.use="usual"
    idf.type =codeableconcept.CodeableConcept()
    idf.type.coding = []
    acsn = coding.Coding()
    acsn.system=TERMINOLOGY_CODING_SYS
    acsn.code=TERMINOLOGY_CODING_SYS_CODE_ACCESSION

    idf.type.coding.append(acsn)
    idf.value=id
    return idf

def gen_studyinstanceuid_identifier(id):
    idf = identifier.Identifier()
    idf.system="urn:dicom:uid"
    idf.value="urn:oid:" + id
    return idf

def getPatientResourceIdentifications(PatientID, IssuerOfPatientID):
    idf = identifier.Identifier()
    idf.use = "usual"
    idf.type = codeableconcept.CodeableConcept()
    idf.type.coding = []
    pid = coding.Coding()
    pid.system = TERMINOLOGY_CODING_SYS
    pid.code = TERMINOLOGY_CODING_SYS_CODE_MRN
    idf.type.coding.append(pid)

    idf.system = "urn:oid:" + IssuerOfPatientID
    idf.value = PatientID
    return idf


def calc_gender(gender):
    if gender is None:
        return "unknown"
    if not gender:
        return "unknown"
    if gender.upper().lower() == "f":
        return "female"
    if gender.upper().lower() == "m":
        return "male"
    if gender.upper().lower() == "o":
        return "other"

    return "unknown"


def calc_dob(dicom_dob):
    if dicom_dob == '':
        return None

    fhir_dob = fhirdate.FHIRDate()
    try:
        dob = datetime.strptime(dicom_dob, '%Y%m%d')
        fhir_dob.date = dob
    except:
        return None
    return fhir_dob

def inline_patient_resource(referenceId, PatientID, IssuerOfPatientID, patientName,gender, dob):
    p = patient.Patient()
    p.id=referenceId
    p.name =[]
    p.use = "official"
    p.identifier= [getPatientResourceIdentifications(PatientID,IssuerOfPatientID)]
    hn=humanname.HumanName()
    hn.family= patientName.family_name
    hn.given = [patientName.given_name]
    p.name.append(hn)
    p.gender= calc_gender(gender)
    p.birthDate =calc_dob(dob)
    p.active=True
    return p

def gen_procedurecode_array(procedures):
    if procedures is None:
        return None
    fhir_proc = []
    for p in procedures:
        concept = codeableconcept.CodeableConcept()
        c = coding.Coding()
        c.system = p["system"]
        c.code = p["code"]
        c.display = p["display"]
        concept.coding =[]
        concept.coding.append(c)
        concept.text=p["display"]
        fhir_proc.append(concept)
    if len(fhir_proc) > 0:
        return fhir_proc
    return None


def gen_started_datetime(dt, tm):
    if dt is None:
        return None

    fhirDtm = fhirdate.FHIRDate()
    fhirDtm.date =  datetime.strptime(dt, '%Y%m%d')
    if tm is None or len(tm) < 6:
        return fhirDtm
    studytm = datetime.strptime(tm[0:6], '%H%M%S')

    fhirDtm.date= fhirDtm.date.replace(hour=studytm.hour, minute =studytm.minute, second =studytm.second)

    return fhirDtm


def gen_reason(reason, reasonStr):
    if reason is None and reasonStr is None:
        return None
    reasonList = []
    if reason is None or len(reason) <= 0:
        rc = codeableconcept.CodeableConcept()
        rc.text=reasonStr
        reasonList.append(rc)
        return reasonList

    for r in reason:
        rc = codeableconcept.CodeableConcept()
        rc.coding = []
        c = coding.Coding()
        c.system = r["system"]
        c.code =r ["code"]
        c.display = r["display"]
        rc.coding.append(c)
        reasonList.append(rc)
    return reasonList


def gen_modality_coding(mod):
    c = coding.Coding()
    c.system = ACQUISITION_MODALITY_SYS
    c.code = mod
    return c


def update_study_modality_list(study: imagingstudy.ImagingStudy, modality: coding.Coding):
    if study.modality is None or len(study.modality) <= 0:
        study.modality = []
        study.modality.append(modality)
        return

    c = next(( mc for mc in study.modality if mc.system == modality.system and mc.code == modality.code), None)
    if c is not None:
        return

    study.modality.append(modality)
    return


def gen_instance_sopclass(SOPClassUID):
    c = coding.Coding()
    c.system=SOP_CLASS_SYS
    c.code = "urn:oid:" + SOPClassUID
    return c


def gen_coding_text_only(text):
    c = coding.Coding()
    c.code = text
    c.userSelected = True
    return c