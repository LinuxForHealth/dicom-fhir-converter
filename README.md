# dicom-fhir-converter
DICOM FHIR converter is an open source python library that accepts a DICOM directory as an input.
It processes all ".dcm" files (instances) within that directory. It expects that directory will only contain files for a single study.
If multiple studies detected, an exception is raised.

This library utilizes the following projects:
- fhir.resources project (https://pypi.org/project/fhir.resources/) - used to create FHIR models
- pydicom (https://pydicom.github.io/) - used to read dicom instances




## Usage

```
dicom2fhir.process_dicom_2_fhir("directory")
```

The dicom file (*.dcm) represents a single instance within DICOM study. A study is a collection of instances grouped by series.
The assumption is that all instances are copied into a single folder prior to calling this function. The flattened structure is then consolidated into a single FHIR Imaging Study resource.

## Structure 
The FHIR Imaging Study id is being generated internally within the library. 
The DICOM Study UID is actually stored as part of the "identifier" (see ```"system":"urn:dicom:uid"``` object for DICOM study uid.

The model is meant to be self-inclusive (to mimic the DICOM structure), it does not produce separate resources for other resource types.
Instead, it uses "contained" resource to include all of the supporting data. (See "subject" with ```"reference": "#patient.contained.inline"```

This approach will allow downstream systems to map inline resources to new or existing FHIR resource types replacing inline references to actual object within FHIR Server.
Until such time, all of the a data is included within a single resource.

### Sample Output
```
{
    "id": "011d5e1b-0402-445a-b417-21b86af500dc",
    "identifier": [
        {
            "type": {
                "coding": [
                    {
                        "code": "ACSN",
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0203"
                    }
                ]
            },
            "use": "usual",
            "value": "DAC007_CRLAT"
        },
        {
            "system": "urn:dicom:uid",
            "value": "urn:oid:1.3.6.1.4.1.5962.99.1.2008629345.2009981611.1359218327649.129.0"
        }
    ],,
    "started": "2005-09-06T16:39:26",
    "status": "available",
    "subject": {
        "reference": "#patient.contained.inline"
    },
    "resourceType": "ImagingStudy"
    "endpoint": [
        {
            "reference": "file:///dcm1"
        }
    ],
    "modality": [
        {
            "code": "CR",
            "system": "http://dicom.nema.org/resources/ontology/DCM"
        }
    ],
    "numberOfInstances": 1,
    "numberOfSeries": 1,
    "contained": [
        {
            "id": "patient.contained.inline",
            "active": true,
            "gender": "unknown",
            "identifier": [
                {
                    "system": "urn:oid:",
                    "type": {
                        "coding": [
                            {
                                "code": "MR",
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203"
                            }
                        ]
                    },
                    "use": "usual",
                    "value": "DAC007_CRLAT"
                }
            ],
            "name": [
                {
                    "family": "CR",
                    "given": [
                        "LateralityCheck"
                    ]
                }
            ],
            "resourceType": "Patient"
        }
    ],
    "series": [
        {
            "bodySite": {
                "code": "CHEST",
                "userSelected": true
            },
            "instance": [
                {
                    "number": 1,
                    "sopClass": {
                        "code": "urn:oid:1.2.840.10008.5.1.4.1.1.1",
                        "system": "urn:ietf:rfc:3986"
                    },
                    "title": "DERIVED\\PRIMARY\\IT",
                    "uid": "1.3.6.1.4.1.5962.99.1.2008629345.2009981611.1359218327649.128.0"
                }
            ],
            "modality": {
                "code": "CR",
                "system": "http://dicom.nema.org/resources/ontology/DCM"
            },
            "number": 1,
            "numberOfInstances": 1,
            "started": "2005-09-06T16:39:28",
            "uid": "1.3.6.1.4.1.5962.99.1.2008629345.2009981611.1359218327649.130.0"
        }
    ]
}
```



