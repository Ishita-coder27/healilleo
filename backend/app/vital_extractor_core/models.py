from dataclasses import dataclass

@dataclass
class VitalResult:
    name: str
    value: str
    unit: str
    category: str
    reference_range: str = ""
    status: str = "Unknown"
    confidence: float = 0.0
    method: str = "regex"
    note: str = ""