import uuid
import os
import json
from fhir import resources  as fr
from pydicom import dcmread
from pydicom import dataset

from . import fhirutils


#TODO: So I feel like everytime the item is missing in DICOM, accessing that item results in runtime error.. we will need to wrap each call in separately?


def dcm_coded_concept(CodeSequence):
    concepts = []
    for seq in CodeSequence:
        concept = {}
        concept["code"] = seq[0x0008, 0x0100].value
        concept["system"] = seq[0x0008, 0x0102].value
        concept["display"] = seq[0x0008, 0x0104].value
        concepts.append(concept)
    return concepts


def addInstance(study: fr.imagingstudy.ImagingStudy, series: fr.imagingstudy.ImagingStudySeries, ds: dataset.FileDataset, fp):
    selectedInstance=None
    instanceUID=ds.SOPInstanceUID
    if series.instance is not None:
        selectedInstance =  next( (i for i in series.instance if i.uid == instanceUID ), None)
    else:
        series.instance =[]

    if selectedInstance is not None:
        print ("Error: SOP Instance UID is not unique")
        print(selectedInstance.as_json())
        return

    selectedInstance = fr.imagingstudy.ImagingStudySeriesInstance()
    selectedInstance.uid = instanceUID
    selectedInstance.sopClass = fhirutils.gen_instance_sopclass(ds.SOPClassUID)
    selectedInstance.number = ds.InstanceNumber

    try:
        if series.modality.code == "SR":
            seq = ds.ConceptNameCodeSequence
            selectedInstance.title = seq[0x0008, 0x0104]
        else:
            selectedInstance.title='\\'.join(ds.ImageType)
    except:
        print("Unable to set instance title")


    series.instance.append(selectedInstance)
    study.numberOfInstances = study.numberOfInstances + 1
    series.numberOfInstances = series.numberOfInstances + 1
    return

def addSeries(study: fr.imagingstudy.ImagingStudy, ds: dataset.FileDataset, fp):
    seriesInstanceUID = ds.SeriesInstanceUID
    # TODO: Add test for studyInstanceUID ... another check to make sure it matches
    selectedSeries = None
    if study.series is not None:
        selectedSeries = next((s for s in study.series if s.uid == seriesInstanceUID), None)
    else:
        study.series = []

    if selectedSeries is not None:
        addInstance(study, selectedSeries,ds, fp)
        return
    #Creating New Series
    series = fr.imagingstudy.ImagingStudySeries()
    series.uid=seriesInstanceUID
    try:
        series.description =ds.SeriesDescription
    except:
        print ("Series Description not found")

    series.number =ds.SeriesNumber
    series.numberOfInstances = 0

    series.modality = fhirutils.gen_modality_coding(ds.Modality)
    fhirutils.update_study_modality_list(study, series.modality)

    stime=None
    try:
        stime = ds.SeriesTime
    except:
        print("Series TimeDate is missing")

    try:
        sdate = ds.SeriesDate
        series.started = fhirutils.gen_started_datetime(sdate, stime)
    except:
        print("Series Date is missing")


    try:
        series.bodySite = fhirutils.gen_coding_text_only(ds.BodyPartExamined)
    except:
        print ("Body Part Examined missing")

    try:
        series.bodySite = fhirutils.gen_coding_text_only(ds.Laterality)
    except:
        print ("Laterality missing")

    #TODO: evaluate if we wonat to have inline "performer.actor" for the I am assuming "technician"
    # PerformingPhysicianName	0x81050
    # PerformingPhysicianIdentificationSequence	0x81052

    study.series.append(series)
    study.numberOfSeries = study.numberOfSeries + 1

    addInstance(study, series, ds, fp)
    return


def createImagingStudy(ds, fp) -> fr.imagingstudy.ImagingStudy:
    study=fr.imagingstudy.ImagingStudy()
    study.id = str(uuid.uuid4())
    study.status="available"
    try:
        study.description = ds.StudyDescription
    except:
        print("Study Description is missing")

    # TODO: ds.IssuerOfAccessionNumberSequence unable to obtain the object and identify correct logic for issuer (SQ)
    study.identifier = []
    study.identifier.append(fhirutils.gen_accession_identifier(ds.AccessionNumber))
    study.identifier.append(fhirutils.gen_studyinstanceuid_identifier(ds.StudyInstanceUID))


    #TODO: ds.IssuerOfPatientID as IPID is not being accepted
    #TODO: ds.PatientBirthTime is also not part of the FileDataset
    study.contained= []
    patientReference = fr.fhirreference.FHIRReference()
    patientref = "patient.contained.inline"
    patientReference.reference = "#" + patientref
    study.contained.append(fhirutils.inline_patient_resource(patientref, ds.PatientID, ""
                                                             , ds.PatientName, ds.PatientSex, ds.PatientBirthDate))
    study.subject =  patientReference
    study.endpoint = []
    endpoint = fr.fhirreference.FHIRReference()
    #TODO: at this point we need a correct reference to the directory
    endpoint.reference="file:///" +dcmDir
    study.endpoint.append(endpoint)

    procedures = []
    try:
        procedures = dcm_coded_concept(ds.ProcedureCodeSequence)
    except:
        print("Procedure Sequence not found. This is not required FHIR field")

    study.procedureCode = fhirutils.gen_procedurecode_array(procedures)

    studyTime=None
    try:
        studyTime = ds.StudyTime
    except:
        print("Study Date is missing")


    try:
        studyDate = ds.StudyDate
        study.started = fhirutils.gen_started_datetime(studyDate, studyTime)
    except:
        print("Study Date is missing")

    #TODO: we can add "inline" referrer
    #TODO: we can add "inline" reading radiologist.. (interpreter)

    #TODO: untested - could not find dicom sample with Reason for Requested Procedure (0040, 1002) and Seq (0040, 100A) populated
    reason = None
    reasonStr = None
    try:
        reason = dcm_coded_concept(ds.ReasonForRequestedProcedureCodeSequence)
    except:
        print("Reason for Request procedure Code Seq is not available")

    try:
        reasonStr = ds.ReasonForTheRequestedProcedure
    except:
        print ("Reason for Requested procedures not found")

    study.reasonCode = fhirutils.gen_reason(reason, reasonStr)
    ##end of untested


   # study.numberOfSeries = ds.NumberOfStudyRelatedSeries
   # study.numberOfInstances =ds.NumberOfStudyRelatedInstances

    study.numberOfSeries=0
    study.numberOfInstances=0
    addSeries(study, ds, fp)
    return study

def process_dicom_2_fhir(dcmDir: str) ->  fr.imagingstudy.ImagingStudy:
    dcmDict = {}
    files = []
    for r, d, f in os.walk(dcmDir):
        for file in f:
            if '.dcm' in file:
                files.append(os.path.join(r, file))
    studyInstanceUID = None
    imagingStudy=None
    for fp in files:
        with dcmread(fp, None,[0x7FE00010], force=True) as ds:
            if studyInstanceUID is None:
                studyInstanceUID = ds.StudyInstanceUID
            if studyInstanceUID != ds.StudyInstanceUID:
                raise Exception("Incorrect DCM path, more than one study detected")
                return None

            if imagingStudy is None:
                imagingStudy = createImagingStudy(ds, fp)
            else:
                addSeries(imagingStudy, ds, fp)

    return imagingStudy

print ("---Current Output---")
dcmDir="multi-instance"
study = process_dicom_2_fhir(dcmDir)
output = dcmDir + "/dicom2fhir.json"
with open(output, 'w') as out:
    json.dump(study.as_json(), out)

