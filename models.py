from pydantic import BaseModel

class ResumeAnalysis(BaseModel):
    experience_level: str 
    skills: list[str] 
    languages: list[str] 

class JobListing(BaseModel):
    job_title: str
    company: str
    location: str
    platform: str
    required_experience_level: str
    key_requirements: list[str]
    contact_email: str

class JobSearchResults(BaseModel):
    jobs: list[JobListing]
