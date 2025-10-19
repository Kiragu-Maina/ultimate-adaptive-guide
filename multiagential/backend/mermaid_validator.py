import re
from typing import Dict, List, Union, Tuple

class MermaidValidationError(Exception):
    """Exception raised when Mermaid validation fails."""
    pass

class MermaidValidator:
    """Validates Mermaid diagram syntax before loading."""
    
    # Known Mermaid diagram types and their basic patterns
    DIAGRAM_TYPES = {
        'flowchart': ['flowchart', 'graph'],
        'sequence': ['sequenceDiagram'],
        'class': ['classDiagram'],
        'state': ['stateDiagram', 'stateDiagram-v2'],
        'er': ['erDiagram'],
        'journey': ['journey'],
        'gantt': ['gantt'],
        'pie': ['pie'],
        'requirement': ['requirementDiagram'],
        'gitgraph': ['gitGraph']
    }
    
    # Dangerous patterns that should be blocked
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',               # JavaScript protocols
        r'on\w+\s*=',                # Event handlers
        r'eval\s*\(',                # Eval function
        r'Function\s*\(',            # Function constructor
        r'setTimeout\s*\(',          # Timer functions
        r'setInterval\s*\(',
        r'alert\s*\(',               # Alert functions
        r'confirm\s*\(',
        r'prompt\s*\(',
    ]
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate(self, mermaid_content: str) -> Dict[str, Union[bool, List[str]]]:
        """
        Validates Mermaid diagram content.
        
        Args:
            mermaid_content: The Mermaid diagram content to validate
            
        Returns:
            Dict containing validation results with keys:
            - 'valid': Boolean indicating if the content is valid
            - 'errors': List of error messages
            - 'warnings': List of warning messages
            - 'diagram_type': Detected diagram type (if valid)
        """
        self.errors = []
        self.warnings = []
        
        if not mermaid_content or not isinstance(mermaid_content, str):
            self.errors.append("Content must be a non-empty string")
            return self._build_result(False)
        
        # Clean the content
        content = self._clean_content(mermaid_content)
        
        # Check for dangerous patterns
        if not self._check_security(content):
            return self._build_result(False)
        
        # Detect diagram type
        diagram_type = self._detect_diagram_type(content)
        if not diagram_type:
            self.errors.append("Unable to detect valid diagram type")
            return self._build_result(False)
        
        # Validate syntax based on diagram type
        if not self._validate_syntax(content, diagram_type):
            return self._build_result(False, diagram_type)
        
        # Check for common issues
        self._check_common_issues(content)
        
        return self._build_result(True, diagram_type)
    
    def _clean_content(self, content: str) -> str:
        """Remove unnecessary whitespace and normalize line endings."""
        return re.sub(r'\r\n|\r', '\n', content.strip())
    
    def _check_security(self, content: str) -> bool:
        """Check for potentially dangerous patterns."""
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                self.errors.append(f"Potentially dangerous content detected: {pattern}")
                return False
        return True
    
    def _detect_diagram_type(self, content: str) -> str:
        """Detect the type of Mermaid diagram."""
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        if not lines:
            return None
            
        first_line = lines[0].lower()
        
        for diagram_type, keywords in self.DIAGRAM_TYPES.items():
            for keyword in keywords:
                if first_line.startswith(keyword.lower()):
                    return diagram_type
        
        return None
    
    def _validate_syntax(self, content: str, diagram_type: str) -> bool:
        """Validate syntax based on diagram type."""
        if diagram_type == 'flowchart':
            return self._validate_flowchart(content)
        elif diagram_type == 'sequence':
            return self._validate_sequence_diagram(content)
        elif diagram_type == 'class':
            return self._validate_class_diagram(content)
        elif diagram_type == 'state':
            return self._validate_state_diagram(content)
        elif diagram_type == 'er':
            return self._validate_er_diagram(content)
        elif diagram_type == 'pie':
            return self._validate_pie_chart(content)
        else:
            # For other diagram types, do basic validation
            return self._validate_basic_syntax(content)
    
    def _validate_flowchart(self, content: str) -> bool:
        """Validate flowchart syntax."""
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        # Check if it starts with flowchart declaration
        if not any(lines[0].lower().startswith(keyword) for keyword in ['flowchart', 'graph']):
            self.errors.append("Flowchart must start with 'flowchart' or 'graph'")
            return False
        
        # Check for basic node and edge patterns
        node_pattern = r'^[A-Za-z0-9_-]+(\[[^\]]*\]|\([^)]*\)|\{[^}]*\}|>[^<]*<)?$'
        edge_pattern = r'^[A-Za-z0-9_-]+\s*(-->|---|\.\.\.|===>)\s*[A-Za-z0-9_-]+(\[[^\]]*\])?$'
        
        for i, line in enumerate(lines[1:], 2):  # Skip first line
            if not line:
                continue
            # Skip comments
            if line.startswith('%%'):
                continue
            
            # Check if line matches node or edge pattern
            if not (re.match(node_pattern, line) or re.match(edge_pattern, line)):
                # Check for multi-line statements
                if '-->' in line or '---' in line or '...' in line or '===>' in line:
                    continue  # Basic edge, probably valid
                else:
                    self.warnings.append(f"Line {i} may have invalid syntax: {line}")
        
        return True
    
    def _validate_sequence_diagram(self, content: str) -> bool:
        """Validate sequence diagram syntax."""
        if not content.lower().startswith('sequencediagram'):
            self.errors.append("Sequence diagram must start with 'sequenceDiagram'")
            return False
        
        # Check for basic participant and message patterns
        participant_pattern = r'participant\s+\w+'
        message_pattern = r'\w+\s*(->|-->|\->>|\-\->>)\s*\w+\s*:'
        
        lines = [line.strip() for line in content.split('\n') if line.strip()][1:]
        has_valid_content = False
        
        for line in lines:
            if line.startswith('%%'):  # Comment
                continue
            if re.match(participant_pattern, line) or re.match(message_pattern, line):
                has_valid_content = True
        
        if not has_valid_content:
            self.warnings.append("No valid participants or messages found in sequence diagram")
        
        return True
    
    def _validate_class_diagram(self, content: str) -> bool:
        """Validate class diagram syntax."""
        if not content.lower().startswith('classdiagram'):
            self.errors.append("Class diagram must start with 'classDiagram'")
            return False
        return True
    
    def _validate_state_diagram(self, content: str) -> bool:
        """Validate state diagram syntax."""
        if not any(content.lower().startswith(keyword) for keyword in ['statediagram', 'statediagram-v2']):
            self.errors.append("State diagram must start with 'stateDiagram' or 'stateDiagram-v2'")
            return False
        return True
    
    def _validate_er_diagram(self, content: str) -> bool:
        """Validate ER diagram syntax."""
        if not content.lower().startswith('erdiagram'):
            self.errors.append("ER diagram must start with 'erDiagram'")
            return False
        return True
    
    def _validate_pie_chart(self, content: str) -> bool:
        """Validate pie chart syntax."""
        if not content.lower().startswith('pie'):
            self.errors.append("Pie chart must start with 'pie'")
            return False
        
        # Check for title and data
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        has_data = False
        
        for line in lines[1:]:
            if ':' in line and not line.startswith('%%'):
                has_data = True
                break
        
        if not has_data:
            self.warnings.append("Pie chart should have data entries in format 'label : value'")
        
        return True
    
    def _validate_basic_syntax(self, content: str) -> bool:
        """Basic validation for diagram types not specifically handled."""
        # Check for balanced brackets and parentheses
        brackets = {'[': ']', '(': ')', '{': '}'}
        stack = []
        
        for char in content:
            if char in brackets:
                stack.append(brackets[char])
            elif char in brackets.values():
                if not stack or stack.pop() != char:
                    self.warnings.append("Potentially unbalanced brackets or parentheses")
                    break
        
        if stack:
            self.warnings.append("Potentially unbalanced brackets or parentheses")
        
        return True
    
    def _check_common_issues(self, content: str):
        """Check for common issues and add warnings."""
        lines = content.split('\n')
        
        # Check for very long lines
        for i, line in enumerate(lines, 1):
            if len(line) > 200:
                self.warnings.append(f"Line {i} is very long ({len(line)} characters)")
        
        # Check for too many nodes (performance)
        node_count = len(re.findall(r'[A-Za-z0-9_-]+\[', content))
        if node_count > 100:
            self.warnings.append(f"Diagram has many nodes ({node_count}), may impact performance")
    
    def _build_result(self, valid: bool, diagram_type: str = None) -> Dict[str, Union[bool, List[str], str]]:
        """Build the validation result dictionary."""
        result = {
            'valid': valid,
            'errors': self.errors.copy(),
            'warnings': self.warnings.copy()
        }
        
        if diagram_type:
            result['diagram_type'] = diagram_type
            
        return result

# Convenience function
def validate_mermaid(content: str) -> Dict[str, Union[bool, List[str]]]:
    """
    Convenience function to validate Mermaid content.
    
    Args:
        content: Mermaid diagram content
        
    Returns:
        Validation result dictionary
    """
    validator = MermaidValidator()
    return validator.validate(content)