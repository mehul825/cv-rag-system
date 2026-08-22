import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.core.config import settings
from app.services.openai_service import get_hf_client, get_openai_client
from app.schemas.cv_schema import CVFixedSchema, ExplicitData, DerivedData, InferredData, PersonalInfo, EducationEntry, ExperienceEntry, ProjectEntry

FIXED_SYSTEM_PROMPT = """You are an advanced AI resume parser. Your task is to extract information from the CV text and structure it as a valid JSON object.
Follow these rules strictly:
1. Output ONLY a valid JSON object. Do NOT include any markdown formatting (like ```json), introduction, or explanation.
2. If a field is not present in the CV, return null (for strings/objects) or an empty array [] (for lists). Do NOT invent or hallucinate any details.
3. Keep formatting clean and consistent.

You must structure the JSON matching the schema below. Note that the output contains two main sections:
- "explicit_data": Information directly found in the resume.
- "inferred_data": AI/model-based conclusions derived from the resume. (Must contain "seniority_level", "candidate_strengths", "suitable_job_roles", and "possible_areas_of_expertise").

Required JSON Schema structure:
{
  "explicit_data": {
    "personal_info": {
      "name": "Full name or null",
      "email": "Email address or null",
      "phone": "Phone number or null",
      "location": "City, state/country or null",
      "linkedin": "LinkedIn profile URL or null"
    },
    "skills": ["Skill 1", "Skill 2", ...],
    "education": [
      {
        "school": "University/School name or null",
        "degree": "Degree name or null",
        "field_of_study": "Major or null",
        "start_date": "Start date or null",
        "end_date": "End date or graduation or null"
      }
    ],
    "experience": [
      {
        "company": "Company name or null",
        "role": "Role title or null",
        "start_date": "Start date or null",
        "end_date": "End date or null",
        "description": "Responsibilities/achievements description or null",
        "technologies": ["Tech 1", "Tech 2", ...]
      }
    ],
    "projects": [
      {
        "title": "Project title or null",
        "description": "Project description or null",
        "technologies": ["Tech 1", "Tech 2", ...],
        "link": "Project link or null"
      }
    ],
    "certifications": ["Certification 1", "Certification 2", ...]
  },
  "inferred_data": {
    "seniority_level": "Seniority rating (e.g. Junior, Mid, Senior, Lead, Manager) or null",
    "candidate_strengths": ["AI-deduced strength 1", "AI-deduced strength 2", ...],
    "suitable_job_roles": ["AI-inferred suitable job role 1", "AI-inferred suitable job role 2", ...],
    "possible_areas_of_expertise": ["AI-inferred specialized area 1", "AI-inferred specialized area 2", ...],
    "ai_label": "AI-Generated Inference"
  }
}
"""

DYNAMIC_SYSTEM_PROMPT_TEMPLATE = """You are an advanced AI resume parser. Your task is to extract specific information from the CV text and structure it as a valid JSON object.
Follow these rules strictly:
1. Output ONLY a valid JSON object. Do NOT include any markdown formatting (like ```json), introduction, or explanation.
2. If a field is not present in the CV, return null (for strings/objects) or an empty array [] (for lists). Do NOT invent or hallucinate any details.
3. The JSON keys MUST exactly match the keys requested below.

Requested fields to extract:
{fields_description}
"""

def clean_json_string(text: str) -> str:
    """
    Cleans the raw LLM output to isolate the JSON string.
    Removes markdown code blocks (e.g. ```json ... ```) and leading/trailing text.
    """
    text = text.strip()
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    if start_idx != -1 and end_idx != -1:
        return text[start_idx:end_idx + 1].strip()
        
    return text

def get_active_client_and_model():
    """
    Returns the appropriate client and model based on settings.
    """
    if settings.HF_TOKEN:
        return get_hf_client(), settings.HF_MODEL
    else:
        return get_openai_client(), settings.OLLAMA_CHAT_MODEL

def parse_date_string(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    date_str = date_str.strip().lower()
    if 'present' in date_str or 'current' in date_str:
        return datetime.now()
    
    # MM/YYYY
    m = re.match(r'(\d{1,2})/(\d{4})', date_str)
    if m:
        return datetime(int(m.group(2)), int(m.group(1)), 1)
        
    # YYYY
    m = re.match(r'^(\d{4})$', date_str)
    if m:
        return datetime(int(m.group(1)), 1, 1)
        
    # Month Name YYYY (e.g. "January 2020", "Jan 2020")
    months = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
        'january': 1, 'february': 2, 'march': 3, 'april': 4, 'june': 6,
        'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    m = re.search(r'([a-zA-Z]+)\s+(\d{4})', date_str)
    if m:
        month_name = m.group(1).lower()[:3]
        month_num = months.get(month_name, 1)
        return datetime(int(m.group(2)), month_num, 1)
        
    return None

def calculate_derived_data(explicit_data: ExplicitData) -> DerivedData:
    experience = explicit_data.experience or []
    companies = set()
    duration_calculations = []
    total_months = 0.0
    parsed_jobs = []
    
    for exp in experience:
        if exp.company:
            companies.add(exp.company.strip().lower())
            
        start = parse_date_string(exp.start_date)
        end = parse_date_string(exp.end_date)
        
        if start and end:
            diff_months = (end.year - start.year) * 12 + (end.month - start.month)
            if diff_months < 0:
                diff_months = 0
            total_months += diff_months
            duration_calculations.append({
                "company": exp.company or "Unknown",
                "duration_months": diff_months
            })
            parsed_jobs.append((start, end, exp.company or "Unknown"))
        else:
            duration_calculations.append({
                "company": exp.company or "Unknown",
                "duration_months": 0
            })
            
    total_years = round(total_months / 12.0, 1)
    
    # Calculate gaps
    gaps = []
    if len(parsed_jobs) > 1:
        parsed_jobs.sort(key=lambda x: x[0], reverse=True)
        for i in range(len(parsed_jobs) - 1):
            current_job = parsed_jobs[i]
            next_job = parsed_jobs[i+1]
            if current_job[0] > next_job[1]:
                gap_months = (current_job[0].year - next_job[1].year) * 12 + (current_job[0].month - next_job[1].month)
                if gap_months > 1:
                    gaps.append(f"Gap of {gap_months} months between {next_job[2]} and {current_job[2]}")
                    
    return DerivedData(
        total_years_experience=total_years,
        employment_gaps=gaps,
        number_of_companies=len(companies),
        skill_count=len(explicit_data.skills or []),
        duration_calculations=duration_calculations
    )

def extract_cv_fixed(cv_text: str) -> Dict[str, Any]:
    """
    Extracts structured JSON from CV text according to the fixed schema.
    Calculates derived metrics in Python.
    Includes a self-correction retry loop up to 2 retries.
    """
    client, model_name = get_active_client_and_model()
    user_prompt = f"Please extract details from the following CV text:\n\n{cv_text}"
    
    max_retries = 2
    retry_count = 0
    current_messages = [
        {"role": "system", "content": FIXED_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
    
    last_raw_output = ""
    last_error_msg = ""
    
    while retry_count <= max_retries:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=current_messages,
                temperature=0.1
            )
            raw_output = response.choices[0].message.content
            last_raw_output = raw_output
            
            cleaned_output = clean_json_string(raw_output)
            
            try:
                parsed_json = json.loads(cleaned_output)
            except json.JSONDecodeError as je:
                last_error_msg = f"JSON decode error: {str(je)}"
                raise ValueError(last_error_msg)
            
            explicit_dict = parsed_json.get("explicit_data", {})
            inferred_dict = parsed_json.get("inferred_data", {})
            
            validation_errors = []
            try:
                explicit_obj = ExplicitData(**explicit_dict)
            except Exception as e:
                validation_errors.append(f"explicit_data validation error: {str(e)}")
                
            try:
                inferred_obj = InferredData(**inferred_dict)
            except Exception as e:
                validation_errors.append(f"inferred_data validation error: {str(e)}")
                
            if validation_errors:
                last_error_msg = "; ".join(validation_errors)
                raise ValueError(last_error_msg)
                
            # If successful, calculate derived data and return
            derived_obj = calculate_derived_data(explicit_obj)
            
            final_schema = CVFixedSchema(
                explicit_data=explicit_obj,
                derived_data=derived_obj,
                inferred_data=inferred_obj
            )
            
            return final_schema.model_dump()
            
        except Exception as e:
            last_error_msg = str(e)
            print(f"Validation failure on attempt {retry_count}: {last_error_msg}")
            
            if retry_count == max_retries:
                print(f"Final failure after {max_retries} retries. Error: {last_error_msg}")
                raise RuntimeError(f"JSON validation and correction failed: {last_error_msg}")
                
            retry_count += 1
            print(f"Initiating retry attempt {retry_count}...")
            
            correction_instruction = (
                f"Your previous output was invalid JSON or failed schema validation.\n"
                f"Error details:\n{last_error_msg}\n\n"
                f"Please review the previous output and correct it. Output ONLY a valid JSON object matching the required schema. Do not include markdown codeblocks or explanations."
            )
            
            current_messages.append({"role": "assistant", "content": last_raw_output})
            current_messages.append({"role": "user", "content": correction_instruction})
            
    raise RuntimeError("JSON extraction retries exhausted with unknown error.")

def extract_cv_dynamic(cv_text: str, fields: Dict[str, str]) -> Dict[str, Any]:
    """
    Extracts custom structured data from CV text according to user-defined fields.
    Includes a self-correction retry loop up to 2 retries.
    """
    client, model_name = get_active_client_and_model()
    
    fields_desc = json.dumps(fields, indent=2)
    system_prompt = DYNAMIC_SYSTEM_PROMPT_TEMPLATE.format(fields_description=fields_desc)
    
    user_prompt = f"Please extract details from the following CV text:\n\n{cv_text}"
    
    max_retries = 2
    retry_count = 0
    current_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    last_raw_output = ""
    last_error_msg = ""
    
    while retry_count <= max_retries:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=current_messages,
                temperature=0.1
            )
            raw_output = response.choices[0].message.content
            last_raw_output = raw_output
            
            cleaned_output = clean_json_string(raw_output)
            
            try:
                parsed_json = json.loads(cleaned_output)
            except json.JSONDecodeError as je:
                last_error_msg = f"JSON decode error: {str(je)}"
                raise ValueError(last_error_msg)
            
            # Ensure all requested keys exist in the output dictionary
            for key in fields.keys():
                if key not in parsed_json:
                    parsed_json[key] = None
                    
            return parsed_json
            
        except Exception as e:
            last_error_msg = str(e)
            print(f"Dynamic validation failure on attempt {retry_count}: {last_error_msg}")
            
            if retry_count == max_retries:
                print(f"Dynamic final failure after {max_retries} retries. Error: {last_error_msg}")
                raise RuntimeError(f"Dynamic JSON validation and correction failed: {last_error_msg}")
                
            retry_count += 1
            print(f"Initiating dynamic retry attempt {retry_count}...")
            
            correction_instruction = (
                f"Your previous output was invalid JSON or missing key fields.\n"
                f"Error details:\n{last_error_msg}\n\n"
                f"Please review the previous output and correct it. Output ONLY a valid JSON object matching the requested keys. Do not include markdown codeblocks or explanations."
            )
            
            current_messages.append({"role": "assistant", "content": last_raw_output})
            current_messages.append({"role": "user", "content": correction_instruction})
            
    raise RuntimeError("Dynamic JSON extraction retries exhausted with unknown error.")
