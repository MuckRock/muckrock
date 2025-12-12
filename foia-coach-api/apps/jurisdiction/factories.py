"""
Factory classes for testing jurisdiction models
"""
# Standard Library
import uuid

# Third Party
import factory
from django.core.files.base import ContentFile
from factory.django import DjangoModelFactory

# Local
from apps.jurisdiction.models import JurisdictionResource, ResourceProviderUpload


class JurisdictionResourceFactory(DjangoModelFactory):
    """Factory for creating JurisdictionResource test instances"""

    class Meta:
        model = JurisdictionResource

    jurisdiction_id = factory.Sequence(lambda n: n + 1)
    jurisdiction_abbrev = factory.Iterator(['CO', 'GA', 'TN', 'CA', 'NY'])

    display_name = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('paragraph')

    # Create a test file with some content
    file = factory.LazyAttribute(
        lambda obj: ContentFile(
            f"Test content for {obj.display_name}\n\nThis is a test resource.".encode(),
            name=f"test_resource_{obj.jurisdiction_abbrev}.txt"
        )
    )

    resource_type = factory.Iterator([
        'law_guide',
        'request_tips',
        'exemptions',
        'agency_info',
        'case_law',
        'general'
    ])

    is_active = True
    order = factory.Sequence(lambda n: n)


class ResourceProviderUploadFactory(DjangoModelFactory):
    """Factory for creating ResourceProviderUpload test instances"""

    class Meta:
        model = ResourceProviderUpload

    resource = factory.SubFactory(JurisdictionResourceFactory)
    provider = factory.Iterator(['openai', 'gemini', 'mock'])

    provider_file_id = factory.LazyAttribute(
        lambda obj: f'{obj.provider}-file-{uuid.uuid4()}'
    )
    provider_store_id = factory.LazyAttribute(
        lambda obj: f'{obj.provider}-store-{uuid.uuid4()}'
    )
    provider_metadata = factory.Dict({'uploaded': True})

    index_status = 'pending'
    error_message = ''
