from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class PersonalInfo(BaseModel):
    name: Optional[str] = Field(None, description="The full name of the candidate")
    email: Optional[str] = Field(None, description="The email address of the candidate")
    phone: Optional[str] = Field(None, description="The phone number of the candidate")
    location: Optional[str] = Field(None, description="The city, state, or country of residence of the candidate")
    linkedin: Optional[str] = Field(None, description="The LinkedIn profile URL of the candidate")

class EducationEntry(BaseModel):
    school: Optional[str] = Field(None, description="Name of the university, college, or school")
    degree: Optional[str] = Field(None, description="The degree name (e.g. Bachelor of Science, Master of Arts)")
    field_of_study: Optional[str] = Field(None, description="Field of study or major")
    start_date: Optional[str] = Field(None, description="Start date of education")
    end_date: Optional[str] = Field(None, description="End date or graduation date, or 'Present'")

class ExperienceEntry(BaseModel):
    company: Optional[str] = Field(None, description="Name of the company or organization")
    role: Optional[str] = Field(None, description="The job title or role")
    start_date: Optional[str] = Field(None, description="Start date of employment")
    end_date: Optional[str] = Field(None, description="End date of employment, or 'Present'")
    description: Optional[str] = Field(None, description="Brief description of responsibilities and achievements")
    technologies: List[str] = Field(default_factory=list, description="Technologies, programming languages, or tools used in this role")

class ProjectEntry(BaseModel):
    title: Optional[str] = Field(None, description="Title of the project")
    description: Optional[str] = Field(None, description="Brief description of the project details")
    technologies: List[str] = Field(default_factory=list, description="List of technologies or tools used in this project")
    link: Optional[str] = Field(None, description="Project repository or live site URL")

class ExplicitData(BaseModel):
    personal_info: Optional[PersonalInfo] = Field(default_factory=PersonalInfo, description="Personal contact information")
    skills: List[str] = Field(default_factory=list, description="List of technical skills, tools, and methodologies")
    education: List[EducationEntry] = Field(default_factory=list, description="Academic background and educational history")
    experience: List[ExperienceEntry] = Field(default_factory=list, description="Professional work experience")
    projects: List[ProjectEntry] = Field(default_factory=list, description="Key projects completed")
    certifications: List[str] = Field(default_factory=list, description="Professional certifications, courses, or training completed")

class DerivedData(BaseModel):
    total_years_experience: float = Field(0.0, description="Total years of work experience calculated from employment history")
    employment_gaps: List[str] = Field(default_factory=list, description="List of calculated gaps between employment dates")
    number_of_companies: int = Field(0, description="Total number of distinct companies worked for")
    skill_count: int = Field(0, description="Total number of listed skills")
    duration_calculations: List[Dict[str, Any]] = Field(default_factory=list, description="Parsed durations in months per role/company")

class InferredData(BaseModel):
    seniority_level: Optional[str] = Field(None, description="Inferred seniority level (e.g. Junior, Mid, Senior, Lead, Manager)")
    candidate_strengths: List[str] = Field(default_factory=list, description="AI-deduced strengths of the candidate based on profile")
    suitable_job_roles: List[str] = Field(default_factory=list, description="AI-inferred suitable job roles for this profile")
    possible_areas_of_expertise: List[str] = Field(default_factory=list, description="AI-inferred specialized areas of focus or expertise")
    ai_label: str = Field("AI-Generated Inference", description="A disclaimer indicating that this section is AI-inferred")

class CVFixedSchema(BaseModel):
    explicit_data: Optional[ExplicitData] = Field(default_factory=ExplicitData, description="Directly stated details from CV")
    derived_data: Optional[DerivedData] = Field(default_factory=DerivedData, description="Python-calculated metrics")
    inferred_data: Optional[InferredData] = Field(default_factory=InferredData, description="AI model inferences")

class DynamicExtractionRequest(BaseModel):
    fields: Dict[str, str] = Field(
        ..., 
        description="A dictionary mapping the field keys to descriptions of what to extract. E.g. {'github': 'GitHub URL', 'years_of_experience': 'Total years of experience'}"
    )

class DynamicExtractionResponse(BaseModel):
    extracted_data: Dict[str, Any] = Field(
        ...,
        description="The extracted custom data, where keys match the requested fields."
    )
