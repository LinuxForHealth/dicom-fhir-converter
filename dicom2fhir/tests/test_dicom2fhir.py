import os
import unittest
from .. import dicom2fhirutils
from .. import dicom2fhir
from fhir import resources as fr

class testDicom2FHIR(unittest.TestCase):
    def test_instance_dicom2fhir(self):
        dcmDir = os.path.join(os.getcwd(), "dicom2fhir", "tests", "resources", "dcm-instance")
        study: fr.ImagingStudy
        study = dicom2fhir.process_dicom_2_fhir(dcmDir)

        self.assertIsNotNone(study, "No ImagingStudy was generated")
        self.assertEqual(study.numberOfSeries, 1, "Number of Series in the study mismatch")
        self.assertEqual(study.numberOfInstances, 1, "Number of Instances in the study mismatch")
        self.assertIsNotNone(study.series,"Series was not built for the study")
        self.assertEqual(len(study.modality), 1, "Series must list only one modality")
        self.assertEqual(study.modality[0].code, "CR", "Incorrect modality detected")
        self.assertEqual(len(study.series), 1, "Number objects in Series Array: mismatch")
        self.assertEqual(len(study.series[0].instance), 1, "Number objects in Instance Array: mismatch")

        series: fr.ImagingSeries
        series = study.series [0]
        self.assertIsNotNone(series, "Missing Series")
        self.assertEqual(series.bodySite.code, 'CHEST', "CHEST is expected bodys site")
        self.assertTrue(series.bodySite.userSelected, "Body Site is currently not a coded concept. Text is used so userSelected value must be set to true")
        instance: fr.ImagingInstance
        instance = series.instance[0]
        self.assertIsNotNone(instance, "Missing Instance")


    def test_multi_instance_dicom(self):
        dcmDir =  os.path.join(os.getcwd(), "dicom2fhir", "tests", "resources", "dcm-multi-instance")
        study: fr.ImagingStudy
        study = dicom2fhir.process_dicom_2_fhir(dcmDir)
        self.assertIsNotNone(study, "No ImagingStudy was generated")
        self.assertEqual(study.numberOfSeries, 1)
        self.assertEqual(study.numberOfInstances, 5)
        self.assertIsNotNone(study.series, "Series was not built for the study")
        self.assertEqual(len(study.modality), 1, "Only single modality expected for this study" )
        self.assertEqual(study.modality[0].code, "CR")
        self.assertEqual(len(study.series), 1, "Incorrect number of series detected")
        self.assertEqual(len(study.series[0].instance), 5, "Incorrect number of instances detected")

    def test_multi_series_dicom(self):
        dcmDir =  os.path.join(os.getcwd(), "dicom2fhir", "tests", "resources", "dcm-multi-series")
        study: fr.ImagingStudy
        study = dicom2fhir.process_dicom_2_fhir(dcmDir)
        self.assertIsNotNone(study, "No ImagingStudy was generated")
        self.assertEqual(study.numberOfSeries, 4, "Number of Series in the study mismatch")
        self.assertEqual(study.numberOfInstances, 4,"Number of Instances in the study mismatch" )
        self.assertIsNotNone(study.series, "Series was not built for the study")
        self.assertEqual(len(study.modality), 1, "Only single modality expected for this study")
        self.assertEqual(study.modality[0].code, "CR", "Incorrect Modality detected")
        self.assertEqual(len(study.series),4, "Number of series in the study: mismatch")



