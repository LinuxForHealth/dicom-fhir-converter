from setuptools import setup, find_packages


REQUIREMENTS = 'requirements.txt'


def load_requirements():
    try:
        with open(REQUIREMENTS) as fh:
            reqs = fh.readlines()
            return reqs
    except IOError:
        raise StopIteration


test_requirements = [
    "pytest==4.6.3",
    "pytest-cov==2.7.1"
]

requirements = load_requirements()


setup(
    description="Convert dicoms to fhir ImagingStudy model",
    install_requires=requirements,
    license="BSD license",
    include_package_data=True,
    keywords="fhir, resources, python, hl7, health IT, healthcare",
    name="dicom2fhir",
    #namespace_packages=["dicom2fhir"],
    #package_dir={"": ""},
    packages=find_packages('.', exclude=["*tests*"]),
    #test_suite="tests",
    tests_require=test_requirements + requirements,
    url="https://github.ibm.com/ebaron/dicom-fhir-converter",
    version="0.0.1",
    python_requires=">=3.6"
)