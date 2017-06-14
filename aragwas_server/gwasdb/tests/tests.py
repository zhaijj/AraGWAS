import os
from django.test import TestCase
from django.shortcuts import reverse
from django.contrib.auth.models import AnonymousUser, User
from rest_framework.test import APIRequestFactory
from gwasdb.models import *
from gwasdb.serializers import *
from gwasdb import rest
from rest_framework import status
from gwasdb import hdf5
import numpy as np


# Create your tests here.
# Basic db initialization:
def generate_basic_db():
    """
    generate database entries for tests
    """
    genotype1 = Genotype.objects.create(name="1001genomes", version="1.2")
    phenotype1 = Phenotype.objects.create(name="Length of something")
    study1 = Study.objects.create(name="McIntosh et al., 2010", transformation="log", method="LMM", genotype=genotype1, phenotype = phenotype1)
    study2 = Study.objects.create(name="Test2", transformation="log", method="LMM", genotype=genotype1, phenotype = phenotype1)
    SNP1 = SNP.objects.create(chromosome=1, position=45602, annotation="TAIR10", genotype=genotype1)
    SNP2 = SNP.objects.create(chromosome=2, position=100000, annotation="TAIR10", genotype=genotype1)
    SNP3 = SNP.objects.create(chromosome=2, position=100100, annotation="TAIR10", genotype=genotype1)
    association1 = Association.objects.create(study=study1, snp = SNP1, maf=0.24, pvalue=1.4e-8)
    association2 = Association.objects.create(study=study1, snp=SNP2, maf=0.24, pvalue=1.4e-8)
    association3 = Association.objects.create(study=study2, snp=SNP2, maf=0.24, pvalue=1.4e-8)



# Test models, to implement when we'll have methods
class ModelRelationshipTests(TestCase):
    def test_generation_basic_db(self):
        """
        Simple test to generate basic database with one genotype, one study
        :return:
        """
        generate_basic_db()

        self.assertIs(len(Study.objects.all()) == 1, True)

    def test_db_connections(self):
        """
        Test basic database connections in toy example
        :return:
        """
        generate_basic_db()
        self.assertEqual(Study.objects.get(pk=1).genotype, Genotype.objects.get(pk=1)) # Test study-genotype relationship
        self.assertNotEqual(Association.objects.get(pk=1).snp, Association.objects.get(pk=2).snp) # Test independence of associations

class SerializerTests(TestCase):

    def test_study_list_serializers(self):
        """
        Test the StudyListSerializer
        """
        generate_basic_db()
        study = Study.objects.get(pk=1)
        serialized = StudySerializer(study)
        # print(serialized.data)
        associations = Association.objects.all()
        snp2 = SNP.objects.get(pk=2)
        serialized_assoc = AssociationListSerializer(associations, many=True)
        # print(serialized_assoc.data[0]['snp'])
        self.assertEqual(serialized.data['name'], study.name)
        self.assertEqual(serialized_assoc.data[1]['snp'], snp2.get_name())


class ApiVersionTests(TestCase):

    def test_get_api_version(self):
        """test that api verison is returned"""

        factory = APIRequestFactory()
        request = factory.get(reverse('api-version'))
        view = rest.ApiVersionView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'date': '2017-04-26T09:11:18Z', 'version': 'N/A', 'build_url': None, 'build': 'N/A', 'github_url': 'https://github.com/1001genomes/aragwas/commit', 'githash': 'N/A'})

class SNPTests(TestCase):

    def test_neightboring_snps(self):
        """
        Test the rest.py neighboring_snps serializer
        """
        generate_basic_db()
        factory = APIRequestFactory()
        view = rest.SNPLocalViewSet.as_view(actions={'get': 'neighboring_snps'})
        request = factory.get(reverse('snp-neighboring-snps', args=(2,))+'?include=True')
        response1 = view(request, pk=2)
        request = factory.get(reverse('snp-neighboring-snps', args=(2,)))
        response2 = view(request, pk=2)
        request = factory.get(reverse('snp-neighboring-snps', args=(1,)))
        response3 = view(request, pk=1)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response1.data), 2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response2.data), 1)
        self.assertEqual(response3.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response3.data), 0)

class AssociationOfPhenotypeTests(TestCase):

    def test_association_of_phenotype(self):
        """
        Test the rest association of phenotype
        :return:
        """
        generate_basic_db()
        view = rest.AssociationsOfPhenotypeViewSet.as_view()



class HDF5LoadingTests(TestCase):

    def __init__(self, *args, **kwargs):
        self.hdf5_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources/gwas.hdf5')
        super(HDF5LoadingTests, self).__init__(*args, **kwargs)

    def test_load_top_associations_by_top_hits(self):
        """Test if top associations by number of hits cann be retrieved"""
        top_hits = [('1', 6369772, 5.559458119903501, 0.1386861313868613, 19),
                    ('2', 18351161, 5.221548337450959, 0.08029197080291971, 11),
                    ('3', 18057816, 4.795206143400829, 0.2116788321167883, 29),
                    ('4', 429928, 6.555416448260276, 0.4233576642335766, 58),
                    ('5', 18577788, 6.219812361173065, 0.15328467153284672, 21)]

        top_associations, thresholds = hdf5.get_top_associations2(self.hdf5_file, 10, top_or_threshold='top')
        assert thresholds['bonferoni_threshold01'] == 7.3140147710960965
        assert thresholds['bonferoni_threshold05'] == 6.615044766760077
        assert thresholds['bh_threshold'] == 6.6150447667600778
        assert thresholds['total_associations'] == 206070
        assert isinstance(top_associations, np.core.records.recarray)
        assert len(top_associations) == 50
        assert top_associations.dtype.names == ('chr', 'position', 'score', 'maf', 'mac')
        assert top_associations.dtype[0] == np.dtype('<U1')
        assert top_associations.dtype[1] == np.dtype('int32')
        assert top_associations.dtype[2] == np.dtype('float64')
        assert top_associations.dtype[3] == np.dtype('float64')
        assert top_associations.dtype[4] == np.dtype('int32')
        for i in range(0 ,5):
            assert top_associations[i*10].tolist() == top_hits[i]

    def test_load_top_associations_by_top_threshold(self):
        """Test if top associations by thresholds """
        top_associations, thresholds = hdf5.get_top_associations2(self.hdf5_file, 5, top_or_threshold='threshold')
        assert isinstance(top_associations, np.core.records.recarray)
        assert len(top_associations) == 14
        for assoc in top_associations:
            assert assoc['score'] >= 5.0

        top_associations_by_e, thresholds = hdf5.get_top_associations2(self.hdf5_file, 1e-5, top_or_threshold='threshold')
        assert isinstance(top_associations, np.core.records.recarray)
        assert len(top_associations) == len(top_associations_by_e)
        for i, assoc in enumerate(top_associations_by_e):
            assert assoc.tolist() == top_associations[i].tolist()

    def test_regroup_top_assocations(self):
        top_associations, thresholds = hdf5.get_top_associations2(self.hdf5_file, 5, top_or_threshold='threshold')
        top_associations = hdf5.regroup_associations(top_associations)
        top_associations[0].tolist() == ('4',   429928,  6.55541645,  0.42335766, 58)
        top_associations[-1].tolist() == ('5', 18606578,  5.07844918,  0.47445255, 65)