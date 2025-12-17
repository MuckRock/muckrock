#!/usr/bin/env python
"""
Test script to query OpenAI and examine citation annotation structure.
This will help us understand the index parameter and citation format.
"""
import os
import sys
import json
from pathlib import Path

# Add the foia-coach-api to the path
sys.path.insert(0, str(Path(__file__).parent / 'foia-coach-api'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
import django
django.setup()

from apps.jurisdiction.services.providers.openai_provider import OpenAIProvider
from apps.jurisdiction.models import JurisdictionResource

def test_citations():
    """Send a test query and print the full annotation structure."""

    # Initialize provider
    provider = OpenAIProvider()

    # Get a test state that has resources
    resources = JurisdictionResource.objects.filter(
        provider_uploads__provider='openai',
        provider_uploads__index_status='ready'
    ).distinct()

    if not resources.exists():
        print("No OpenAI resources found with 'ready' status")
        return

    # Use the first available state
    test_resource = resources.first()
    state = test_resource.jurisdiction_abbrev
    print(f"\nUsing state: {state}")
    print(f"Resource: {test_resource.display_name}")
    print(f"File: {test_resource.file.name}\n")

    # Send a test query
    question = "What is the process for submitting a FOIA request?"

    print(f"Question: {question}\n")
    print("Sending query to OpenAI...\n")

    try:
        # We need to look at the raw response, so let's call the API directly
        from openai import OpenAI

        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

        # Get the vector store for this state
        from apps.jurisdiction.models import ResourceProviderUpload
        uploads = ResourceProviderUpload.objects.filter(
            resource__jurisdiction_abbrev=state,
            provider='openai',
            index_status='ready'
        )

        if not uploads.exists():
            print("No ready uploads found")
            return

        vector_store_id = uploads.first().provider_store_id
        print(f"Using vector store: {vector_store_id}\n")

        # Create a response using the Responses API (not Chat Completions)
        response = client.responses.create(
            model="gpt-4o",
            input=question,
            tools=[{
                "type": "file_search",
                "vector_store_ids": [vector_store_id]
            }],
            include=["file_search_call.results"]
        )

        print("=" * 80)
        print("FULL RESPONSE STRUCTURE")
        print("=" * 80)
        print(json.dumps(response.model_dump(), indent=2, default=str))
        print("\n")

        # Process output items
        for item in response.output:
            if item.type == "message" and item.role == "assistant":
                print("=" * 80)
                print("ASSISTANT MESSAGE CONTENT")
                print("=" * 80)

                for content in item.content:
                    if content.type == "output_text":
                        print(f"Text: {content.text}")
                        print("\n")

                        # Check for annotations
                        if hasattr(content, 'annotations') and content.annotations:
                            print("=" * 80)
                            print("ANNOTATIONS (CITATIONS)")
                            print("=" * 80)

                            for idx, annotation in enumerate(content.annotations):
                                print(f"\nAnnotation #{idx + 1}:")
                                print(f"  Type: {annotation.type}")

                                # Print all attributes of the annotation
                                print(f"  All attributes: {dir(annotation)}")
                                print(f"  Raw annotation: {annotation}")

                                # Check for common attributes
                                if hasattr(annotation, 'text'):
                                    print(f"  Text: {annotation.text}")
                                if hasattr(annotation, 'start_index'):
                                    print(f"  Start Index: {annotation.start_index}")
                                if hasattr(annotation, 'end_index'):
                                    print(f"  End Index: {annotation.end_index}")
                                if hasattr(annotation, 'file_citation'):
                                    print(f"  File Citation: {annotation.file_citation}")
                                if hasattr(annotation, 'file_id'):
                                    print(f"  File ID: {annotation.file_id}")
                                if hasattr(annotation, 'filename'):
                                    print(f"  Filename: {annotation.filename}")
                                if hasattr(annotation, 'quote'):
                                    print(f"  Quote: {annotation.quote}")

                        else:
                            print("\nNo annotations found")
                print("\n")

    except Exception as exc:
        print(f"Error: {exc}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_citations()
