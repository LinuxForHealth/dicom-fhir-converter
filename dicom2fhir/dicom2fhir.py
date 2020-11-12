import uuid
import os
from fhir import resources  as fr
from pydicom import dcmread
from pydicom import dataset

from . import dicom2fhirutils


def _add_imaging_study_instance(study: fr.imagingstudy.ImagingStudy, series: fr.imagingstudy.ImagingStudySeries,
                                ds: dataset.FileDataset, fp):
    selectedInstance = None
    instanceUID = ds.SOPInstanceUID
    if series.instance is not None:
        selectedInstance = next((i for i in series.instance if i.uid == instanceUID), None)
    else:
        series.instance = []

    if selectedInstance is not None:
        print("Error: SOP Instance UID is not unique")
        print(selectedInstance.as_json())
        return

    selectedInstance = fr.imagingstudy.ImagingStudySeriesInstance()
    selectedInstance.uid = instanceUID
    selectedInstance.sopClass = dicom2fhirutils.gen_instance_sopclass(ds.SOPClassUID)
    selectedInstance.number = ds.InstanceNumber

    try:
        if series.modality.code == "SR":
            seq = ds.ConceptNameCodeSequence
            selectedInstance.title = seq[0x0008, 0x0104]
        else:
            selectedInstance.title = '\\'.join(ds.ImageType)
    except:
        print("Unable to set instance title")

    series.instance.append(selectedInstance)
    study.numberOfInstances = study.numberOfInstances + 1
    series.numberOfInstances = series.numberOfInstances + 1
    return


def _add_imaging_study_series(study: fr.imagingstudy.ImagingStudy, ds: dataset.FileDataset, fp):
    seriesInstanceUID = ds.SeriesInstanceUID
    # TODO: Add test for studyInstanceUID ... another check to make sure it matches
    selectedSeries = None
    if study.series is not None:
        selectedSeries = next((s for s in study.series if s.uid == seriesInstanceUID), None)
    else:
        study.series = []

    if selectedSeries is not None:
        _add_imaging_study_instance(study, selectedSeries, ds, fp)
        return
    # Creating New Series
    series = fr.imagingstudy.ImagingStudySeries()
    series.uid = seriesInstanceUID
    try:
        series.description = ds.SeriesDescription
    except:
        pass

    series.number = ds.SeriesNumber
    series.numberOfInstances = 0

    series.modality = dicom2fhirutils.gen_modality_coding(ds.Modality)
    dicom2fhirutils.update_study_modality_list(study, series.modality)

    stime = None
    try:
        stime = ds.SeriesTime
    except:
        pass  # print("Series TimeDate is missing")

    try:
        sdate = ds.SeriesDate
        series.started = dicom2fhirutils.gen_started_datetime(sdate, stime)
    except:
        pass  # print("Series Date is missing")

    try:
        series.bodySite = dicom2fhirutils.gen_coding_text_only(ds.BodyPartExamined)
    except:
        pass  # print ("Body Part Examined missing")

    try:
        series.bodySite = dicom2fhirutils.gen_coding_text_only(ds.Laterality)
    except:
        pass  # print ("Laterality missing")

    # TODO: evaluate if we wonat to have inline "performer.actor" for the I am assuming "technician"
    # PerformingPhysicianName	0x81050
    # PerformingPhysicianIdentificationSequence	0x81052

    study.series.append(series)
    study.numberOfSeries = study.numberOfSeries + 1

    _add_imaging_study_instance(study, series, ds, fp)
    return


def _create_imaging_study(ds, fp, dcmDir) -> fr.imagingstudy.ImagingStudy:
    study = fr.imagingstudy.ImagingStudy()
    study.id = str(uuid.uuid4())
    study.status = "available"
    try:
        study.description = ds.StudyDescription
    except:
        pass  # missing study description

    study.identifier = []
    study.identifier.append(dicom2fhirutils.gen_accession_identifier(ds.AccessionNumber))
    study.identifier.append(dicom2fhirutils.gen_studyinstanceuid_identifier(ds.StudyInstanceUID))

    try:
        ipid = ds.IssuerOfPatientID
    except:
        pass  # print("Issuer of Patient ID is missing")

    study.contained = []
    patientReference = fr.fhirreference.FHIRReference()
    patientref = "patient.contained.inline"
    patientReference.reference = "#" + patientref
    study.contained.append(dicom2fhirutils.inline_patient_resource(patientref, ds.PatientID, ""
                                                                   , ds.PatientName, ds.PatientSex,
                                                                   ds.PatientBirthDate))
    study.subject = patientReference
    study.endpoint = []
    endpoint = fr.fhirreference.FHIRReference()
    endpoint.reference = "file://" + dcmDir

    study.endpoint.append(endpoint)

    procedures = []
    try:
        procedures = dicom2fhirutils.dcm_coded_concept(ds.ProcedureCodeSequence)
    except:
        pass  # procedure code sequence not found

    study.procedureCode = dicom2fhirutils.gen_procedurecode_array(procedures)

    studyTime = None
    try:
        studyTime = ds.StudyTime
    except:
        pass  # print("Study Date is missing")

    try:
        studyDate = ds.StudyDate
        study.started = dicom2fhirutils.gen_started_datetime(studyDate, studyTime)
    except:
        pass  # print("Study Date is missing")

    # TODO: we can add "inline" referrer
    # TODO: we can add "inline" reading radiologist.. (interpreter)

    reason = None
    reasonStr = None
    try:
        reason = dicom2fhirutils.dcm_coded_concept(ds.ReasonForRequestedProcedureCodeSequence)
    except:
        pass  # print("Reason for Request procedure Code Seq is not available")

    try:
        reasonStr = ds.ReasonForTheRequestedProcedure
    except:
        pass  # print ("Reason for Requested procedures not found")

    study.reasonCode = dicom2fhirutils.gen_reason(reason, reasonStr)

    study.numberOfSeries = 0
    study.numberOfInstances = 0
    _add_imaging_study_series(study, ds, fp)
    return study


def process_dicom_2_fhir(dcmDir: str) -> fr.imagingstudy.ImagingStudy:
    dcmDict = {}
    files = []
    #TODO: subdirectory must be traversed
    for r, d, f in os.walk(dcmDir):
        for file in f:
            files.append(os.path.join(r, file))

    studyInstanceUID = None
    imagingStudy = None
    for fp in files:
        try:
            with dcmread(fp, None, [0x7FE00010], force=True) as ds:
                if studyInstanceUID is None:
                    studyInstanceUID = ds.StudyInstanceUID
                if studyInstanceUID != ds.StudyInstanceUID:
                    raise Exception("Incorrect DCM path, more than one study detected")
                    return None
                if imagingStudy is None:
                    imagingStudy = _create_imaging_study(ds, fp, dcmDir)
                else:
                    _add_imaging_study_series(imagingStudy, ds, fp)
        except:
            pass #file is not a dicom file

    return imagingStudy
