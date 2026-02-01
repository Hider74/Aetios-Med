"""
Notes Parser
Parses markdown and text notes for ingestion.
"""
from pathlib import Path
from typing import List, Dict, Optional
import re
from dataclasses import dataclass


@dataclass
class NoteSection:
    """A section from a note document."""
    title: str
    content: str
    level: int  # Heading level (1-6)
    metadata: Dict


class NotesParser:
    """Parser for markdown and text notes."""
    
    def parse_markdown(self, file_path: Path) -> List[NoteSection]:
        """Parse a markdown file into sections."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        sections = []
        
        # Split by headings
        pattern = r'^(#{1,6})\s+(.+)$'
        lines = content.split('\n')
        
        current_section = {
            'title': file_path.stem,
            'content': [],
            'level': 0
        }
        
        for line in lines:
            match = re.match(pattern, line)
            
            if match:
                # Save previous section
                if current_section['content']:
                    sections.append(NoteSection(
                        title=current_section['title'],
                        content='\n'.join(current_section['content']).strip(),
                        level=current_section['level'],
                        metadata={'source': str(file_path)}
                    ))
                
                # Start new section
                level = len(match.group(1))
                title = match.group(2).strip()
                
                current_section = {
                    'title': title,
                    'content': [],
                    'level': level
                }
            else:
                current_section['content'].append(line)
        
        # Add last section
        if current_section['content']:
            sections.append(NoteSection(
                title=current_section['title'],
                content='\n'.join(current_section['content']).strip(),
                level=current_section['level'],
                metadata={'source': str(file_path)}
            ))
        
        return sections
    
    def parse_text(self, file_path: Path) -> NoteSection:
        """Parse a plain text file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return NoteSection(
            title=file_path.stem,
            content=content.strip(),
            level=1,
            metadata={'source': str(file_path)}
        )
    
    def extract_tags(self, content: str) -> List[str]:
        """Extract tags from content (e.g., #tag)."""
        tags = re.findall(r'#(\w+)', content)
        return list(set(tags))
    
    def extract_links(self, content: str) -> List[str]:
        """Extract URLs from content."""
        urls = re.findall(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            content
        )
        return urls
