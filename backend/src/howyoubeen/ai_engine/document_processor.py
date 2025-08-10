"""
Mock document processing and AI analysis

This module provides mock implementations for document processing and AI analysis.
In production, this would use real AI services like OpenAI or Anthropic via LiteLLM.
"""

import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..data_models.models import Document, LifeEvent, LifeFact, VisibilityCategory
from ..data_models.enums import ContentType, VisibilityCategoryType


class MockDocumentProcessor:
    """Mock document processing for development"""
    
    async def process_text_document(self, document: Document) -> Dict[str, Any]:
        """Mock processing of text documents"""
        await asyncio.sleep(0.2)  # Simulate processing time
        
        # Mock extracted information based on document type
        if "resume" in document.description.lower() if document.description else False:
            return {
                "type": "professional_info",
                "extracted_data": {
                    "skills": ["Python", "JavaScript", "Project Management"],
                    "experience": "5+ years in software development",
                    "education": "BS Computer Science"
                }
            }
        elif "journal" in document.description.lower() if document.description else False:
            return {
                "type": "personal_experiences",
                "extracted_data": {
                    "activities": ["hiking", "cooking", "reading"],
                    "recent_events": ["weekend trip to mountains", "dinner with friends"],
                    "interests": ["outdoor activities", "culinary experiments"]
                }
            }
        else:
            return {
                "type": "general_content",
                "extracted_data": {
                    "topics": ["technology", "lifestyle", "personal growth"],
                    "sentiment": "positive"
                }
            }
    
    async def process_image_document(self, document: Document) -> Dict[str, Any]:
        """Mock processing of image documents"""
        await asyncio.sleep(0.3)  # Simulate image analysis time
        
        return {
            "type": "visual_content",
            "extracted_data": {
                "description": "Photo showing outdoor activities and social gatherings",
                "objects": ["people", "outdoor setting", "food"],
                "activities": ["hiking", "dining", "socializing"],
                "mood": "happy and social"
            }
        }
    
    async def process_document(self, document: Document) -> Dict[str, Any]:
        """Process a document and extract information"""
        if document.content_type == ContentType.TEXT or document.content_type == ContentType.DOCUMENT:
            return await self.process_text_document(document)
        elif document.content_type == ContentType.IMAGE:
            return await self.process_image_document(document)
        else:
            return {
                "type": "unsupported",
                "extracted_data": {
                    "message": f"Processing for {document.content_type} not yet implemented"
                }
            }


class MockProfileGenerator:
    """Mock AI profile generation"""
    
    async def generate_user_summary(self, user_data: Dict[str, Any]) -> str:
        """Generate a comprehensive user summary"""
        await asyncio.sleep(0.5)  # Simulate AI processing
        
        name = user_data.get("full_name", "User")
        bio = user_data.get("bio", "")
        
        # Mock summary based on available data
        summary_parts = [f"Meet {name}"]
        
        if bio:
            summary_parts.append(f"who describes themselves as: {bio}")
        
        if "sources" in user_data and user_data["sources"]:
            platforms = [source.get("platform", "unknown") for source in user_data["sources"]]
            summary_parts.append(f"They're active on {', '.join(platforms)}")
        
        if "documents" in user_data and user_data["documents"]:
            doc_count = len(user_data["documents"])
            summary_parts.append(f"and has shared {doc_count} documents providing insights into their life")
        
        summary_parts.append("Their AI is ready to chat with friends and share appropriate updates based on their configured privacy preferences.")
        
        return ". ".join(summary_parts) + "."
    
    async def generate_life_events(self, extracted_data: List[Dict[str, Any]], visibility_config: List[VisibilityCategory]) -> List[LifeEvent]:
        """Generate life events from extracted data"""
        await asyncio.sleep(0.3)
        
        entries = []
        default_visibility = visibility_config[0] if visibility_config else VisibilityCategory(
            type=VisibilityCategoryType.PUBLIC
        )
        
        # Create mock diary entries based on extracted data
        for data in extracted_data[:3]:  # Limit to 3 entries for demo
            if data.get("type") == "personal_experiences":
                extracted = data.get("extracted_data", {})
                activities = extracted.get("activities", [])
                recent_events = extracted.get("recent_events", [])
                
                if recent_events:
                    entries.append(LifeEvent(
                        visibility=default_visibility,
                        start_date=datetime.now(),
                        summary=f"Recently enjoyed: {', '.join(recent_events)}. Activities included {', '.join(activities)}."
                    ))
        
        # Add a default entry if no specific experiences were found
        if not entries:
            entries.append(LifeEvent(
                visibility=default_visibility,
                start_date=datetime.now(),
                summary="Recently been focusing on personal growth and staying connected with friends and family."
            ))
        
        return entries
    
    async def generate_life_facts(self, extracted_data: List[Dict[str, Any]], visibility_config: List[VisibilityCategory]) -> List[LifeFact]:
        """Generate life facts from extracted data"""
        await asyncio.sleep(0.2)
        
        facts = []
        default_visibility = visibility_config[0] if visibility_config else VisibilityCategory(
            type=VisibilityCategoryType.PUBLIC
        )
        
        # Extract professional information
        for data in extracted_data:
            if data.get("type") == "professional_info":
                extracted = data.get("extracted_data", {})
                
                if "skills" in extracted:
                    facts.append(LifeFact(
                        visibility=default_visibility,
                        summary=f"Professional skills: {', '.join(extracted['skills'])}",
                        category="professional"
                    ))
                
                if "experience" in extracted:
                    facts.append(LifeFact(
                        visibility=default_visibility,
                        summary=f"Experience: {extracted['experience']}",
                        category="professional"
                    ))
            
            elif data.get("type") == "personal_experiences":
                extracted = data.get("extracted_data", {})
                
                if "interests" in extracted:
                    facts.append(LifeFact(
                        visibility=default_visibility,
                        summary=f"Interests: {', '.join(extracted['interests'])}",
                        category="interests"
                    ))
        
        # Add default facts if none were extracted
        if not facts:
            facts.extend([
                LifeFact(
                    visibility=default_visibility,
                    summary="Enjoys connecting with friends and exploring new experiences",
                    category="interests"
                ),
                LifeFact(
                    visibility=default_visibility,
                    summary="Values meaningful relationships and personal growth",
                    category="values"
                )
            ])
        
        return facts


# Global instances
document_processor = MockDocumentProcessor()
profile_generator = MockProfileGenerator()