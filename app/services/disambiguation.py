"""Disambiguation service for handling multiple entities in search results."""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

from app.services.semantic_search import SearchResult

logger = logging.getLogger(__name__)


@dataclass
class EntityGroup:
    """Group of search results belonging to the same entity/document."""
    entity_id: str
    entity_type: str  # document, section, topic
    entity_title: str
    results: List[SearchResult]
    combined_score: float
    metadata: Dict[str, Any]


@dataclass
class DisambiguationOption:
    """Option presented to user for disambiguation."""
    group_id: str
    title: str
    description: str
    entity_type: str
    result_count: int
    avg_score: float
    sample_text: str
    metadata: Dict[str, Any]


class DisambiguationService:
    """Service for disambiguating search results when multiple entities are found."""
    
    def __init__(self):
        pass
    
    def disambiguate_results(
        self, 
        results: List[SearchResult],
        max_groups: int = 5,
        min_score_threshold: float = 0.5
    ) -> Tuple[List[EntityGroup], Optional[List[DisambiguationOption]]]:
        """
        Disambiguate search results by grouping related entities.
        
        Args:
            results: List of search results
            max_groups: Maximum number of groups to return
            min_score_threshold: Minimum score threshold for grouping
            
        Returns:
            Tuple of (entity_groups, disambiguation_options)
            - If clear winner: entity_groups with 1 group, disambiguation_options=None
            - If ambiguous: entity_groups with multiple groups, disambiguation_options for user selection
        """
        if not results:
            return [], None
        
        # Group results by entity
        entity_groups = self._group_results_by_entity(results)
        
        # Filter by score threshold
        filtered_groups = [
            group for group in entity_groups 
            if group.combined_score >= min_score_threshold
        ]
        
        # Sort by combined score
        filtered_groups.sort(key=lambda x: x.combined_score, reverse=True)
        
        # Limit to max_groups
        limited_groups = filtered_groups[:max_groups]
        
        # Determine if disambiguation is needed
        if len(limited_groups) == 1:
            # Clear winner, no disambiguation needed
            return limited_groups, None
        elif len(limited_groups) > 1:
            # Multiple entities, need disambiguation
            disambiguation_options = self._create_disambiguation_options(limited_groups)
            return limited_groups, disambiguation_options
        else:
            # No groups meet threshold
            return [], None
    
    def _group_results_by_entity(self, results: List[SearchResult]) -> List[EntityGroup]:
        """
        Group search results by entity (document, section, or topic).
        
        Args:
            results: List of search results
            
        Returns:
            List of entity groups
        """
        # Strategy 1: Group by document_id (primary)
        document_groups = self._group_by_document(results)
        
        # Strategy 2: If too many documents, try grouping by section within top documents
        if len(document_groups) > 5:
            # Take top 3 documents and group their results by section
            top_docs = sorted(document_groups, key=lambda x: x.combined_score, reverse=True)[:3]
            section_groups = []
            
            for doc_group in top_docs:
                section_subgroups = self._group_by_section(doc_group.results)
                section_groups.extend(section_subgroups)
            
            return section_groups
        
        return document_groups
    
    def _group_by_document(self, results: List[SearchResult]) -> List[EntityGroup]:
        """Group results by document_id."""
        doc_groups = defaultdict(list)
        
        for result in results:
            doc_groups[result.document_id].append(result)
        
        entity_groups = []
        for doc_id, doc_results in doc_groups.items():
            if not doc_results:
                continue
            
            # Calculate combined score (weighted average)
            combined_score = self._calculate_combined_score(doc_results)
            
            # Get document title
            title = doc_results[0].document_title or f"Document {doc_id[:8]}"
            
            # Collect metadata
            metadata = {
                "document_id": doc_id,
                "document_type": doc_results[0].document_type,
                "result_count": len(doc_results),
                "sections": list(set(r.section for r in doc_results if r.section))
            }
            
            group = EntityGroup(
                entity_id=doc_id,
                entity_type="document",
                entity_title=title,
                results=doc_results,
                combined_score=combined_score,
                metadata=metadata
            )
            
            entity_groups.append(group)
        
        return entity_groups
    
    def _group_by_section(self, results: List[SearchResult]) -> List[EntityGroup]:
        """Group results by section within a document."""
        section_groups = defaultdict(list)
        
        for result in results:
            section = result.section or "general"
            section_groups[section].append(result)
        
        entity_groups = []
        for section, section_results in section_groups.items():
            if not section_results:
                continue
            
            combined_score = self._calculate_combined_score(section_results)
            doc_id = section_results[0].document_id
            doc_title = section_results[0].document_title or f"Document {doc_id[:8]}"
            
            title = f"{doc_title} - {section.title()}" if section != "general" else doc_title
            
            metadata = {
                "document_id": doc_id,
                "section": section,
                "document_type": section_results[0].document_type,
                "result_count": len(section_results)
            }
            
            group = EntityGroup(
                entity_id=f"{doc_id}_{section}",
                entity_type="section",
                entity_title=title,
                results=section_results,
                combined_score=combined_score,
                metadata=metadata
            )
            
            entity_groups.append(group)
        
        return entity_groups
    
    def _calculate_combined_score(self, results: List[SearchResult]) -> float:
        """Calculate combined score for a group of results."""
        if not results:
            return 0.0
        
        # Weighted average based on result position and individual scores
        total_weight = 0
        weighted_sum = 0
        
        for i, result in enumerate(results):
            # Higher weight for better positions and higher scores
            position_weight = 1.0 / (i + 1)  # Decreasing weight for later results
            score_weight = result.score
            
            combined_weight = position_weight * score_weight
            weighted_sum += combined_weight
            total_weight += position_weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _create_disambiguation_options(self, groups: List[EntityGroup]) -> List[DisambiguationOption]:
        """Create disambiguation options from entity groups."""
        options = []
        
        for group in groups:
            # Create description
            if group.entity_type == "document":
                description = f"Document with {group.metadata['result_count']} relevant sections"
                if group.metadata.get("sections"):
                    sections = ", ".join(group.metadata["sections"][:3])
                    description += f" (sections: {sections})"
            elif group.entity_type == "section":
                description = f"Section '{group.metadata['section']}' with {group.metadata['result_count']} relevant parts"
            else:
                description = f"Content with {group.metadata['result_count']} relevant parts"
            
            # Get sample text (first 200 chars)
            sample_text = group.results[0].text[:200] + "..." if group.results else ""
            
            option = DisambiguationOption(
                group_id=group.entity_id,
                title=group.entity_title,
                description=description,
                entity_type=group.entity_type,
                result_count=len(group.results),
                avg_score=group.combined_score,
                sample_text=sample_text,
                metadata=group.metadata
            )
            
            options.append(option)
        
        return options
    
    def select_entity_group(
        self, 
        groups: List[EntityGroup], 
        selected_group_id: str
    ) -> Optional[EntityGroup]:
        """
        Select a specific entity group by ID.
        
        Args:
            groups: List of entity groups
            selected_group_id: ID of the group to select
            
        Returns:
            Selected entity group or None if not found
        """
        for group in groups:
            if group.entity_id == selected_group_id:
                return group
        return None
