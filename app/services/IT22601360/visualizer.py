"""
Visualization Data Generator
Generates chart-ready data for React frontend
Student: IT22601360
"""

from typing import Dict, List, Any
from dataclasses import asdict
from app.utils.constants import CATEGORY_COLORS, CONCEPT_DESCRIPTIONS


class VisualizationGenerator:
    """
    Generates visualization data for the frontend
    
    Supports:
    - Concept relationship graph (for D3.js/vis.js)
    - Category distribution (for pie/bar charts)
    - Concept cards data
    - Mermaid diagram syntax
    """
    
    def __init__(self):
        self.category_colors = CATEGORY_COLORS
    
    def generate_all_visualizations(self, concepts: List[Any]) -> Dict:
        """
        Generate all visualization data at once
        
        Args:
            concepts: List of ExtractedConcept objects
            
        Returns:
            Dict with all visualization data
        """
        return {
            "graph": self.generate_concept_graph(concepts),
            "distribution": self.generate_category_distribution(concepts),
            "cards": self.generate_concept_cards(concepts),
            "mermaid": self.generate_mermaid_diagram(concepts),
            "summary_stats": self.generate_summary_stats(concepts)
        }
    
    def generate_concept_graph(self, concepts: List[Any]) -> Dict:
        """
        Generate node-link graph data for D3.js or vis.js
        
        Format compatible with:
        - react-force-graph
        - vis-network
        - d3-force
        """
        nodes = []
        links = []
        
        # Create nodes
        for i, concept in enumerate(concepts):
            nodes.append({
                "id": str(i),
                "label": concept.name,
                "name": concept.name,  # For react-force-graph
                "category": concept.category,
                "color": self.category_colors.get(concept.category, "#666666"),
                "confidence": concept.confidence,
                "description": concept.description,
                "size": 10 + (concept.confidence * 20),  # Size based on confidence
                "val": 10 + (concept.confidence * 20)    # For react-force-graph
            })
        
        # Create links based on related_concepts
        concept_id_map = {c.name.lower(): str(i) for i, c in enumerate(concepts)}
        
        for i, concept in enumerate(concepts):
            for related in concept.related_concepts:
                related_lower = related.lower()
                # Find matching concept
                for other_name, other_id in concept_id_map.items():
                    if related_lower in other_name or other_name in related_lower:
                        if str(i) != other_id:  # Avoid self-links
                            links.append({
                                "source": str(i),
                                "target": other_id,
                                "value": 1
                            })
                        break
        
        # Also link concepts in same category (weaker links)
        category_groups = {}
        for i, concept in enumerate(concepts):
            cat = concept.category
            if cat not in category_groups:
                category_groups[cat] = []
            category_groups[cat].append(str(i))
        
        for category, ids in category_groups.items():
            if len(ids) > 1:
                for j in range(len(ids) - 1):
                    # Only add if link doesn't exist
                    existing = [(l['source'], l['target']) for l in links]
                    if (ids[j], ids[j+1]) not in existing and (ids[j+1], ids[j]) not in existing:
                        links.append({
                            "source": ids[j],
                            "target": ids[j+1],
                            "value": 0.5  # Weaker link for same category
                        })
        
        return {
            "nodes": nodes,
            "links": links
        }
    
    def generate_category_distribution(self, concepts: List[Any]) -> Dict:
        """
        Generate pie/bar chart data for category distribution
        
        Compatible with:
        - Recharts
        - Chart.js
        - Victory
        """
        distribution = {}
        confidence_sum = {}
        
        for concept in concepts:
            cat = concept.category
            distribution[cat] = distribution.get(cat, 0) + 1
            confidence_sum[cat] = confidence_sum.get(cat, 0) + concept.confidence
        
        # Format for charts
        chart_data = []
        for category, count in distribution.items():
            avg_confidence = confidence_sum[category] / count if count > 0 else 0
            chart_data.append({
                "name": self._format_category_name(category),
                "value": count,
                "count": count,
                "category": category,
                "color": self.category_colors.get(category, "#666666"),
                "avgConfidence": round(avg_confidence, 2)
            })
        
        # Sort by count descending
        chart_data.sort(key=lambda x: x['count'], reverse=True)
        
        return {
            "data": chart_data,
            "total": len(concepts),
            "categories_found": len(distribution)
        }
    
    def generate_concept_cards(self, concepts: List[Any]) -> List[Dict]:
        """
        Generate card data for concept list display
        """
        cards = []
        
        for concept in concepts:
            cards.append({
                "name": concept.name,
                "category": concept.category,
                "categoryFormatted": self._format_category_name(concept.category),
                "description": concept.description,
                "confidence": round(concept.confidence * 100),  # Percentage
                "confidenceLevel": self._get_confidence_level(concept.confidence),
                "evidence": concept.evidence,
                "relatedConcepts": concept.related_concepts,
                "color": self.category_colors.get(concept.category, "#666666"),
                "icon": self._get_category_icon(concept.category)
            })
        
        # Sort by confidence descending
        cards.sort(key=lambda x: x['confidence'], reverse=True)
        
        return cards
    
    def generate_mermaid_diagram(self, concepts: List[Any]) -> str:
        """
        Generate Mermaid.js diagram syntax
        
        Can be rendered using mermaid.js in React
        """
        lines = ["graph TD"]
        
        # Group concepts by category
        categories = {}
        for concept in concepts:
            cat = concept.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(concept)
        
        # Create subgraphs for each category
        for category, cat_concepts in categories.items():
            category_formatted = self._format_category_name(category)
            lines.append(f"    subgraph {category_formatted.replace(' ', '_')}")
            
            for concept in cat_concepts:
                # Create safe node ID
                node_id = self._safe_mermaid_id(concept.name)
                lines.append(f'        {node_id}["{concept.name}"]')
            
            lines.append("    end")
        
        # Add relationships
        concept_id_map = {c.name.lower(): self._safe_mermaid_id(c.name) for c in concepts}
        
        for concept in concepts:
            src_id = self._safe_mermaid_id(concept.name)
            for related in concept.related_concepts:
                related_lower = related.lower()
                for name, tgt_id in concept_id_map.items():
                    if related_lower in name or name in related_lower:
                        if src_id != tgt_id:
                            lines.append(f"    {src_id} --> {tgt_id}")
                        break
        
        return "\n".join(lines)
    
    def generate_summary_stats(self, concepts: List[Any]) -> Dict:
        """
        Generate summary statistics
        """
        if not concepts:
            return {
                "total_concepts": 0,
                "categories_covered": 0,
                "avg_confidence": 0,
                "high_confidence_count": 0,
                "top_category": None
            }
        
        # Calculate stats
        total = len(concepts)
        categories = set(c.category for c in concepts)
        avg_confidence = sum(c.confidence for c in concepts) / total
        high_confidence = len([c for c in concepts if c.confidence >= 0.8])
        
        # Find top category
        category_counts = {}
        for c in concepts:
            category_counts[c.category] = category_counts.get(c.category, 0) + 1
        top_category = max(category_counts, key=category_counts.get)
        
        return {
            "total_concepts": total,
            "categories_covered": len(categories),
            "avg_confidence": round(avg_confidence * 100),
            "high_confidence_count": high_confidence,
            "top_category": self._format_category_name(top_category),
            "category_breakdown": {
                self._format_category_name(k): v 
                for k, v in category_counts.items()
            }
        }
    
    def _format_category_name(self, category: str) -> str:
        """Convert category slug to display name"""
        return category.replace('_', ' ').title()
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Convert confidence score to level string"""
        if confidence >= 0.9:
            return "very_high"
        elif confidence >= 0.75:
            return "high"
        elif confidence >= 0.5:
            return "medium"
        else:
            return "low"
    
    def _get_category_icon(self, category: str) -> str:
        """Get icon name for category (for Lucide icons in React)"""
        icons = {
            "data_structure": "Database",
            "algorithm": "GitBranch",
            "design_pattern": "Layers",
            "architecture": "Building2",
            "paradigm": "Boxes",
            "programming_concept": "Code"
        }
        return icons.get(category, "Code")
    
    def _safe_mermaid_id(self, name: str) -> str:
        """Convert name to safe Mermaid node ID"""
        # Remove special characters and spaces
        safe_id = name.replace(' ', '_').replace('-', '_')
        safe_id = ''.join(c for c in safe_id if c.isalnum() or c == '_')
        return safe_id
