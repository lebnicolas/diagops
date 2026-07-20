"""Schemas Pydantic du contrat DiagOps.

Ces modeles sont la traduction executable de data_pack/SCHEMA.md.
Toute sortie qui ne les respecte pas est rejetee a l'execution — y compris
celle produite par le modele IA.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Severity(str, Enum):
    """Niveaux de severite autorises par le contrat DiagOps.

    Herite de str pour etre serialisable directement en JSON :
    Severity.HIGH devient "high", pas "Severity.HIGH".
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DiagnoseRequest(BaseModel):
    """Entree de POST /diagnose : le rapport redige par le technicien."""

    technician_note: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Texte libre du rapport technicien.",
    )
    equipment_id: str | None = Field(
        default=None,
        description="Equipement concerne, si connu de l'appelant.",
    )
    report_id: str | None = Field(
        default=None,
        description="Identifiant du rapport source, si connu.",
    )

    @field_validator("technician_note")
    @classmethod
    def note_non_vide(cls, v: str) -> str:
        """Refuse une note faite uniquement d'espaces et normalise les bords.

        min_length ne suffit pas : "          " fait 10 caracteres et
        passerait la contrainte de longueur.
        """
        nettoye = v.strip()
        if not nettoye:
            raise ValueError("technician_note ne peut pas etre vide")
        return nettoye

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "technician_note": (
                        "Pompe P-204 en zone A. Vibration plus forte que "
                        "d'habitude depuis la prise de poste. Bruit metallique "
                        "au demarrage. Temperature carter mesuree a 71 C."
                    ),
                    "equipment_id": "EQ-PUMP-001",
                    "report_id": "RPT-2026S1-0001",
                }
            ]
        }
    )


class DiagnosisResponse(BaseModel):
    """Sortie de POST /diagnose — contrat DiagOps commun a tous les modules.

    Ce schema est impose par data_pack/SCHEMA.md : ne pas en modifier les
    champs, d'autres modules de la formation s'appuient dessus.
    """

    equipment_id: str = Field(..., description="Equipement concerne.")
    symptom: str = Field(..., description="Symptome extrait du rapport.")
    severity: Severity = Field(..., description="Gravite estimee.")
    failure_hypothesis: str = Field(..., description="Hypothese de panne.")
    recommended_action: str = Field(..., description="Action recommandee.")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confiance du modele, entre 0 et 1.",
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="Elements du rapport ayant motive le diagnostic.",
    )
    requires_human_review: bool = Field(
        ...,
        description="True si un technicien doit valider avant intervention.",
    )

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "examples": [
                {
                    "equipment_id": "EQ-0001",
                    "symptom": "vibration anormale au demarrage",
                    "severity": "high",
                    "failure_hypothesis": "roulement use ou desalignement",
                    "recommended_action": "planifier une inspection prioritaire du palier",
                    "confidence": 0.72,
                    "evidence": ["rapport RPT-0001"],
                    "requires_human_review": True,
                }
            ]
        },
    )
